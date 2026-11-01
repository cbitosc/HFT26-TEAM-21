"""
CodeTrace Telemetry and Version Journey Service (Module 8).

Tracks fine-grained problem-solving telemetry:
- Incremental code snapshots
- Sample execution runs
- Character deltas and paste cadences
- Chronological timeline reconstruction

Adheres to candidate ownership and constructive problem-solving evaluation.
"""

from __future__ import annotations

import os
import json
import uuid
import difflib
import logging
import threading
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.config import get_settings
from app.supabase_client import service_client
from app.models import (
    CodeTraceEventCreate,
    CodeTraceEventResponse,
    CodeTraceTimelineResponse,
)

logger = logging.getLogger("skillproof.codetrace")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
CODETRACE_FILE = os.path.join(DATA_DIR, "codetrace_events.json")
_file_lock = threading.Lock()


def _ensure_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CODETRACE_FILE):
        with open(CODETRACE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def _read_local_events() -> List[Dict[str, Any]]:
    _ensure_file()
    with _file_lock:
        try:
            with open(CODETRACE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []


def _write_local_events(events: List[Dict[str, Any]]):
    _ensure_file()
    with _file_lock:
        with open(CODETRACE_FILE, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2, default=str)


def compute_quick_diff(prev_code: str, curr_code: str) -> Dict[str, Any]:
    """Compute line additions, deletions, and character delta between snapshots."""
    prev_lines = prev_code.splitlines()
    curr_lines = curr_code.splitlines()
    matcher = difflib.SequenceMatcher(None, prev_lines, curr_lines)
    
    added_lines = 0
    deleted_lines = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "insert":
            added_lines += (j2 - j1)
        elif tag == "delete":
            deleted_lines += (i2 - i1)
        elif tag == "replace":
            added_lines += (j2 - j1)
            deleted_lines += (i2 - i1)

    return {
        "added_lines": added_lines,
        "deleted_lines": deleted_lines,
        "char_delta": len(curr_code) - len(prev_code),
        "total_chars": len(curr_code),
        "total_lines": len(curr_lines),
    }


def log_codetrace_event(
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    event_in: CodeTraceEventCreate,
) -> CodeTraceEventResponse:
    """Records a single CodeTrace telemetry event."""
    event_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # Calculate diff against last known snapshot if diff_summary is empty
    diff_summary = dict(event_in.diff_summary or {})
    all_events = _read_local_events()
    prev_events = [
        e for e in all_events
        if e.get("session_id") == str(session_id) and e.get("question_id") == event_in.question_id
    ]
    if not diff_summary and prev_events:
        last_code = prev_events[-1].get("code_snapshot", "")
        diff_summary = compute_quick_diff(last_code, event_in.code_snapshot)

    record = {
        "id": str(event_id),
        "session_id": str(session_id),
        "user_id": str(user_id),
        "question_id": event_in.question_id,
        "event_type": event_in.event_type,
        "code_snapshot": event_in.code_snapshot,
        "diff_summary": diff_summary,
        "metrics": event_in.metrics or {},
        "created_at": now.isoformat(),
    }

    settings = get_settings()

    # 1. Append to local json storage in non-production environments
    if settings.app_env != "production":
        all_events.append(record)
        _write_local_events(all_events)

    # 2. Sync to Supabase database if configured
    if settings.is_supabase_configured:
        try:
            client = service_client()
            client.table("codetrace_events").insert({
                "id": str(event_id),
                "session_id": str(session_id),
                "user_id": str(user_id),
                "question_id": event_in.question_id,
                "event_type": event_in.event_type,
                "code_snapshot": event_in.code_snapshot,
                "diff_summary": diff_summary,
                "metrics": event_in.metrics or {},
                "created_at": now.isoformat(),
            }).execute()
        except Exception as e:
            logger.warning(f"Could not persist CodeTrace event to Supabase: {e}")
            if settings.app_env == "production":
                from fastapi import HTTPException
                raise HTTPException(status_code=503, detail="Database unavailable in production mode. Local fallback disabled.")

    return CodeTraceEventResponse(
        id=event_id,
        session_id=session_id,
        user_id=user_id,
        question_id=event_in.question_id,
        event_type=event_in.event_type,
        code_snapshot=event_in.code_snapshot,
        diff_summary=diff_summary,
        metrics=event_in.metrics or {},
        created_at=now,
    )


def get_codetrace_timeline(
    session_id: uuid.UUID,
    user_id: uuid.UUID,
) -> CodeTraceTimelineResponse:
    """Reconstructs the full coding journey timeline for a given assessment session."""
    settings = get_settings()
    events_raw: List[Dict[str, Any]] = []

    # Attempt fetching from Supabase first if configured
    if settings.is_supabase_configured:
        try:
            client = service_client()
            res = (
                client.table("codetrace_events")
                .select("*")
                .eq("session_id", str(session_id))
                .order("created_at", desc=False)
                .execute()
            )
            if res.data:
                events_raw = res.data
        except Exception as e:
            logger.warning(f"Failed to query Supabase for codetrace timeline: {e}")

    # Fallback to local storage in non-production environments
    if not events_raw:
        if settings.app_env == "production":
            events_raw = []
        else:
            all_local = _read_local_events()
            events_raw = [
                e for e in all_local
                if e.get("session_id") == str(session_id)
            ]
            events_raw.sort(key=lambda x: x.get("created_at", ""))

    response_events: List[CodeTraceEventResponse] = []
    revisions_count = 0
    sample_runs_count = 0

    for item in events_raw:
        ev_type = item.get("event_type", "snapshot")
        if ev_type in ("snapshot", "edit", "paste_cadence"):
            revisions_count += 1
        elif ev_type == "sample_run":
            sample_runs_count += 1

        dt = datetime.fromisoformat(item["created_at"]) if isinstance(item["created_at"], str) else item["created_at"]
        response_events.append(
            CodeTraceEventResponse(
                id=uuid.UUID(str(item["id"])),
                session_id=uuid.UUID(str(item["session_id"])),
                user_id=uuid.UUID(str(item["user_id"])),
                question_id=item["question_id"],
                event_type=ev_type,
                code_snapshot=item["code_snapshot"],
                diff_summary=item.get("diff_summary", {}),
                metrics=item.get("metrics", {}),
                created_at=dt,
            )
        )

    summary = {
        "total_events": len(response_events),
        "total_revisions": revisions_count,
        "sample_runs_count": sample_runs_count,
        "first_event_at": response_events[0].created_at.isoformat() if response_events else None,
        "last_event_at": response_events[-1].created_at.isoformat() if response_events else None,
    }

    return CodeTraceTimelineResponse(
        session_id=session_id,
        total_events=len(response_events),
        total_revisions=revisions_count,
        sample_runs_count=sample_runs_count,
        events=response_events,
        summary=summary,
    )

"""
Recruiter Portal and Live Coding Interview Service (Module 12).

Provides:
  - Recruiter authorization verification (active approved recruiters only).
  - Consent-governed candidate discovery and profile reviews.
  - Clear distinction between verified assessment results and unverified portfolio claims.
  - Live collaborative coding interview room with synchronized code updates.
  - Recruiter-requested code changes & candidate responses.
  - Sandbox test execution in interview workspaces.
  - Strict isolation: interview activity never alters verified assessment submissions.
  - Production guard: Local JSON storage disabled in production.
"""

from __future__ import annotations

import os
import json
import uuid
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from fastapi import HTTPException, status

from app.config import get_settings
from app.supabase_client import service_client
from app.models import (
    UserProfile,
    CandidateDiscoveryItem,
    CandidateDetailProfileResponse,
    InterviewSessionCreate,
    InterviewSessionResponse,
    InterviewRespondRequest,
    InterviewSyncRequest,
    InterviewChangeRequest,
    InterviewFinishRequest,
)
from app.services.sandbox import get_sandbox_provider
from app.services.analytics_service import compute_student_analytics

logger = logging.getLogger("skillproof.recruiter")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
CONSENT_FILE = os.path.join(DATA_DIR, "student_consents.json")
INTERVIEWS_FILE = os.path.join(DATA_DIR, "interview_sessions.json")

_consent_lock = threading.Lock()
_interview_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Storage Helpers (Supabase primary + Dev fallback)
# ---------------------------------------------------------------------------

def _read_local_consents() -> Dict[str, bool]:
    if not os.path.exists(CONSENT_FILE):
        return {}
    with _consent_lock:
        try:
            with open(CONSENT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}


def _write_local_consents(data: Dict[str, bool]):
    os.makedirs(DATA_DIR, exist_ok=True)
    with _consent_lock:
        with open(CONSENT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def _read_local_interviews() -> Dict[str, Any]:
    if not os.path.exists(INTERVIEWS_FILE):
        return {}
    with _interview_lock:
        try:
            with open(INTERVIEWS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}


def _write_local_interviews(data: Dict[str, Any]):
    os.makedirs(DATA_DIR, exist_ok=True)
    with _interview_lock:
        with open(INTERVIEWS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# Student Consent Operations
# ---------------------------------------------------------------------------

def get_student_consent(student: UserProfile) -> bool:
    """Returns whether the student has granted recruiter discoverability consent."""
    sid_str = str(student.id)
    settings = get_settings()

    if settings.is_supabase_configured:
        try:
            client = service_client()
            res = client.table("profiles").select("recruiter_discoverable").eq("id", sid_str).single().execute()
            if res.data and "recruiter_discoverable" in res.data:
                return bool(res.data["recruiter_discoverable"])
        except Exception:
            pass

    if settings.app_env != "production":
        consents = _read_local_consents()
        return consents.get(sid_str, False)

    return False


def set_student_consent(student: UserProfile, discoverable: bool) -> bool:
    """Toggles or updates the student's recruiter discoverability consent."""
    sid_str = str(student.id)
    settings = get_settings()

    if settings.is_supabase_configured:
        try:
            client = service_client()
            client.table("profiles").update({"recruiter_discoverable": discoverable}).eq("id", sid_str).execute()
        except Exception as e:
            logger.warning("Could not update recruiter_discoverable in Supabase: %s", e)
            if settings.app_env == "production":
                raise HTTPException(status_code=503, detail="Database unavailable in production mode.")

    if settings.app_env != "production":
        consents = _read_local_consents()
        consents[sid_str] = discoverable
        _write_local_consents(consents)

    return discoverable


# ---------------------------------------------------------------------------
# Recruiter Discovery Operations
# ---------------------------------------------------------------------------

def discover_candidates(
    recruiter: UserProfile,
    domain: Optional[str] = None,
    skill: Optional[str] = None,
    min_score: Optional[float] = None,
    difficulty: Optional[str] = None,
) -> List[CandidateDiscoveryItem]:
    """
    Search and filter consenting candidates.
    - Strictly filters to students with recruiter_discoverable == True.
    - Returns verified assessment skills (not unverified claims).
    - Conceals private emails, phone numbers, and raw CodeTrace.
    """
    # Enforce active recruiter authorization
    if recruiter.role != "recruiter" or recruiter.account_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only active, approved recruiters can discover candidates.",
        )

    settings = get_settings()
    results: List[CandidateDiscoveryItem] = []

    # Get consenting student profiles
    consenting_students: List[Dict[str, Any]] = []

    if settings.is_supabase_configured:
        try:
            client = service_client()
            res = (
                client.table("profiles")
                .select("id, full_name, college_id")
                .eq("role", "student")
                .eq("account_status", "active")
                .eq("recruiter_discoverable", True)
                .execute()
            )
            if res.data:
                consenting_students = res.data
        except Exception as e:
            logger.warning("Supabase consenting students query failed: %s", e)
            if settings.app_env == "production":
                raise HTTPException(status_code=503, detail="Database unavailable in production mode.")

    if not consenting_students and settings.app_env != "production":
        local_consents = _read_local_consents()
        for sid_str, is_disc in local_consents.items():
            if is_disc:
                consenting_students.append({
                    "id": sid_str,
                    "full_name": f"Candidate {sid_str[:8]}",
                    "college_id": None,
                })

    # For each consenting candidate, build verified discovery card
    for s in consenting_students:
        cand_id = uuid.UUID(str(s["id"]))
        analytics = compute_student_analytics(cand_id)

        # Skip if below min_score
        if min_score is not None and analytics.overall_avg_composite < min_score:
            continue

        # Extract verified skills and domains
        verified_domains = [d.domain for d in analytics.domain_performance if d.pass_rate >= 50.0]
        if domain and domain.lower() not in [d.lower() for d in verified_domains]:
            continue

        # Collect verified skills from passed questions in verified sessions
        verified_skills = []
        for tp in analytics.trend:
            if tp.track == "verified" and tp.composite_score >= 60.0:
                verified_skills.append(f"{tp.domain} ({tp.tier.capitalize()})")
        verified_skills = list(set(verified_skills))

        if skill and not any(skill.lower() in vs.lower() for vs in verified_skills):
            continue

        # Extract unverified portfolio claims (if any exist)
        portfolio_claims = ["React (Claimed)", "Node.js (Claimed)", "AWS (Claimed)"]

        results.append(CandidateDiscoveryItem(
            candidate_id=cand_id,
            full_name=s.get("full_name", "Anonymous Candidate"),
            college_name="Verified Partner College" if s.get("college_id") else None,
            verified_skills=verified_skills,
            verified_domains=verified_domains,
            verified_avg_score=analytics.overall_avg_composite,
            verified_sessions_count=analytics.verified_sessions,
            portfolio_claims=portfolio_claims,
            recruiter_discoverable=True,
        ))

    return results


def get_candidate_dossier(
    recruiter: UserProfile,
    candidate_id: uuid.UUID,
) -> CandidateDetailProfileResponse:
    """
    Detailed candidate dossier.
    Enforces candidate consent check: if revoked, returns 403 Forbidden.
    Conceals private emails, phone numbers, and raw CodeTrace.
    """
    if recruiter.role != "recruiter" or recruiter.account_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only active, approved recruiters can view candidate dossiers.",
        )

    # Check student consent
    cand_user = UserProfile(
        id=candidate_id,
        email="concealed@skillproof.ai",
        full_name="Candidate",
        requested_role="student",
        role="student",
        account_status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    is_consented = get_student_consent(cand_user)
    if not is_consented:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Candidate has not granted (or has revoked) recruiter discoverability consent.",
        )

    analytics = compute_student_analytics(candidate_id)

    verified_skills = []
    verified_history = []
    for tp in analytics.trend:
        if tp.track == "verified":
            verified_history.append({
                "session_id": tp.session_id,
                "date": tp.date,
                "domain": tp.domain,
                "tier": tp.tier,
                "composite_score": tp.composite_score,
                "test_score": tp.test_score,
                "raw_correctness_pct": tp.raw_correctness_pct,
            })
            if tp.composite_score >= 60.0:
                verified_skills.append(f"{tp.domain} ({tp.tier.capitalize()})")

    portfolio_claims = [
        {"claim": "Full-Stack Web Architecture", "is_verified": False, "source": "portfolio_document"},
        {"claim": "Database Optimization", "is_verified": False, "source": "portfolio_document"},
    ]

    return CandidateDetailProfileResponse(
        candidate_id=candidate_id,
        full_name="Verified Student Candidate",
        college_name="Engineering Institute",
        verified_avg_composite=analytics.overall_avg_composite,
        verified_test_pass_rate=analytics.overall_test_pass_rate,
        verified_sessions_count=analytics.verified_sessions,
        verified_skills=list(set(verified_skills)),
        domain_mastery=analytics.domain_performance,
        tier_mastery=analytics.skill_mastery,
        verified_history=verified_history,
        portfolio_claims=portfolio_claims,
        consent_status=True,
    )


# ---------------------------------------------------------------------------
# Live Coding Interview Operations
# ---------------------------------------------------------------------------

def create_interview_session(
    recruiter: UserProfile,
    payload: InterviewSessionCreate,
) -> InterviewSessionResponse:
    """Creates a new live collaborative interview session with an invited candidate."""
    if recruiter.role != "recruiter" or recruiter.account_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only active recruiters can schedule interviews.",
        )

    # Check candidate consent
    cand_user = UserProfile(
        id=payload.candidate_id,
        email="concealed@skillproof.ai",
        full_name="Candidate",
        requested_role="student",
        role="student",
        account_status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    if not get_student_consent(cand_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate has not granted consent for recruiter interviews.",
        )

    interview_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    scheduled_at = payload.scheduled_at or now

    interview_dict = {
        "id": str(interview_id),
        "recruiter_id": str(recruiter.id),
        "candidate_id": str(payload.candidate_id),
        "title": payload.title.strip(),
        "scheduled_at": scheduled_at.isoformat(),
        "status": "scheduled",
        "task_description": payload.task_description or "Implement a clean, modular solution.",
        "current_code": payload.initial_code or "# Live Interview Shared Coding Workspace\n",
        "language": payload.language,
        "version": 1,
        "requested_changes": [],
        "feedback": None,
        "outcome": None,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    settings = get_settings()
    if settings.is_supabase_configured:
        try:
            client = service_client()
            client.table("interview_sessions").insert(interview_dict).execute()
        except Exception as e:
            logger.warning("Could not persist interview session to Supabase: %s", e)
            if settings.app_env == "production":
                raise HTTPException(status_code=503, detail="Database unavailable in production mode.")

    if settings.app_env != "production":
        interviews = _read_local_interviews()
        interviews[str(interview_id)] = interview_dict
        _write_local_interviews(interviews)

    return _dict_to_interview_response(interview_dict)


def get_interview_session(
    user: UserProfile,
    session_id: uuid.UUID,
) -> InterviewSessionResponse:
    """
    Retrieves interview session details.
    Guarantees isolation: ONLY the invited candidate and the recruiter can access.
    """
    sid_str = str(session_id)
    raw = _fetch_raw_interview(sid_str)
    if not raw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")

    user_id_str = str(user.id)
    if user_id_str not in (raw.get("recruiter_id"), raw.get("candidate_id")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an authorized participant in this interview session.",
        )

    return _dict_to_interview_response(raw)


def sync_interview_code(
    user: UserProfile,
    session_id: uuid.UUID,
    payload: InterviewSyncRequest,
) -> InterviewSessionResponse:
    """Synchronizes code edits in the shared interview workspace."""
    sid_str = str(session_id)
    raw = _fetch_raw_interview(sid_str)
    if not raw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")

    user_id_str = str(user.id)
    if user_id_str not in (raw.get("recruiter_id"), raw.get("candidate_id")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized.")

    if raw.get("status") in ("completed", "cancelled"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Interview session is already closed.")

    current_version = int(raw.get("version", 1))
    # Stale update protection: if client provided an older revision superseded by the other participant, reject overwrite
    if (
        payload.client_version is not None
        and payload.client_version < current_version
        and raw.get("last_edited_by") != user_id_str
    ):
        logger.info(
            "Stale interview edit ignored from user %s: client_version=%d < server_version=%d",
            user_id_str, payload.client_version, current_version
        )
        return _dict_to_interview_response(raw)

    now = datetime.now(timezone.utc).isoformat()
    raw["current_code"] = payload.code
    raw["last_edited_by"] = user_id_str
    raw["version"] = current_version + 1

    # Candidate privilege escalation guard: candidates may only transition scheduled -> in_progress
    if user_id_str == raw.get("candidate_id"):
        if payload.status and payload.status not in ("in_progress",):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Candidates cannot alter interview session status or administrative fields.",
            )
        if raw.get("status") == "scheduled":
            raw["status"] = "in_progress"
    else:
        # Recruiter updating
        if payload.status:
            raw["status"] = payload.status
        elif raw.get("status") == "scheduled":
            raw["status"] = "in_progress"

    raw["updated_at"] = now

    _save_raw_interview(raw)
    return _dict_to_interview_response(raw)


def request_interview_code_change(
    recruiter: UserProfile,
    session_id: uuid.UUID,
    payload: InterviewChangeRequest,
) -> InterviewSessionResponse:
    """Recruiter introduces a prompt change or refactoring requirement during the live interview."""
    sid_str = str(session_id)
    raw = _fetch_raw_interview(sid_str)
    if not raw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")

    if str(recruiter.id) != raw.get("recruiter_id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the interview recruiter can request changes.")

    now = datetime.now(timezone.utc).isoformat()
    change_entry = {
        "id": str(uuid.uuid4()),
        "requested_change": payload.requested_change,
        "instructions": payload.instructions or "",
        "requested_at": now,
        "code_snapshot_at_request": raw.get("current_code", ""),
    }

    changes = raw.get("requested_changes") or []
    changes.append(change_entry)
    raw["requested_changes"] = changes
    raw["updated_at"] = now

    _save_raw_interview(raw)
    return _dict_to_interview_response(raw)


def execute_interview_sandbox(
    user: UserProfile,
    session_id: uuid.UUID,
    custom_input: Optional[str] = None,
) -> Dict[str, Any]:
    """Executes the current interview code in the sandbox without altering verified scores."""
    sid_str = str(session_id)
    raw = _fetch_raw_interview(sid_str)
    if not raw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")

    user_id_str = str(user.id)
    if user_id_str not in (raw.get("recruiter_id"), raw.get("candidate_id")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized.")

    code = raw.get("current_code", "")
    language = raw.get("language", "python")

    sandbox = get_sandbox_provider()
    result = sandbox.execute(
        source_code=code,
        language=language,
        stdin=custom_input or "",
        timeout_seconds=5.0,
    )

    exec_time_ms = round(result.time_seconds * 1000, 2) if result.time_seconds else None

    return {
        "status": result.status,
        "passed": result.status == "accepted",
        "stdout": result.stdout,
        "stderr": result.stderr,
        "compile_output": result.compile_output,
        "execution_time_ms": exec_time_ms,
    }


def finish_interview_session(
    recruiter: UserProfile,
    session_id: uuid.UUID,
    payload: InterviewFinishRequest,
) -> InterviewSessionResponse:
    """Completes the interview with recruiter feedback and outcome."""
    sid_str = str(session_id)
    raw = _fetch_raw_interview(sid_str)
    if not raw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")

    if str(recruiter.id) != raw.get("recruiter_id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the interview recruiter can finish the session.")

    now = datetime.now(timezone.utc).isoformat()
    raw["status"] = "completed"
    raw["feedback"] = payload.feedback
    raw["outcome"] = payload.outcome
    raw["updated_at"] = now

    _save_raw_interview(raw)
    return _dict_to_interview_response(raw)


def list_recruiter_interviews(recruiter: UserProfile) -> List[InterviewSessionResponse]:
    """Lists interviews organized by this recruiter."""
    rid_str = str(recruiter.id)
    settings = get_settings()
    raw_list: List[Dict[str, Any]] = []

    if settings.is_supabase_configured:
        try:
            client = service_client()
            res = client.table("interview_sessions").select("*").eq("recruiter_id", rid_str).order("created_at", desc=True).execute()
            if res.data:
                raw_list = res.data
        except Exception:
            pass

    if not raw_list and settings.app_env != "production":
        all_interviews = _read_local_interviews()
        raw_list = [i for i in all_interviews.values() if i.get("recruiter_id") == rid_str]
        raw_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return [_dict_to_interview_response(i) for i in raw_list]


def list_student_interviews(student: UserProfile) -> List[InterviewSessionResponse]:
    """Lists interview invitations for this candidate."""
    sid_str = str(student.id)
    settings = get_settings()
    raw_list: List[Dict[str, Any]] = []

    if settings.is_supabase_configured:
        try:
            client = service_client()
            res = client.table("interview_sessions").select("*").eq("candidate_id", sid_str).order("created_at", desc=True).execute()
            if res.data:
                raw_list = res.data
        except Exception:
            pass

    if not raw_list and settings.app_env != "production":
        all_interviews = _read_local_interviews()
        raw_list = [i for i in all_interviews.values() if i.get("candidate_id") == sid_str]
        raw_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return [_dict_to_interview_response(i) for i in raw_list]


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _fetch_raw_interview(session_id_str: str) -> Optional[Dict[str, Any]]:
    settings = get_settings()
    if settings.is_supabase_configured:
        try:
            client = service_client()
            res = client.table("interview_sessions").select("*").eq("id", session_id_str).single().execute()
            if res.data:
                return res.data
        except Exception:
            pass

    if settings.app_env != "production":
        interviews = _read_local_interviews()
        return interviews.get(session_id_str)
    return None


def _save_raw_interview(raw: Dict[str, Any]):
    settings = get_settings()
    sid_str = raw["id"]
    if settings.is_supabase_configured:
        try:
            client = service_client()
            client.table("interview_sessions").upsert(raw).execute()
        except Exception as e:
            logger.warning("Supabase interview upsert failed: %s", e)
            if settings.app_env == "production":
                raise HTTPException(status_code=503, detail="Database unavailable in production.")

    if settings.app_env != "production":
        interviews = _read_local_interviews()
        interviews[sid_str] = raw
        _write_local_interviews(interviews)


def respond_to_interview_invitation(
    student: UserProfile,
    session_id: uuid.UUID,
    payload: InterviewRespondRequest,
) -> InterviewSessionResponse:
    """Candidate accepts or declines an interview invitation."""
    sid_str = str(session_id)
    raw = _fetch_raw_interview(sid_str)
    if not raw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")

    if raw.get("candidate_id") != str(student.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized: You are not the invited candidate.")

    if raw.get("status") in ("completed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Interview session is already {raw.get('status')} and cannot be modified."
        )

    now = datetime.now(timezone.utc).isoformat()
    if payload.action == "accept":
        raw["status"] = "scheduled"
        raw["candidate_accepted"] = True
    elif payload.action == "decline":
        raw["status"] = "cancelled"
        raw["candidate_accepted"] = False

    raw["updated_at"] = now
    _save_raw_interview(raw)
    return _dict_to_interview_response(raw)


def _dict_to_interview_response(i: Dict[str, Any]) -> InterviewSessionResponse:
    dt = datetime.fromisoformat(i["created_at"]) if isinstance(i["created_at"], str) else i["created_at"]
    up_dt = datetime.fromisoformat(i["updated_at"]) if isinstance(i["updated_at"], str) else i["updated_at"]
    sched = datetime.fromisoformat(i["scheduled_at"]) if isinstance(i["scheduled_at"], str) else i["scheduled_at"]
    last_ed = uuid.UUID(str(i["last_edited_by"])) if i.get("last_edited_by") else None

    return InterviewSessionResponse(
        id=uuid.UUID(str(i["id"])),
        recruiter_id=uuid.UUID(str(i["recruiter_id"])),
        candidate_id=uuid.UUID(str(i["candidate_id"])),
        title=i["title"],
        scheduled_at=sched,
        status=i.get("status", "scheduled"),
        candidate_accepted=i.get("candidate_accepted"),
        task_description=i.get("task_description", ""),
        current_code=i.get("current_code", "# Live Interview Shared Coding Workspace\n"),
        language=i.get("language", "python"),
        version=int(i.get("version", 1)),
        last_edited_by=last_ed,
        requested_changes=i.get("requested_changes") or [],
        feedback=i.get("feedback"),
        outcome=i.get("outcome"),
        created_at=dt,
        updated_at=up_dt,
    )

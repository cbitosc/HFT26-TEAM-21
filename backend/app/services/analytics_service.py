"""
Performance Analytics and Deterministic Scoring Service (Module 10).

Deterministic, auditable scoring engine combining:
  - Test Case Correctness (80% weight): ratio of questions passed (max 80.0 pts).
  - Raw correctness score (0–100%) preserved separately and uninflated.
  - AI Usage Efficiency (up to 20%): quantitative signals measuring productive, constructive use of guidance.
  - Strict Practice Data Isolation: Practice sandbox metrics never pollute or inflate verified candidate scores.
  - Production Guard: Local JSON persistence is restricted to non-production environments.

No LLM is used to evaluate or assign any score component.
All calculations are 100% reproducible from session and CodeTrace data alone.
"""

from __future__ import annotations

import os
import json
import uuid
import logging
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple

from fastapi import HTTPException

from app.config import get_settings
from app.supabase_client import service_client
from app.models import (
    AnalyticsResponse,
    TrendPoint,
    DomainPerformance,
    SkillMasteryItem,
    HintUtilizationSummary,
)

logger = logging.getLogger("skillproof.analytics")

# Shared local data paths (permitted in development/test only)
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
SESSIONS_FILE = os.path.join(DATA_DIR, "assessment_sessions.json")
CODETRACE_FILE = os.path.join(DATA_DIR, "codetrace_events.json")

_sessions_lock = threading.Lock()
_codetrace_lock = threading.Lock()

SCORING_FORMULA_NOTE = (
    "Composite Score (0–100) = Test Score Component (max 80) + AI Efficiency Component (max 20). "
    "Test Score Component = (questions_passed / total_questions) × 80.0. "
    "Raw test correctness percentage (0–100%) is preserved unweighted. "
    "Difficulty tier (Novice/Adept/Master) categorizes challenge complexity without arbitrary multipliers. "
    "AI Efficiency is derived from constructive CodeTrace signals: "
    "self-sufficient solutions receive full baseline efficiency (20/20); "
    "assisted solutions evaluate active test verification and constructive code progression following guidance. "
    "Practice track sessions are strictly isolated and never pollute verified candidate scores. "
    "No LLM evaluates candidate code or determines scores."
)


# ---------------------------------------------------------------------------
# Data readers (with production guard & Supabase primary)
# ---------------------------------------------------------------------------

def _load_sessions_data(uid_str: str) -> List[Dict[str, Any]]:
    """
    Loads completed assessment sessions for the student.
    Queries Supabase first if configured. In production mode, rejects local JSON fallback.
    """
    settings = get_settings()
    sessions: List[Dict[str, Any]] = []

    # 1. Query Supabase if configured
    if settings.is_supabase_configured:
        try:
            client = service_client()
            res = (
                client.table("assessment_sessions")
                .select("*")
                .eq("user_id", uid_str)
                .eq("status", "completed")
                .execute()
            )
            if res.data:
                sessions = res.data
        except Exception as e:
            logger.warning("Supabase session query failed: %s", e)
            if settings.app_env == "production":
                raise HTTPException(
                    status_code=503,
                    detail="Production database unavailable. Local JSON fallback is restricted in production.",
                )

    # 2. Local JSON fallback only in non-production environments
    if not sessions:
        if settings.app_env == "production":
            raise HTTPException(
                status_code=503,
                detail="Production database required. Local filesystem storage is disabled in production.",
            )
        if os.path.exists(SESSIONS_FILE):
            with _sessions_lock:
                try:
                    with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            sessions = list(data.values())
                        elif isinstance(data, list):
                            sessions = data
                except Exception as exc:
                    logger.error("Failed to read local sessions file: %s", exc)

    return sessions


def _load_codetrace_data(session_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Loads CodeTrace events for the specified session IDs.
    Queries Supabase if configured; falls back to local JSON only in non-production environments.
    """
    if not session_ids:
        return []

    settings = get_settings()
    events: List[Dict[str, Any]] = []

    if settings.is_supabase_configured:
        try:
            client = service_client()
            res = (
                client.table("codetrace_events")
                .select("*")
                .in_("session_id", session_ids)
                .order("created_at", desc=False)
                .execute()
            )
            if res.data:
                events = res.data
        except Exception as e:
            logger.warning("Supabase CodeTrace query failed: %s", e)

    if not events:
        if settings.app_env == "production":
            return []  # In production, do not read local json
        if os.path.exists(CODETRACE_FILE):
            with _codetrace_lock:
                try:
                    with open(CODETRACE_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            events = data
                except Exception as exc:
                    logger.error("Failed to read local CodeTrace file: %s", exc)

    return events


# ---------------------------------------------------------------------------
# Core Deterministic Scoring Engine
# ---------------------------------------------------------------------------

class TelemetryStatus:
    SELF_SUFFICIENT = "self_sufficient"
    ASSISTED = "assisted"
    UNKNOWN = "unknown"


def compute_composite_score(
    questions_passed: int,
    total_questions: int,
    tier: str,
    codetrace_events: List[Dict[str, Any]],
) -> Tuple[float, float, float, float, str]:
    """
    Compute deterministic score components without arbitrary tier multipliers:
      - raw_correctness_pct: (questions_passed / total_questions) * 100.0 (0-100)
      - test_score_component: (questions_passed / total_questions) * 80.0 (0-80)
      - ai_efficiency_component: derived from constructive CodeTrace signals (0-20)
      - composite_score: test_score_component + ai_efficiency_component (0-100)
      - telemetry_status: 'self_sufficient' | 'assisted' | 'unknown'

    Returns:
        (composite_score, test_score_component, ai_efficiency_component, raw_correctness_pct, telemetry_status)
    """
    if total_questions <= 0:
        return 0.0, 0.0, 0.0, 0.0, TelemetryStatus.UNKNOWN

    raw_ratio = max(0.0, min(1.0, questions_passed / total_questions))
    raw_correctness_pct = round(raw_ratio * 100.0, 1)

    # Test score component: pure correctness scaled to max 80 points
    test_score = round(raw_ratio * 80.0, 1)

    # AI Efficiency Component (max 20 points) & Telemetry Status
    ai_efficiency, telemetry_status = _compute_ai_efficiency(codetrace_events)

    composite = round(min(100.0, test_score + ai_efficiency), 1)
    return composite, test_score, ai_efficiency, raw_correctness_pct, telemetry_status


def _compute_ai_efficiency(events: List[Dict[str, Any]]) -> Tuple[float, str]:
    """
    Deterministic AI efficiency score from CodeTrace telemetry.

    Status Categories:
      1. UNKNOWN: Missing or empty CodeTrace telemetry. Does NOT award the
         20/20 self-sufficiency baseline. Assigns neutral unproven baseline (10.0).
      2. SELF_SUFFICIENT: Confirmed telemetry present with 0 hints requested.
         Awarded full 20.0 baseline (independent problem solving).
      3. ASSISTED: Telemetry records hint requests:
         - Baseline: 12.0
         - Active Verification: +4.0 (sample_run after guidance)
         - Positive Progression: +4.0 (code delta after guidance)
         - Spam Protection: -3.0 (consecutive requests with 0 code edits)
         - Bounded strictly in [0.0, 20.0].

    Returns:
        (efficiency_score, telemetry_status)
    """
    if not events:
        # Unknown status: telemetry missing / unrecorded. Do not represent as verified self-sufficient.
        return 10.0, TelemetryStatus.UNKNOWN

    # Identify hint events
    hint_events = [
        e for e in events
        if e.get("metrics", {}).get("hint_requested") or e.get("metrics", {}).get("hint_level")
    ]

    # Confirmed self-sufficiency: events exist, but zero hints requested
    if not hint_events:
        return 20.0, TelemetryStatus.SELF_SUFFICIENT

    score = 12.0

    # Signal 1: Active verification — sample run executed after receiving guidance
    first_hint_idx = -1
    for i, ev in enumerate(events):
        if ev.get("metrics", {}).get("hint_requested") or ev.get("metrics", {}).get("hint_level"):
            first_hint_idx = i
            break

    sample_runs_after_hint = [
        ev for i, ev in enumerate(events)
        if i > first_hint_idx and ev.get("event_type") == "sample_run"
    ]
    if sample_runs_after_hint:
        score += 4.0

    # Signal 2: Code progression after guidance
    chars_at_hint = (
        events[first_hint_idx].get("diff_summary", {}).get("total_chars")
        if first_hint_idx >= 0 else 0
    )
    final_chars = events[-1].get("diff_summary", {}).get("total_chars", 0)

    if final_chars is not None and chars_at_hint is not None and final_chars != chars_at_hint:
        score += 4.0

    # Signal 3: Spam check — repeated hint requests with zero code changes in between
    spam_detected = False
    consecutive_hints_without_edit = 0
    last_code_length = None

    for ev in events:
        is_hint = ev.get("metrics", {}).get("hint_requested") or ev.get("metrics", {}).get("hint_level")
        current_len = ev.get("diff_summary", {}).get("total_chars")

        if is_hint:
            if last_code_length is not None and current_len == last_code_length:
                consecutive_hints_without_edit += 1
            last_code_length = current_len
        else:
            consecutive_hints_without_edit = 0

        if consecutive_hints_without_edit >= 2:
            spam_detected = True
            break

    if spam_detected:
        score -= 3.0

    final_score = max(0.0, min(20.0, round(score, 1)))
    return final_score, TelemetryStatus.ASSISTED


# ---------------------------------------------------------------------------
# Analytics Aggregator
# ---------------------------------------------------------------------------

def compute_student_analytics(user_id: uuid.UUID) -> AnalyticsResponse:
    """
    Build a complete deterministic analytics report for a student.
    - Strictly validates completed status and user ownership.
    - Deduplicates assessment sessions by session_id.
    - Strictly isolates practice track results from verified candidate scores.
    """
    uid_str = str(user_id)
    raw_sessions = _load_sessions_data(uid_str)

    # Strict deduplication and ownership check
    seen_sids: set[str] = set()
    completed_sessions: List[Dict[str, Any]] = []

    for s in raw_sessions:
        sid = str(s.get("session_id", ""))
        if not sid or sid in seen_sids:
            continue
        if s.get("user_id") != uid_str:
            continue
        if s.get("status") != "completed":
            continue
        seen_sids.add(sid)
        completed_sessions.append(s)

    # Sort chronologically
    completed_sessions.sort(key=lambda s: s.get("created_at", ""))

    session_ids = [s["session_id"] for s in completed_sessions]
    all_events = _load_codetrace_data(session_ids)

    # Build per-session codetrace lookup
    events_by_session: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for ev in all_events:
        sid = str(ev.get("session_id", ""))
        if sid:
            events_by_session[sid].append(ev)

    # Aggregators
    trend: List[TrendPoint] = []
    domain_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "sessions": 0, "attempted": 0, "passed": 0
    })
    tier_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "sessions": 0, "composites": [], "total_q": 0, "total_passed": 0
    })

    verified_composites: List[float] = []
    practice_composites: List[float] = []
    verified_questions_passed = 0
    verified_questions_total = 0

    total_hints = 0
    l1_hints = 0
    l2_hints = 0
    l3_hints = 0
    sessions_with_hints = 0

    for sess in completed_sessions:
        sid = sess["session_id"]
        tier = sess.get("tier", "novice").lower()
        track = sess.get("track", "verified").lower()
        domain = sess.get("domain", "General")
        results = sess.get("results") or []
        created_at = sess.get("created_at", "")
        date_str = created_at[:10] if created_at else "unknown"

        questions_passed = sum(1 for r in results if r.get("all_passed"))
        total_qs = len(results)

        # CodeTrace events for this session
        sess_events = events_by_session.get(sid, [])

        composite, test_score, ai_eff, raw_correctness, telemetry_status = compute_composite_score(
            questions_passed, total_qs, tier, sess_events
        )

        trend.append(TrendPoint(
            session_id=sid,
            date=date_str,
            composite_score=composite,
            test_score=test_score,
            raw_correctness_pct=raw_correctness,
            ai_efficiency_score=ai_eff,
            telemetry_status=telemetry_status,
            tier=tier,
            track=track,
            domain=domain,
            questions_passed=questions_passed,
            total_questions=total_qs,
        ))

        # Domain performance
        dm = domain_map[domain]
        dm["sessions"] += 1
        dm["attempted"] += total_qs
        dm["passed"] += questions_passed

        # Skill mastery by tier
        difficulty = {"novice": "easy", "adept": "medium", "master": "hard"}.get(tier, "easy")
        tm = tier_map[tier]
        tm["sessions"] += 1
        tm["composites"].append(composite)
        tm["total_q"] += total_qs
        tm["total_passed"] += questions_passed
        tm["difficulty"] = difficulty

        # STRICT PRACTICE ISOLATION
        if track == "verified":
            verified_composites.append(composite)
            verified_questions_passed += questions_passed
            verified_questions_total += total_qs
        else:
            practice_composites.append(composite)

        # Hint utilization from CodeTrace metrics
        sess_has_hints = False
        for ev in sess_events:
            m = ev.get("metrics", {})
            hl = m.get("hint_level")
            if hl:
                total_hints += 1
                sess_has_hints = True
                if hl == 1:
                    l1_hints += 1
                elif hl == 2:
                    l2_hints += 1
                elif hl == 3:
                    l3_hints += 1
        if sess_has_hints:
            sessions_with_hints += 1

    # Build domain performance list
    domain_performance: List[DomainPerformance] = []
    for domain, dm in domain_map.items():
        pass_rate = round((dm["passed"] / dm["attempted"] * 100), 1) if dm["attempted"] > 0 else 0.0
        domain_performance.append(DomainPerformance(
            domain=domain,
            sessions=dm["sessions"],
            questions_attempted=dm["attempted"],
            questions_passed=dm["passed"],
            pass_rate=pass_rate,
        ))
    domain_performance.sort(key=lambda x: x.pass_rate, reverse=True)

    # Build skill mastery list
    skill_mastery: List[SkillMasteryItem] = []
    for tier_key, tm in tier_map.items():
        composites = tm["composites"]
        avg_c = round(sum(composites) / len(composites), 1) if composites else 0.0
        best_c = round(max(composites), 1) if composites else 0.0
        skill_mastery.append(SkillMasteryItem(
            tier=tier_key,
            difficulty=tm.get("difficulty", "easy"),
            sessions=tm["sessions"],
            avg_composite_score=avg_c,
            best_composite_score=best_c,
            total_questions=tm["total_q"],
            total_passed=tm["total_passed"],
        ))

    # Hint utilization summary
    total_sess = len(completed_sessions)
    avg_hints = round(total_hints / total_sess, 2) if total_sess > 0 else 0.0
    ai_eff_scores = [t.ai_efficiency_score for t in trend]
    ai_eff_avg = round(sum(ai_eff_scores) / len(ai_eff_scores), 1) if ai_eff_scores else 0.0

    hint_util = HintUtilizationSummary(
        total_hint_requests=total_hints,
        level_1_hints=l1_hints,
        level_2_hints=l2_hints,
        level_3_hints=l3_hints,
        sessions_with_hints=sessions_with_hints,
        avg_hints_per_session=avg_hints,
        ai_efficiency_avg=ai_eff_avg,
    )

    # STRICT CANDIDATE EVALUATION: Derived exclusively from verified sessions
    overall_avg_composite = (
        round(sum(verified_composites) / len(verified_composites), 1)
        if verified_composites else 0.0
    )
    best_composite_score = (
        round(max(verified_composites), 1)
        if verified_composites else 0.0
    )
    overall_test_pass_rate = (
        round((verified_questions_passed / verified_questions_total * 100), 1)
        if verified_questions_total > 0 else 0.0
    )
    practice_avg_composite = (
        round(sum(practice_composites) / len(practice_composites), 1)
        if practice_composites else None
    )

    return AnalyticsResponse(
        user_id=uid_str,
        generated_at=datetime.now(timezone.utc).isoformat(),
        total_sessions=total_sess,
        verified_sessions=len(verified_composites),
        practice_sessions=len(practice_composites),
        overall_avg_composite=overall_avg_composite,
        best_composite_score=best_composite_score,
        overall_test_pass_rate=overall_test_pass_rate,
        practice_avg_composite=practice_avg_composite,
        trend=trend,
        domain_performance=domain_performance,
        skill_mastery=skill_mastery,
        hint_utilization=hint_util,
        scoring_formula_note=SCORING_FORMULA_NOTE,
    )

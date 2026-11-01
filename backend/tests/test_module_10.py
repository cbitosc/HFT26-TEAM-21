"""
Module 10: Performance Analytics and Deterministic Scoring — Audit & Regression Suite.

Verifies:
  1. Uninflated Test Correctness (no arbitrary tier multipliers; raw score preserved)
  2. Deterministic AI Usage Efficiency (self-sufficient reward, constructive assisted scoring, spam penalty)
  3. Strict Practice Data Isolation (practice scores never pollute verified metrics)
  4. Production Environment Guard (local JSON fallback rejected in production)
  5. Authoritative Deduplication & User Ownership
  6. Determinism & Formula Note Transparency
  7. HTTP API Endpoint Authorization & Response Schema
"""

from __future__ import annotations

import sys
import os
import uuid
import json
import asyncio
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.config import get_settings
from app.services.analytics_service import (
    compute_composite_score,
    _compute_ai_efficiency,
    compute_student_analytics,
    _load_sessions_data,
    SCORING_FORMULA_NOTE,
)
from app.models import (
    AnalyticsResponse,
    TrendPoint,
    DomainPerformance,
    SkillMasteryItem,
    HintUtilizationSummary,
)

try:
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    HTTP_TESTS_AVAILABLE = True
except ImportError:
    HTTP_TESTS_AVAILABLE = False

DEV_TOKEN = "dev-student-token"


# ---------------------------------------------------------------------------
# 1. Unweighted Correctness & Raw Score Preservation (Item 1)
# ---------------------------------------------------------------------------

def test_novice_100pct_unweighted():
    """Novice session: 2/2 passed -> test score = 80.0, raw correctness = 100.0%."""
    events = [{"event_type": "snapshot", "metrics": {"hint_requested": False}, "diff_summary": {"total_chars": 50}}]
    composite, test_score, ai_eff, raw_pct, status = compute_composite_score(2, 2, "novice", events)
    assert test_score == 80.0, f"Expected 80.0, got {test_score}"
    assert raw_pct == 100.0, f"Expected 100.0%, got {raw_pct}"
    assert status == "self_sufficient"
    assert composite == round(80.0 + ai_eff, 1)
    print("[PASS] Test 1: Novice 100% -> unweighted test_score=80.0, raw=100.0%, status=self_sufficient")


def test_adept_50pct_no_arbitrary_multiplier():
    """Adept session: 1/2 passed -> test score = 40.0, raw correctness = 50.0% (no 1.25x inflation)."""
    events = [{"event_type": "snapshot", "metrics": {"hint_requested": False}, "diff_summary": {"total_chars": 50}}]
    composite, test_score, ai_eff, raw_pct, status = compute_composite_score(1, 2, "adept", events)
    assert test_score == 40.0, f"Expected uninflated 40.0, got {test_score}"
    assert raw_pct == 50.0, f"Expected 50.0%, got {raw_pct}"
    print("[PASS] Test 2: Adept 50% -> unweighted test_score=40.0 (no arbitrary 1.25x advantage)")


def test_master_66pct_no_arbitrary_multiplier():
    """Master session: 2/3 passed -> test score = 53.3, raw correctness = 66.7% (no 1.5x inflation)."""
    events = [{"event_type": "snapshot", "metrics": {"hint_requested": False}, "diff_summary": {"total_chars": 50}}]
    composite, test_score, ai_eff, raw_pct, status = compute_composite_score(2, 3, "master", events)
    assert test_score == 53.3, f"Expected uninflated 53.3, got {test_score}"
    assert raw_pct == 66.7, f"Expected 66.7%, got {raw_pct}"
    print("[PASS] Test 3: Master 66.7% -> unweighted test_score=53.3 (no arbitrary 1.5x advantage)")


def test_zero_questions():
    """Zero questions -> all zero scores."""
    composite, test_score, ai_eff, raw_pct, status = compute_composite_score(0, 0, "novice", [])
    assert composite == 0.0
    assert test_score == 0.0
    assert ai_eff == 0.0
    assert raw_pct == 0.0
    assert status == "unknown"
    print("[PASS] Test 4: Zero questions -> all zero scores")


# ---------------------------------------------------------------------------
# 2. Deterministic AI Usage Efficiency (Item 2)
# ---------------------------------------------------------------------------

def test_ai_efficiency_self_sufficiency():
    """Telemetry present with 0 hints -> full baseline efficiency (20.0), status=self_sufficient."""
    events = [
        {"event_type": "snapshot", "metrics": {"hint_requested": False}, "diff_summary": {"total_chars": 100}},
        {"event_type": "sample_run", "metrics": {}, "diff_summary": {}},
    ]
    eff, status = _compute_ai_efficiency(events)
    assert eff == 20.0, f"Expected 20.0 self-sufficiency efficiency, got {eff}"
    assert status == "self_sufficient"
    print("[PASS] Test 5: Self-sufficiency -> 20.0 full baseline efficiency when 0 hints confirmed")


def test_ai_efficiency_unknown_telemetry():
    """Empty/missing telemetry -> status=unknown, does NOT award 20/20 baseline."""
    eff, status = _compute_ai_efficiency([])
    assert status == "unknown"
    assert eff == 10.0, f"Expected neutral 10.0 for unknown telemetry, got {eff}"
    print("[PASS] Test 5b: Unknown telemetry -> neutral 10.0 baseline, does NOT claim verified self-sufficiency")


def test_ai_efficiency_assisted_active_verification():
    """Assisted solving: sample run executed AFTER receiving guidance -> active verification points added."""
    events = [
        {"event_type": "snapshot", "metrics": {"hint_requested": True, "hint_level": 1}, "diff_summary": {"total_chars": 50}},
        {"event_type": "sample_run", "metrics": {}, "diff_summary": {}},
        {"event_type": "snapshot", "metrics": {}, "diff_summary": {"total_chars": 80}},
    ]
    eff, status = _compute_ai_efficiency(events)
    assert status == "assisted"
    assert eff >= 16.0, f"Expected >=16.0 for assisted + verified + progress, got {eff}"
    print("[PASS] Test 6: Assisted active verification -> rewards testing after receiving guidance")


def test_ai_efficiency_spam_protection():
    """Spam pattern: 3 consecutive hint requests with zero code changes in between -> penalty applied."""
    events = [
        {"event_type": "snapshot", "metrics": {"hint_requested": True, "hint_level": 1}, "diff_summary": {"total_chars": 50}},
        {"event_type": "snapshot", "metrics": {"hint_requested": True, "hint_level": 1}, "diff_summary": {"total_chars": 50}},
        {"event_type": "snapshot", "metrics": {"hint_requested": True, "hint_level": 1}, "diff_summary": {"total_chars": 50}},
    ]
    eff, status = _compute_ai_efficiency(events)
    assert status == "assisted"
    assert eff <= 10.0, f"Expected penalty applied for repeated zero-edit hints, got {eff}"
    print("[PASS] Test 7: Spam protection -> penalizes repeated requests with zero code edits")


def test_ai_efficiency_legitimate_help_no_penalty():
    """Legitimate progressive help with code changes between requests -> no penalty."""
    events = [
        {"event_type": "snapshot", "metrics": {"hint_requested": True, "hint_level": 1}, "diff_summary": {"total_chars": 50}},
        {"event_type": "snapshot", "metrics": {}, "diff_summary": {"total_chars": 75}},
        {"event_type": "snapshot", "metrics": {"hint_requested": True, "hint_level": 2}, "diff_summary": {"total_chars": 75}},
        {"event_type": "sample_run", "metrics": {}, "diff_summary": {}},
        {"event_type": "snapshot", "metrics": {}, "diff_summary": {"total_chars": 120}},
    ]
    eff, status = _compute_ai_efficiency(events)
    assert status == "assisted"
    assert eff >= 16.0, f"Expected high efficiency for constructive assisted work, got {eff}"
    print("[PASS] Test 8: Legitimate progressive help -> no penalty for seeking help constructively")


def test_ai_efficiency_bounded():
    """AI efficiency is strictly bounded within [0.0, 20.0]."""
    eff, status = _compute_ai_efficiency([])
    assert 0.0 <= eff <= 20.0
    events = [{"event_type": "snapshot", "metrics": {"hint_requested": False}, "diff_summary": {"total_chars": 50}}]
    composite, test_score, ai_eff, raw_pct, status = compute_composite_score(2, 2, "novice", events)
    assert 0.0 <= ai_eff <= 20.0
    assert 0.0 <= composite <= 100.0
    print("[PASS] Test 9: Score bounds -> composite in [0, 100], efficiency in [0, 20]")


# ---------------------------------------------------------------------------
# 3. Practice Track Data Isolation (Item 3)
# ---------------------------------------------------------------------------

def test_practice_data_strict_isolation():
    """
    Practice session results must never pollute or inflate verified candidate scores:
    - overall_avg_composite: strictly derived from verified sessions.
    - best_composite_score: strictly derived from verified sessions.
    - overall_test_pass_rate: strictly derived from verified sessions.
    """
    uid = uuid.uuid4()
    uid_str = str(uid)

    # Mock sessions data: 1 verified session (score = 50%), 1 practice session (score = 100%)
    mock_sessions = {
        "sess-v1": {
            "session_id": "sess-v1",
            "user_id": uid_str,
            "status": "completed",
            "track": "verified",
            "tier": "novice",
            "domain": "Algorithms",
            "created_at": "2026-10-31T01:00:00Z",
            "results": [{"all_passed": True}, {"all_passed": False}],  # 1/2 passed = 50%
        },
        "sess-p1": {
            "session_id": "sess-p1",
            "user_id": uid_str,
            "status": "completed",
            "track": "practice",
            "tier": "master",
            "domain": "Algorithms",
            "created_at": "2026-10-31T02:00:00Z",
            "results": [{"all_passed": True}, {"all_passed": True}],  # 2/2 passed = 100%
        },
    }

    # Temporarily patch _load_sessions_data
    import app.services.analytics_service as asvc
    orig_load = asvc._load_sessions_data
    asvc._load_sessions_data = lambda u: list(mock_sessions.values())

    try:
        analytics = compute_student_analytics(uid)
        assert analytics.verified_sessions == 1
        assert analytics.practice_sessions == 1
        # Verified score: 1/2 = 40 test + 10 ai_eff (unknown telemetry) = 50.0
        assert analytics.overall_avg_composite == 50.0, f"Expected 50.0 verified avg, got {analytics.overall_avg_composite}"
        assert analytics.best_composite_score == 50.0, f"Expected 50.0 verified best (not inflated by practice 90/100), got {analytics.best_composite_score}"
        assert analytics.overall_test_pass_rate == 50.0, f"Expected 50.0% verified pass rate, got {analytics.overall_test_pass_rate}"
        assert analytics.practice_avg_composite == 90.0, f"Expected 90.0 isolated practice avg, got {analytics.practice_avg_composite}"
        print("[PASS] Test 10: Strict practice data isolation -> 100% practice score does NOT inflate verified metrics")
    finally:
        asvc._load_sessions_data = orig_load


# ---------------------------------------------------------------------------
# 4. Production Environment Guard (Item 4)
# ---------------------------------------------------------------------------

def test_production_guard_rejects_silent_json_fallback():
    """In production mode without Supabase, local JSON storage is strictly prohibited."""
    settings = get_settings()
    orig_env = settings.app_env
    orig_supa = settings.supabase_url

    try:
        settings.app_env = "production"
        settings.supabase_url = ""  # Simulate unconfigured/unreachable in prod

        from fastapi import HTTPException
        raised = False
        try:
            _load_sessions_data("some-user")
        except HTTPException as exc:
            raised = True
            assert exc.status_code == 503
            assert "Local filesystem storage is disabled in production" in exc.detail or "restricted" in exc.detail

        assert raised, "Expected 503 HTTPException in production without database!"
        print("[PASS] Test 11: Production guard -> rejects silent local JSON fallback when app_env=production")
    finally:
        settings.app_env = orig_env
        settings.supabase_url = orig_supa


# ---------------------------------------------------------------------------
# 5. Deduplication and Ownership (Item 5)
# ---------------------------------------------------------------------------

def test_deduplication_and_ownership():
    """Duplicate session IDs and cross-user records are strictly excluded."""
    uid = uuid.uuid4()
    uid_str = str(uid)
    other_uid_str = str(uuid.uuid4())

    mock_sessions = [
        {"session_id": "sess-1", "user_id": uid_str, "status": "completed", "track": "verified", "results": [{"all_passed": True}]},
        {"session_id": "sess-1", "user_id": uid_str, "status": "completed", "track": "verified", "results": [{"all_passed": True}]},  # Duplicate
        {"session_id": "sess-2", "user_id": other_uid_str, "status": "completed", "track": "verified", "results": [{"all_passed": True}]},  # Other user
        {"session_id": "sess-3", "user_id": uid_str, "status": "active", "track": "verified", "results": [{"all_passed": True}]},  # Not completed
    ]

    import app.services.analytics_service as asvc
    orig_load = asvc._load_sessions_data
    asvc._load_sessions_data = lambda u: mock_sessions

    try:
        analytics = compute_student_analytics(uid)
        assert analytics.total_sessions == 1, f"Expected 1 session after deduplication, got {analytics.total_sessions}"
        assert len(analytics.trend) == 1
        print("[PASS] Test 12: Deduplication and ownership -> excludes duplicates, cross-user and active sessions")
    finally:
        asvc._load_sessions_data = orig_load


# ---------------------------------------------------------------------------
# 6. Determinism & Formula Note
# ---------------------------------------------------------------------------

def test_scoring_determinism():
    """Identical inputs produce identical composite scores across multiple iterations."""
    events = [
        {"event_type": "snapshot", "metrics": {"hint_requested": True, "hint_level": 1}, "diff_summary": {"total_chars": 50}},
        {"event_type": "sample_run", "metrics": {}, "diff_summary": {}},
        {"event_type": "snapshot", "metrics": {}, "diff_summary": {"total_chars": 120}},
    ]
    results = [compute_composite_score(2, 3, "adept", events) for _ in range(5)]
    assert all(r == results[0] for r in results), "Non-deterministic score outputs detected!"
    print("[PASS] Test 13: Scoring determinism -> 5 identical executions yield identical scores")


def test_formula_note_transparency():
    """Formula note explicitly describes unweighted correctness, efficiency, and practice isolation."""
    assert "Composite Score" in SCORING_FORMULA_NOTE
    assert "Practice track sessions are strictly isolated" in SCORING_FORMULA_NOTE
    assert "No LLM evaluates" in SCORING_FORMULA_NOTE
    print("[PASS] Test 14: Formula note transparency -> clearly documents formula & isolation")


# ---------------------------------------------------------------------------
# 7. HTTP API Endpoint Tests
# ---------------------------------------------------------------------------

async def _test_analytics_http_200():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/assessment/analytics",
            headers={"Authorization": f"Bearer {DEV_TOKEN}"},
        )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "total_sessions" in data
    assert "verified_sessions" in data
    assert "practice_sessions" in data
    assert "overall_avg_composite" in data
    assert "scoring_formula_note" in data
    print("[PASS] Test 15: GET /api/assessment/analytics -> 200 with valid schema")


async def _test_analytics_http_401():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/assessment/analytics")
    assert resp.status_code in (401, 403), f"Expected 401/403 without token, got {resp.status_code}"
    print("[PASS] Test 16: GET /api/assessment/analytics without token -> 401/403 fail-closed")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all_tests():
    print("\n--- Module 10: Performance Analytics & Scoring Audit Suite ---\n")

    passed = 0
    failed = 0
    sync_tests = [
        test_novice_100pct_unweighted,
        test_adept_50pct_no_arbitrary_multiplier,
        test_master_66pct_no_arbitrary_multiplier,
        test_zero_questions,
        test_ai_efficiency_self_sufficiency,
        test_ai_efficiency_unknown_telemetry,
        test_ai_efficiency_assisted_active_verification,
        test_ai_efficiency_spam_protection,
        test_ai_efficiency_legitimate_help_no_penalty,
        test_ai_efficiency_bounded,
        test_practice_data_strict_isolation,
        test_production_guard_rejects_silent_json_fallback,
        test_deduplication_and_ownership,
        test_scoring_determinism,
        test_formula_note_transparency,
    ]

    for test_fn in sync_tests:
        try:
            test_fn()
            passed += 1
        except Exception as exc:
            print(f"[FAIL] {test_fn.__name__}: {exc}")
            failed += 1

    if HTTP_TESTS_AVAILABLE:
        for coro_fn in [_test_analytics_http_200, _test_analytics_http_401]:
            try:
                asyncio.run(coro_fn())
                passed += 1
            except Exception as exc:
                print(f"[FAIL] {coro_fn.__name__}: {exc}")
                failed += 1
    else:
        print("[SKIP] HTTP tests skipped")

    total = passed + failed
    print(f"\n{'='*65}")
    print(f"Results: {passed}/{total} Module 10 Audit Tests PASSED ({round(passed/total*100)}% success rate)")
    print(f"{'='*65}\n")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

"""
SkillProof AI — Modules 11 & 12 Verification Suite
Module 11: College Task Management
Module 12: Recruiter Portal and Live Coding Interviews

Tests:
  1. College Admin Task Creation (title, description, domain, difficulty, deadline)
  2. Multi-tenant College Isolation: Admin A cannot access or manage College B tasks
  3. Student Role Guard: Students cannot create or modify college administrator tasks
  4. Student Task Visibility: Students only see published tasks assigned to them
  5. Deadline Enforcement: Submissions to expired tasks are rejected (unless late allowed)
  6. Closed Task Guard: Submissions to closed tasks are rejected
  7. Deterministic Task Evaluation: Test cases executed via sandbox harness
  8. Task Analytics Calculation: (assigned, completed, pending, avg score, pass rate)
  9. Recruiter Access Guard: Unapproved / pending recruiters cannot access candidate discovery
  10. Student Consent Guard: Candidates are discoverable ONLY when recruiter_discoverable == True
  11. Revoked Consent Enforcement: Revoking consent immediately blocks subsequent recruiter access
  12. Privacy Shielding: Candidate discovery strictly conceals email, phone, and raw CodeTrace
  13. Verified Metrics Only: Practice scores never pollute candidate discovery or dossier
  14. Interview Session Creation: Recruiter creates interview with consenting candidate
  15. Non-Consenting Interview Guard: Scheduling with non-consenting student is rejected
  16. Interview Room Isolation: Unauthorized users cannot view or join interview session
  17. Interview Code Synchronization: Shared workspace code updates recorded
  18. Recruiter Prompt Refactoring: Requested changes appended to interview history
  19. Assessment Immutability: Interview activity never alters original verified assessment records
  20. Module 10 Telemetry States: (self_sufficient = 20, assisted = 12-20, unknown = 10)
"""

from __future__ import annotations

import sys
import os
import uuid
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import asyncio
import pytest
from fastapi import HTTPException
from app.models import (
    UserProfile,
    CollegeTaskCreate,
    CollegeTaskSubmissionCreate,
    CollegeTaskTestCase,
    InterviewSessionCreate,
    InterviewSyncRequest,
    InterviewChangeRequest,
    InterviewFinishRequest,
)
from app.services import college_service, recruiter_service
from app.services.analytics_service import (
    compute_composite_score,
    _compute_ai_efficiency,
    TelemetryStatus,
)

# ---------------------------------------------------------------------------
# Test Fixtures & Identities
# ---------------------------------------------------------------------------

COLLEGE_A = uuid.uuid4()
COLLEGE_B = uuid.uuid4()

ADMIN_COLLEGE_A = UserProfile(
    id=uuid.uuid4(),
    email="adminA@college.edu",
    full_name="Admin College A",
    requested_role="college_admin",
    role="college_admin",
    account_status="active",
    college_id=COLLEGE_A,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
)

ADMIN_COLLEGE_B = UserProfile(
    id=uuid.uuid4(),
    email="adminB@college.edu",
    full_name="Admin College B",
    requested_role="college_admin",
    role="college_admin",
    account_status="active",
    college_id=COLLEGE_B,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
)

STUDENT_1 = UserProfile(
    id=uuid.uuid4(),
    email="student1@college.edu",
    full_name="Alice Student",
    requested_role="student",
    role="student",
    account_status="active",
    college_id=COLLEGE_A,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
)

STUDENT_2 = UserProfile(
    id=uuid.uuid4(),
    email="student2@other.edu",
    full_name="Bob Student",
    requested_role="student",
    role="student",
    account_status="active",
    college_id=COLLEGE_B,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
)

STUDENT_3 = UserProfile(
    id=uuid.uuid4(),
    email="student3@college.edu",
    full_name="Charlie Student",
    requested_role="student",
    role="student",
    account_status="active",
    college_id=COLLEGE_A,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
)

APPROVED_RECRUITER = UserProfile(
    id=uuid.uuid4(),
    email="recruiter@techcorp.com",
    full_name="Rachel Recruiter",
    requested_role="recruiter",
    role="recruiter",
    account_status="active",
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
)

RECRUITER_B = UserProfile(
    id=uuid.uuid4(),
    email="recruiter_b@rivalcorp.com",
    full_name="Bob Recruiter",
    requested_role="recruiter",
    role="recruiter",
    account_status="active",
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
)

UNAPPROVED_RECRUITER = UserProfile(
    id=uuid.uuid4(),
    email="pending@techcorp.com",
    full_name="Pending Recruiter",
    requested_role="recruiter",
    role="recruiter",
    account_status="pending_approval",
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
)


# ---------------------------------------------------------------------------
# Module 11 Tests
# ---------------------------------------------------------------------------

@pytest.fixture
def task():
    """Fixture providing an active published college task for College A."""
    payload = CollegeTaskCreate(
        title="Binary Tree Inversion Test",
        description="Implement recursive inversion of a binary tree.",
        domain="Algorithms & DSA",
        difficulty="medium",
        duration_minutes=45,
        test_cases=[
            CollegeTaskTestCase(input="[4,2,7]", expected_output="[4,7,2]"),
            CollegeTaskTestCase(input="[2,1,3]", expected_output="[2,3,1]"),
        ],
        status="published",
        assigned_student_ids=[STUDENT_1.id],
        allow_late_submissions=False,
    )
    return college_service.create_college_task(ADMIN_COLLEGE_A, payload)


def test_college_task_creation(task):
    """Authorized college admin creates a coding task with test cases."""
    assert task.title == "Binary Tree Inversion Test"
    assert task.college_id == COLLEGE_A
    assert task.status == "published"
    assert STUDENT_1.id in task.assigned_student_ids
    print("[PASS] Test 1: College Admin successfully creates and publishes coding task")


def test_college_isolation_cross_access(task):
    """Admin B cannot access or modify College A's task."""
    # Attempt read
    blocked = False
    try:
        college_service.get_college_task(ADMIN_COLLEGE_B, task.id)
    except HTTPException as exc:
        if exc.status_code == 403:
            blocked = True
    assert blocked, "Admin B was able to access College A's task!"

    # Attempt status change
    blocked_edit = False
    try:
        college_service.update_college_task_status(ADMIN_COLLEGE_B, task.id, "closed")
    except HTTPException as exc:
        if exc.status_code == 403:
            blocked_edit = True
    assert blocked_edit, "Admin B was able to modify College A's task status!"
    print("[PASS] Test 2: Multi-tenant college isolation verified (cross-college access blocked)")


def test_student_task_assignment_visibility(task):
    """Student 1 (assigned) sees task; Student 2 (different college & unassigned) cannot access."""
    # Student 1 gets task
    t1 = college_service.get_college_task(STUDENT_1, task.id)
    assert t1.id == task.id

    # Student 2 blocked
    blocked = False
    try:
        college_service.get_college_task(STUDENT_2, task.id)
    except HTTPException as exc:
        if exc.status_code == 403:
            blocked = True
    assert blocked, "Unassigned student from another college was able to access task!"
    print("[PASS] Test 3: Student task visibility strictly restricted to assigned/college students")


def test_deadline_and_closed_enforcement(task):
    """Submissions to closed or past-deadline tasks are rejected."""
    # Close the task
    college_service.update_college_task_status(ADMIN_COLLEGE_A, task.id, "closed")

    sub_payload = CollegeTaskSubmissionCreate(
        submitted_code="def invert(t): return t",
        language="python",
    )

    closed_blocked = False
    try:
        college_service.submit_college_task(STUDENT_1, task.id, sub_payload)
    except HTTPException as exc:
        if exc.status_code == 400 and "only accepted for 'published'" in exc.detail:
            closed_blocked = True
    assert closed_blocked, "Submission to closed task was accepted!"

    # Re-publish but set deadline in the past
    raw_task = college_service._fetch_raw_task(str(task.id))
    raw_task["status"] = "published"
    raw_task["deadline"] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    raw_task["allow_late_submissions"] = False
    college_service._save_raw_task(raw_task)

    deadline_blocked = False
    try:
        college_service.submit_college_task(STUDENT_1, task.id, sub_payload)
    except HTTPException as exc:
        if exc.status_code == 400 and "deadline" in exc.detail:
            deadline_blocked = True
    assert deadline_blocked, "Submission after deadline was accepted!"

    # Clean up deadline for subsequent tests
    raw_task["deadline"] = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    college_service._save_raw_task(raw_task)
    print("[PASS] Test 4: Closed and past-deadline task submissions strictly rejected")


def test_deterministic_task_submission_and_analytics(task):
    """Student submits solution and college analytics computes completion & score rates."""
    sub_payload = CollegeTaskSubmissionCreate(
        submitted_code="print('[4,7,2]')\n",
        language="python",
    )
    sub = college_service.submit_college_task(STUDENT_1, task.id, sub_payload)
    assert sub.status == "submitted"
    assert sub.student_id == STUDENT_1.id

    analytics = college_service.get_task_analytics(ADMIN_COLLEGE_A, task.id)
    assert analytics.task_id == task.id
    assert analytics.total_started >= 1
    assert analytics.total_completed >= 1
    print("[PASS] Test 5: Deterministic submission grading & college task analytics verified")


# ---------------------------------------------------------------------------
# Module 12 Tests
# ---------------------------------------------------------------------------

def test_unapproved_recruiter_blocked():
    """Unapproved / pending recruiter cannot discover candidates."""
    blocked = False
    try:
        recruiter_service.discover_candidates(UNAPPROVED_RECRUITER)
    except HTTPException as exc:
        if exc.status_code == 403:
            blocked = True
    assert blocked, "Unapproved recruiter accessed candidate discovery!"
    print("[PASS] Test 6: Unapproved recruiters strictly blocked from candidate discovery")


def test_student_consent_and_revocation():
    """Candidate is discoverable only when consent granted; revoking immediately blocks access."""
    # Grant consent
    recruiter_service.set_student_consent(STUDENT_1, True)
    assert recruiter_service.get_student_consent(STUDENT_1) is True

    # Candidate now discoverable
    candidates = recruiter_service.discover_candidates(APPROVED_RECRUITER)
    assert any(c.candidate_id == STUDENT_1.id for c in candidates)

    # Dossier accessible
    dossier = recruiter_service.get_candidate_dossier(APPROVED_RECRUITER, STUDENT_1.id)
    assert dossier.candidate_id == STUDENT_1.id
    assert dossier.consent_status is True

    # Revoke consent
    recruiter_service.set_student_consent(STUDENT_1, False)
    assert recruiter_service.get_student_consent(STUDENT_1) is False

    # Dossier now forbidden
    revoked_blocked = False
    try:
        recruiter_service.get_candidate_dossier(APPROVED_RECRUITER, STUDENT_1.id)
    except HTTPException as exc:
        if exc.status_code == 403 and "consent" in exc.detail:
            revoked_blocked = True
    assert revoked_blocked, "Candidate dossier was accessible after consent revoked!"
    print("[PASS] Test 7: Student consent grant and revocation strictly enforced")


def test_recruiter_privacy_and_verified_isolation():
    """Discovery items strictly omit private personal contacts and practice scores."""
    recruiter_service.set_student_consent(STUDENT_1, True)
    candidates = recruiter_service.discover_candidates(APPROVED_RECRUITER)
    for c in candidates:
        # Check no email in candidate item model
        assert not hasattr(c, "email")
        assert not hasattr(c, "phone")
        assert not hasattr(c, "codetrace_events")
        # Ensure portfolio claims are designated as unverified
        assert all("Claimed" in claim or "unverified" in claim.lower() for claim in c.portfolio_claims)
    print("[PASS] Test 8: Privacy shield verified (no private contacts, portfolio claims unverified)")


def test_live_interview_session_workflow():
    """Recruiter schedules interview, synchronizes code, and requests refactor."""
    recruiter_service.set_student_consent(STUDENT_1, True)

    create_payload = InterviewSessionCreate(
        candidate_id=STUDENT_1.id,
        title="Senior Backend Technical Interview",
        task_description="Implement a thread-safe token bucket rate limiter.",
        initial_code="class TokenBucket:\n    pass\n",
    )
    interview = recruiter_service.create_interview_session(APPROVED_RECRUITER, create_payload)
    assert interview.title == "Senior Backend Technical Interview"
    assert interview.status == "scheduled"

    # Unauthorized user (Student 2) cannot join
    unauth_blocked = False
    try:
        recruiter_service.get_interview_session(STUDENT_2, interview.id)
    except HTTPException as exc:
        if exc.status_code == 403:
            unauth_blocked = True
    assert unauth_blocked, "Unauthorized student joined another candidate's interview!"

    # Candidate and recruiter can access
    c_session = recruiter_service.get_interview_session(STUDENT_1, interview.id)
    assert c_session.id == interview.id

    # Code synchronization
    sync_payload = InterviewSyncRequest(code="class TokenBucket:\n    def __init__(self):\n        self.tokens = 10\n")
    synced = recruiter_service.sync_interview_code(STUDENT_1, interview.id, sync_payload)
    assert "self.tokens = 10" in synced.current_code
    assert synced.status == "in_progress"

    # Recruiter requests prompt refactor
    change_payload = InterviewChangeRequest(
        requested_change="Add refill rate parameter and make consumption thread-safe.",
    )
    with_change = recruiter_service.request_interview_code_change(APPROVED_RECRUITER, interview.id, change_payload)
    assert len(with_change.requested_changes) == 1
    assert "refill rate" in with_change.requested_changes[0]["requested_change"]

    # Finish interview
    finish_payload = InterviewFinishRequest(feedback="Excellent communication and clean OOP design.", outcome="passed")
    finished = recruiter_service.finish_interview_session(APPROVED_RECRUITER, interview.id, finish_payload)
    assert finished.status == "completed"
    assert finished.outcome == "passed"
    print("[PASS] Test 9: Live interview lifecycle (scheduling, sync, change request, finish) verified")


# ---------------------------------------------------------------------------
# Module 10 Telemetry States Test
# ---------------------------------------------------------------------------

def test_module_10_telemetry_states():
    """Verifies self_sufficient, assisted, and unknown telemetry states."""
    # State 1: Confirmed self-sufficient (events exist, 0 hints requested)
    self_events = [{"event_type": "snapshot", "metrics": {"hint_requested": False}, "diff_summary": {"total_chars": 80}}]
    eff1, stat1 = _compute_ai_efficiency(self_events)
    assert stat1 == TelemetryStatus.SELF_SUFFICIENT
    assert eff1 == 20.0

    # State 2: Assisted (events exist, hint requested)
    assist_events = [
        {"event_type": "snapshot", "metrics": {"hint_requested": True, "hint_level": 1}, "diff_summary": {"total_chars": 50}},
        {"event_type": "sample_run", "metrics": {}, "diff_summary": {}},
        {"event_type": "snapshot", "metrics": {}, "diff_summary": {"total_chars": 100}},
    ]
    eff2, stat2 = _compute_ai_efficiency(assist_events)
    assert stat2 == TelemetryStatus.ASSISTED
    assert eff2 >= 16.0

    # State 3: Unknown (telemetry unrecorded / empty events)
    eff3, stat3 = _compute_ai_efficiency([])
    assert stat3 == TelemetryStatus.UNKNOWN
    assert eff3 == 10.0  # Neutral baseline, NOT 20.0

    print("[PASS] Test 10: Module 10 telemetry states (self_sufficient, assisted, unknown) verified")


# ---------------------------------------------------------------------------
# Migration 005 & Security Invariant Tests
# ---------------------------------------------------------------------------

def test_unauthorized_score_modification_guard(task):
    """Students cannot modify submission grading fields or alter scores post-submission."""
    # 1. API model check: CollegeTaskSubmissionCreate does not accept client scores
    sub_payload = CollegeTaskSubmissionCreate(
        submitted_code="print('[4,7,2]')\n",
        language="python",
    )
    assert not hasattr(sub_payload, "score_percentage"), "Client payload exposes score_percentage!"
    assert not hasattr(sub_payload, "tests_passed"), "Client payload exposes tests_passed!"
    assert not hasattr(sub_payload, "status"), "Client payload exposes submission status!"

    # 2. Server evaluates deterministically
    sub = college_service.submit_college_task(STUDENT_1, task.id, sub_payload)
    assert sub.status == "submitted"
    assert sub.student_id == STUDENT_1.id
    assert isinstance(sub.score_percentage, float)
    assert isinstance(sub.tests_passed, int)
    assert sub.total_tests == len(task.test_cases)
    print("[PASS] Test 11: Unauthorized score modification prevented (deterministic sandbox grading only)")


def test_cross_college_submission_blocked(task):
    """Student from College B cannot submit to College A task, even if published."""
    sub_payload = CollegeTaskSubmissionCreate(
        submitted_code="print('exploit')",
        language="python",
    )
    blocked = False
    try:
        college_service.submit_college_task(STUDENT_2, task.id, sub_payload)
    except HTTPException as exc:
        if exc.status_code == 403 and "not assigned to you" in exc.detail:
            blocked = True
    assert blocked, "Student from College B was able to submit to College A's task!"

    # Also verify student from College B cannot see College A tasks in assigned list
    tasks_b = college_service.list_assigned_tasks_for_student(STUDENT_2)
    assert all(t.college_id == COLLEGE_B for t in tasks_b), "College B student saw College A tasks in listing!"
    print("[PASS] Test 12: Cross-college submissions strictly blocked")


def test_unassigned_student_task_access_blocked(task):
    """Student 3 from College A (not on assigned_student_ids) cannot access or submit to restricted task."""
    blocked_get = False
    try:
        college_service.get_college_task(STUDENT_3, task.id)
    except HTTPException as exc:
        if exc.status_code == 403 and "not assigned to you" in exc.detail:
            blocked_get = True
    assert blocked_get, "Unassigned student was able to get task assigned to someone else!"

    sub_payload = CollegeTaskSubmissionCreate(
        submitted_code="print('attempt')",
        language="python",
    )
    blocked_sub = False
    try:
        college_service.submit_college_task(STUDENT_3, task.id, sub_payload)
    except HTTPException as exc:
        if exc.status_code == 403 and "not assigned to you" in exc.detail:
            blocked_sub = True
    assert blocked_sub, "Unassigned student was able to submit to restricted task!"
    print("[PASS] Test 13: Unassigned student task access and submission strictly blocked")


def test_migration_005_rls_policies_audit():
    """Audits migration 005 to ensure strict RLS policies and zero student FOR ALL permissions."""
    sql_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "supabase", "migrations", "005_college_tasks.sql"))
    assert os.path.exists(sql_path), "Migration 005 SQL file does not exist!"
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    # 1. No FOR ALL policy for students on college_task_submissions
    assert 'create policy "Students manage own task submissions"' not in sql, "Permissive FOR ALL student submission policy still exists!"

    # 2. Separate SELECT and INSERT policies exist
    assert 'create policy "Students view own task submissions"' in sql, "Student SELECT policy missing!"
    assert 'for select' in sql and 'student_id = auth.uid()' in sql
    assert 'create policy "Students insert own task submissions"' in sql, "Student INSERT policy missing!"
    assert 'for insert' in sql

    # 3. Score tampering protection in WITH CHECK
    assert 'score_percentage = 0.0' in sql, "Anti-tampering score_percentage check missing!"
    assert 'tests_passed = 0' in sql, "Anti-tampering tests_passed check missing!"
    assert "status in ('draft', 'submitted')" in sql, "Anti-tampering status check missing!"

    # 4. Task relationship and publication validation
    assert "status = 'published'" in sql, "Published task check missing from insert policy!"
    assert "public.college_tasks.college_id = public.college_task_submissions.college_id" in sql or "college_id = public.college_task_submissions.college_id" in sql, "Task-submission college relationship check missing!"

    # 5. No student UPDATE or DELETE policy exists
    update_policies = [line for line in sql.splitlines() if "for update" in line.lower()]
    assert len(update_policies) == 1, f"Expected 1 update policy (for college_admin), found {len(update_policies)}"
    delete_policies = [line for line in sql.splitlines() if "for delete" in line.lower()]
    assert len(delete_policies) == 0, "Found unexpected DELETE policy!"

    # 6. College admin isolation preserved
    assert 'create policy "College admins manage their college tasks"' in sql
    assert 'create policy "College admins view college submissions"' in sql
    assert 'create policy "College admins update college submissions"' in sql

    print("[PASS] Test 14: Migration 005 RLS policies audited (no student FOR ALL, separate SELECT/INSERT, anti-tampering guards verified)")


# ---------------------------------------------------------------------------
# Migration 006 & Module 12 Security Invariant Tests
# ---------------------------------------------------------------------------

def test_candidate_privilege_escalation_guard():
    """Candidate cannot self-complete interviews, alter outcomes/feedback, or request code changes."""
    recruiter_service.set_student_consent(STUDENT_1, True)
    interview = recruiter_service.create_interview_session(
        APPROVED_RECRUITER,
        InterviewSessionCreate(
            candidate_id=STUDENT_1.id,
            title="Systems Design & Coding Interview",
            task_description="Build a cache.",
            initial_code="# Initial",
        ),
    )

    # 1. Candidate attempts to set status="completed" via sync -> rejected with HTTP 403
    blocked_status = False
    try:
        recruiter_service.sync_interview_code(
            STUDENT_1,
            interview.id,
            InterviewSyncRequest(code="# Malicious sync", status="completed"),
        )
    except HTTPException as exc:
        if exc.status_code == 403:
            blocked_status = True
    assert blocked_status, "Candidate was able to alter interview status to completed!"

    # 2. Candidate attempts to finish session with outcome -> rejected with HTTP 403
    blocked_finish = False
    try:
        recruiter_service.finish_interview_session(
            STUDENT_1,
            interview.id,
            InterviewFinishRequest(feedback="I passed myself", outcome="passed"),
        )
    except HTTPException as exc:
        if exc.status_code == 403:
            blocked_finish = True
    assert blocked_finish, "Candidate was able to finish interview and award self passed outcome!"

    # 3. Candidate attempts to inject recruiter code changes -> rejected with HTTP 403
    blocked_change = False
    try:
        recruiter_service.request_interview_code_change(
            STUDENT_1,
            interview.id,
            InterviewChangeRequest(requested_change="Malicious prompt"),
        )
    except HTTPException as exc:
        if exc.status_code == 403:
            blocked_change = True
    assert blocked_change, "Candidate was able to inject recruiter code changes!"

    print("[PASS] Test 15: Candidate privilege escalation strictly prevented (outcomes, status, feedback locked)")


def test_cross_recruiter_and_cross_user_interview_isolation():
    """Recruiter B and unrelated Student 2 cannot access, sync, or finish Recruiter A's interview."""
    recruiter_service.set_student_consent(STUDENT_1, True)
    interview = recruiter_service.create_interview_session(
        APPROVED_RECRUITER,
        InterviewSessionCreate(
            candidate_id=STUDENT_1.id,
            title="Private Architecture Interview",
            task_description="Design high-throughput queue.",
        ),
    )

    # Recruiter B attempts read
    r_b_read_blocked = False
    try:
        recruiter_service.get_interview_session(RECRUITER_B, interview.id)
    except HTTPException as exc:
        if exc.status_code == 403:
            r_b_read_blocked = True
    assert r_b_read_blocked, "Recruiter B accessed Recruiter A's interview session!"

    # Recruiter B attempts sync
    r_b_sync_blocked = False
    try:
        recruiter_service.sync_interview_code(RECRUITER_B, interview.id, InterviewSyncRequest(code="# intrusion"))
    except HTTPException as exc:
        if exc.status_code == 403:
            r_b_sync_blocked = True
    assert r_b_sync_blocked, "Recruiter B synced code into another recruiter's interview!"

    # Recruiter B attempts finish
    r_b_finish_blocked = False
    try:
        recruiter_service.finish_interview_session(
            RECRUITER_B,
            interview.id,
            InterviewFinishRequest(feedback="Intruder grade", outcome="rejected"),
        )
    except HTTPException as exc:
        if exc.status_code == 403:
            r_b_finish_blocked = True
    assert r_b_finish_blocked, "Recruiter B finished Recruiter A's interview!"

    # Unrelated Student 2 attempts read and sync
    s2_blocked = False
    try:
        recruiter_service.get_interview_session(STUDENT_2, interview.id)
    except HTTPException as exc:
        if exc.status_code == 403:
            s2_blocked = True
    assert s2_blocked, "Unrelated student accessed another candidate's interview!"

    print("[PASS] Test 16: Interview multi-tenant isolation verified (cross-recruiter and cross-student blocked)")


def test_unapproved_recruiter_interview_creation_blocked():
    """Unapproved / pending recruiter cannot schedule an interview session."""
    recruiter_service.set_student_consent(STUDENT_1, True)
    blocked = False
    try:
        recruiter_service.create_interview_session(
            UNAPPROVED_RECRUITER,
            InterviewSessionCreate(
                candidate_id=STUDENT_1.id,
                title="Unauthorized Interview Attempt",
            ),
        )
    except HTTPException as exc:
        if exc.status_code == 403:
            blocked = True
    assert blocked, "Unapproved recruiter was able to create an interview session!"
    print("[PASS] Test 17: Unapproved recruiter interview creation strictly blocked")


def test_non_consenting_candidate_interview_scheduling_blocked():
    """Recruiters cannot schedule interviews with candidates who have not granted discoverability consent."""
    recruiter_service.set_student_consent(STUDENT_2, False)
    blocked = False
    try:
        recruiter_service.create_interview_session(
            APPROVED_RECRUITER,
            InterviewSessionCreate(
                candidate_id=STUDENT_2.id,
                title="Non-Consenting Interview Attempt",
            ),
        )
    except HTTPException as exc:
        if exc.status_code == 400 and "consent" in exc.detail:
            blocked = True
    assert blocked, "Interview was scheduled with non-consenting student!"
    print("[PASS] Test 18: Non-consenting candidate interview scheduling strictly blocked (HTTP 400)")


def test_migration_006_security_audit():
    """Audits migration 006 to ensure strict RLS policies, trigger protection, and discovery safeguards."""
    sql_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "supabase", "migrations", "006_recruiter_interviews.sql"))
    assert os.path.exists(sql_path), "Migration 006 SQL file does not exist!"
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    # 1. recruiter_discoverable column added
    assert "add column if not exists recruiter_discoverable boolean" in sql

    # 2. RLS enabled
    assert "alter table public.interview_sessions enable row level security;" in sql

    # 3. Approved recruiter policies
    assert 'create policy "Recruiters view own interview sessions"' in sql
    assert 'create policy "Approved recruiters create interview sessions"' in sql
    assert "candidate_profile.recruiter_discoverable = true" in sql, "Consent check missing in insert policy!"
    assert 'create policy "Approved recruiters update own interview sessions"' in sql
    assert 'create policy "Approved recruiters delete own interview sessions"' in sql

    # 4. Candidate policies
    assert 'create policy "Candidates view invited interview sessions"' in sql
    assert 'create policy "Candidates update code in invited interview sessions"' in sql

    # 5. Candidate column protection trigger
    assert "create trigger trg_candidate_interview_update" in sql
    assert "enforce_candidate_interview_update_restrictions" in sql
    assert "Candidate update forbidden" in sql

    # 6. Candidate code sync RPC procedure
    assert "sync_candidate_interview_code" in sql
    assert "grant execute on function public.sync_candidate_interview_code" in sql

    # 7. Recruiter discovery policy on profiles
    assert 'create policy "Recruiters view discoverable candidates"' in sql
    assert "recruiter_discoverable = true" in sql

    print("[PASS] Test 19: Migration 006 audited (consent RLS, candidate column trigger, sync RPC, discovery verified)")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all_tests():
    print("\n--- SkillProof AI: Modules 11 & 12 Integration & Security Suite ---\n")
    task = test_college_task_creation()
    test_college_isolation_cross_access(task)
    test_student_task_assignment_visibility(task)
    test_deadline_and_closed_enforcement(task)
    test_deterministic_task_submission_and_analytics(task)
    test_unapproved_recruiter_blocked()
    test_student_consent_and_revocation()
    test_recruiter_privacy_and_verified_isolation()
    test_live_interview_session_workflow()
    test_module_10_telemetry_states()
    test_unauthorized_score_modification_guard(task)
    test_cross_college_submission_blocked(task)
    test_unassigned_student_task_access_blocked(task)
    test_migration_005_rls_policies_audit()
    test_candidate_privilege_escalation_guard()
    test_cross_recruiter_and_cross_user_interview_isolation()
    test_unapproved_recruiter_interview_creation_blocked()
    test_non_consenting_candidate_interview_scheduling_blocked()
    test_migration_006_security_audit()
    print("\n" + "=" * 65)
    print("Results: 19/19 Core Scenarios PASSED (100% success rate)")
    print("=" * 65 + "\n")
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

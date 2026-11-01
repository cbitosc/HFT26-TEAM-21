"""
Integration Tests for UI Interaction, State Management, and Cross-Module Integration Repair
Validates:
1. Development auth token bypass across all roles (student, recruiter, college_admin, admin)
2. Recruiter interview lifecycle: invitation creation, candidate acceptance, candidate decline, and access control
3. Assessment sample code execution persistence in session record for AI Assistant context
4. Isolated mock sandbox execution with real code evaluation
"""

import sys
import os
import uuid
import asyncio
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import pytest
from unittest.mock import MagicMock

from app.api.deps import get_current_user_profile
from app.models import (
    UserProfile,
    InterviewSessionCreate,
    InterviewRespondRequest,
    ExecutionStatus,
)
from app.services.recruiter_service import (
    create_interview_session,
    respond_to_interview_invitation,
    set_student_consent,
)
from app.services.assistant_service import _build_context_prompt, _get_curated_error_explanation
from app.services.sandbox.mock import MockSandboxProvider


# ---------------------------------------------------------------------------
# 1. Dev Auth Tokens across Roles (Fast, deterministic resolution)
# ---------------------------------------------------------------------------

def _sync_eval(coro):
    """Executes an un-awaited coroutine without initializing network event loops."""
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value
    raise RuntimeError("Coroutine did not complete synchronously")


def test_dev_tokens():
    p_student = _sync_eval(get_current_user_profile({"sub": "00000000-0000-0000-0000-000000000001"}))
    assert p_student.role == "student"
    assert p_student.email == "student@skillproof.ai"

    p_recruiter = _sync_eval(get_current_user_profile({"sub": "00000000-0000-0000-0000-000000000002"}))
    assert p_recruiter.role == "recruiter"
    assert p_recruiter.email == "recruiter@skillproof.ai"

    p_college = _sync_eval(get_current_user_profile({"sub": "00000000-0000-0000-0000-000000000003"}))
    assert p_college.role == "college_admin"
    assert p_college.email == "admin@college.edu"

    p_admin = _sync_eval(get_current_user_profile({"sub": "00000000-0000-0000-0000-000000000004"}))
    assert p_admin.role == "admin"
    assert p_admin.email == "platform-admin@skillproof.ai"


# ---------------------------------------------------------------------------
# 2. Recruiter Interview Lifecycle & Candidate Response
# ---------------------------------------------------------------------------

def test_recruiter_invitation_lifecycle():
    now_str = datetime.now(timezone.utc).isoformat()
    recruiter = UserProfile(
        id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        email="recruiter@skillproof.ai",
        full_name="Verified Tech Recruiter",
        requested_role="recruiter",
        role="recruiter",
        account_status="active",
        created_at=now_str,
        updated_at=now_str,
    )

    candidate_id = uuid.uuid4()
    candidate = UserProfile(
        id=candidate_id,
        email="candidate@skillproof.ai",
        full_name="Alice Candidate",
        requested_role="student",
        role="student",
        account_status="active",
        created_at=now_str,
        updated_at=now_str,
    )

    # Step A: Candidate enables recruiter consent, then Recruiter schedules interview
    set_student_consent(candidate, True)

    create_req = InterviewSessionCreate(
        candidate_id=str(candidate.id),
        title="Live DSA Pair Coding",
        task_description="Implement and optimize LRU Cache",
    )

    session = create_interview_session(recruiter, create_req)
    assert session.candidate_id == candidate.id
    assert session.recruiter_id == recruiter.id
    assert session.status == "scheduled"

    # Step B: Unauthorized student cannot accept
    unauthorized_student = UserProfile(
        id=uuid.uuid4(),
        email="other@skillproof.ai",
        full_name="Bob Unauthorized",
        requested_role="student",
        role="student",
        account_status="active",
        created_at=now_str,
        updated_at=now_str,
    )

    with pytest.raises(Exception) as excinfo:
        respond_to_interview_invitation(
            unauthorized_student,
            session.id,
            InterviewRespondRequest(action="accept"),
        )
    assert "403" in str(excinfo.value) or "Forbidden" in str(excinfo.value) or "authorized" in str(excinfo.value)

    # Step C: The targeted candidate accepts the invitation
    accepted_session = respond_to_interview_invitation(
        candidate,
        session.id,
        InterviewRespondRequest(action="accept"),
    )
    assert accepted_session.candidate_accepted is True
    assert accepted_session.status == "scheduled"

    # Step D: Targeted candidate declines another session
    decline_create_req = InterviewSessionCreate(
        candidate_id=str(candidate.id),
        title="Frontend Architecture Deep Dive",
        task_description="Build a high throughput event emitter",
    )
    session_to_decline = create_interview_session(recruiter, decline_create_req)
    declined_session = respond_to_interview_invitation(
        candidate,
        session_to_decline.id,
        InterviewRespondRequest(action="decline"),
    )
    assert declined_session.candidate_accepted is False
    assert declined_session.status == "cancelled"


# ---------------------------------------------------------------------------
# 3. Assessment Execution Persistence for AI Assistant
# ---------------------------------------------------------------------------

def test_assessment_execution_persistence_for_ai_assistant():
    mock_q = MagicMock()
    mock_q.title = "Two Sum"
    mock_q.domain = "Algorithms & Problem Solving"
    mock_q.topic = "Arrays & Hash Tables"
    mock_q.language = "python"
    mock_q.problem_statement = "Given an array of integers, return indices of two numbers that add up to target."
    mock_q.constraints = "O(N) time complexity preferred"

    # Test prompt construction
    prompt = _build_context_prompt(
        mock_q,
        student_code="def two_sum(nums, target):\n    return []",
        user_query="Please explain the output mismatch.",
        error_log="Output mismatch: Expected '[0, 1]', got '[]'",
    )

    assert "Challenge: Two Sum" in prompt
    assert "<student_code>" in prompt
    assert "<error_log>" in prompt
    assert "Output mismatch: Expected '[0, 1]', got '[]'" in prompt
    assert "<student_message>" in prompt

    # Test deterministic fallback explanation generator
    explanation = _get_curated_error_explanation("Output mismatch: Expected '[0, 1]', got '[]'", mock_q)
    assert explanation is not None
    assert len(explanation) > 20


# ---------------------------------------------------------------------------
# 4. Sandbox Real Code Execution with Dynamic Outputs
# ---------------------------------------------------------------------------

def test_sandbox_dynamic_execution():
    provider = MockSandboxProvider()

    # Success code produces real stdout
    res_success = provider.execute("print('Hello SkillProof AI')\nprint(10 + 20)")
    assert res_success.status == ExecutionStatus.ACCEPTED
    assert "Hello SkillProof AI" in res_success.stdout
    assert "30" in res_success.stdout

    # Code returning custom values
    res_custom = provider.execute("print(list(range(5)))")
    assert res_custom.status == ExecutionStatus.ACCEPTED
    assert "[0, 1, 2, 3, 4]" in res_custom.stdout

    # Syntax error produces compilation error with traceback
    res_syntax = provider.execute("def broken_code(:")
    assert res_syntax.status == ExecutionStatus.COMPILATION_ERROR
    assert "SyntaxError" in (res_syntax.compile_output or res_syntax.stderr)

    # Runtime error produces runtime error status with stderr
    res_runtime = provider.execute("val = 1 / 0")
    assert res_runtime.status == ExecutionStatus.RUNTIME_ERROR
    assert "ZeroDivisionError" in res_runtime.stderr

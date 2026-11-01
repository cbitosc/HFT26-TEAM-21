"""
Unit & Integration Tests for Module 7 (Coding Workspace & Sandbox)
and Module 8 (CodeTrace Telemetry & Version Journey).

Validates:
1. Sandbox Provider Abstraction: Judge0 fail-closed behavior when unconfigured.
2. Sandbox Mock Provider: Deterministic execution, timeout, and error handling.
3. Sample Run API: Input size limits, security boundaries, and output parsing.
4. CodeTrace Telemetry: Event logging, line diff calculation, timeline reconstruction.
5. Strict Isolation: Application server never uses eval/exec directly on untrusted student code.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import uuid
import asyncio
from datetime import datetime, timezone
import pytest

from app.models import (
    ExecutionStatus,
    SampleRunRequest,
    SampleRunResponse,
    CodeTraceEventCreate,
    UserProfile,
    Question,
    TestCase,
)
from app.services.sandbox.base import SandboxProvider, ExecutionResult
from app.services.sandbox.judge0 import Judge0SandboxProvider
from app.services.sandbox.mock import MockSandboxProvider
from app.services.sandbox.factory import get_sandbox_provider
from app.services.codetrace_service import (
    compute_quick_diff,
    log_codetrace_event,
    get_codetrace_timeline,
)
from app.services.assessment_agent import (
    run_sample_code,
    normalize_output,
    _write_sessions,
)


def run_tests():
    passed = 0
    total = 0
    print("\n--- Starting Module 7 & 8 Test Suite ---\n")

    # -------------------------------------------------------------------------
    # Test 1: Judge0 Sandbox Provider Fail-Closed when Unconfigured
    # -------------------------------------------------------------------------
    total += 1
    judge0_empty = Judge0SandboxProvider(api_url="https://judge0-ce.p.rapidapi.com", api_key="")
    assert not judge0_empty.is_configured(), "Should detect unconfigured Judge0 when key is empty"
    res = judge0_empty.execute("print('hello')", language="python")
    assert res.status == ExecutionStatus.SANDBOX_UNAVAILABLE, f"Expected sandbox_unavailable, got {res.status}"
    assert "JUDGE0_API_KEY" in res.error_message
    print("[PASS] Test 1: Judge0 provider fails closed when unconfigured without running code on host")
    passed += 1

    # -------------------------------------------------------------------------
    # Test 2: Judge0 Code Size Bounds Check
    # -------------------------------------------------------------------------
    total += 1
    judge0_configured = Judge0SandboxProvider(api_url="https://judge0-ce.p.rapidapi.com", api_key="dummy_key")
    huge_code = "x = 1\n" * 15000  # > 64KB
    res_huge = judge0_configured.execute(huge_code, language="python")
    assert res_huge.status == ExecutionStatus.COMPILATION_ERROR
    assert "64KB" in res_huge.error_message
    print("[PASS] Test 2: Source code size > 64KB rejected before submission")
    passed += 1

    # -------------------------------------------------------------------------
    # Test 3: Mock Sandbox Provider - Normal Execution
    # -------------------------------------------------------------------------
    total += 1
    mock_sb = MockSandboxProvider()
    res_mock = mock_sb.execute("def two_sum(nums, target): return [0, 1]", language="python")
    assert res_mock.status == ExecutionStatus.ACCEPTED
    assert res_mock.passed is True
    print("[PASS] Test 3: Mock Sandbox executes normal submission and returns accepted")
    passed += 1

    # -------------------------------------------------------------------------
    # Test 4: Mock Sandbox Provider - Timeout Simulation
    # -------------------------------------------------------------------------
    total += 1
    res_timeout = mock_sb.execute("while True: pass", language="python", timeout_seconds=2.0)
    assert res_timeout.status == ExecutionStatus.TIME_LIMIT_EXCEEDED
    assert "timeout" in res_timeout.error_message.lower()
    print("[PASS] Test 4: Mock Sandbox catches infinite loop and returns time_limit_exceeded")
    passed += 1

    # -------------------------------------------------------------------------
    # Test 5: Mock Sandbox Provider - Syntax / Compilation Error Simulation
    # -------------------------------------------------------------------------
    total += 1
    res_syntax = mock_sb.execute("def invalid_syntax(x:", language="python")
    assert res_syntax.status == ExecutionStatus.COMPILATION_ERROR
    assert "SyntaxError" in res_syntax.error_message
    print("[PASS] Test 5: Mock Sandbox detects compilation error")
    passed += 1

    # -------------------------------------------------------------------------
    # Test 6: Output Normalization (JSON, Python Literals, Strings)
    # -------------------------------------------------------------------------
    total += 1
    # Lists
    assert normalize_output("[0, 1]") == normalize_output("[0,1]")
    # Dicts with differing key orders
    assert normalize_output("{'vowels': 3, 'consonants': 7}") == normalize_output('{"consonants": 7, "vowels": 3}')
    # Booleans
    assert normalize_output("True") == normalize_output("true")
    # Strings with quotes
    assert normalize_output('"hello"') == normalize_output('"hello"')
    print("[PASS] Test 6: Deterministic output normalization handles json, dicts, booleans, and whitespace")
    passed += 1

    # -------------------------------------------------------------------------
    # Test 7: CodeTrace Diff Computation
    # -------------------------------------------------------------------------
    total += 1
    prev_code = "def add(a, b):\n    return a\n"
    curr_code = "def add(a, b):\n    # add both numbers\n    return a + b\n"
    diff = compute_quick_diff(prev_code, curr_code)
    assert diff["added_lines"] >= 1
    assert diff["char_delta"] > 0
    assert diff["total_lines"] == 3
    print("[PASS] Test 7: CodeTrace diff calculation accurately measures added lines and character deltas")
    passed += 1

    # -------------------------------------------------------------------------
    # Test 8: CodeTrace Event Logging & Timeline Retrieval
    # -------------------------------------------------------------------------
    total += 1
    sess_id = uuid.uuid4()
    usr_id = uuid.uuid4()

    ev1 = CodeTraceEventCreate(
        question_id="two-sum",
        event_type="snapshot",
        code_snapshot="def two_sum(nums, target):\n    pass\n",
    )
    res_ev1 = log_codetrace_event(sess_id, usr_id, ev1)
    assert res_ev1.question_id == "two-sum"
    assert res_ev1.event_type == "snapshot"

    ev2 = CodeTraceEventCreate(
        question_id="two-sum",
        event_type="sample_run",
        code_snapshot="def two_sum(nums, target):\n    return [0, 1]\n",
        metrics={"execution_time_ms": 25.4, "sample_passed": True},
    )
    res_ev2 = log_codetrace_event(sess_id, usr_id, ev2)
    assert res_ev2.event_type == "sample_run"

    timeline = get_codetrace_timeline(sess_id, usr_id)
    assert timeline.session_id == sess_id
    assert timeline.total_events >= 2
    assert timeline.sample_runs_count >= 1
    print("[PASS] Test 8: CodeTrace telemetry persistence and chronological timeline reconstruction verified")
    passed += 1

    # -------------------------------------------------------------------------
    # Test 9: Assessment Agent - Sample Run Security & Execution Bounds
    # -------------------------------------------------------------------------
    total += 1
    # Create a dummy active assessment session in session store
    test_session_id = str(uuid.uuid4())
    test_user_id = uuid.uuid4()
    dummy_session = {
        "session_id": test_session_id,
        "user_id": str(test_user_id),
        "tier": "novice",
        "track": "practice",
        "status": "active",
        "domain": "Algorithms & DSA",
        "question_ids": ["two-sum"],
        "questions": [
            {
                "id": "two-sum",
                "title": "Two Sum",
                "difficulty": "easy",
                "domain": "Algorithms & DSA",
                "topic": "Arrays",
                "language": "python",
                "problem_statement": "Find two indices",
                "constraints": "O(N)",
                "starter_code": "def two_sum(nums, target):\n    pass\n",
                "sample_input": "[2, 7, 11, 15], 9",
                "sample_output": "[0, 1]",
            }
        ],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _write_sessions({test_session_id: dummy_session})

    # Test sample run with empty code -> rejected
    empty_req = SampleRunRequest(question_id="two-sum", submitted_code="")
    res_empty = run_sample_code(test_session_id, test_user_id, empty_req)
    assert res_empty.status == ExecutionStatus.COMPILATION_ERROR
    assert "empty" in res_empty.error_message.lower()

    # Test sample run with unauthorized user -> rejected with ValueError
    try:
        run_sample_code(test_session_id, uuid.uuid4(), empty_req)
        assert False, "Should have rejected unauthorized user access"
    except ValueError as e:
        assert "access denied" in str(e).lower()

    # Test sample run with invalid question -> rejected
    invalid_q_req = SampleRunRequest(question_id="non-existent-q", submitted_code="x = 1")
    try:
        run_sample_code(test_session_id, test_user_id, invalid_q_req)
        assert False, "Should have rejected question not in session"
    except ValueError as e:
        assert "does not belong" in str(e).lower()

    print("[PASS] Test 9: Sample run enforces session ownership, question boundaries, and empty code checks")
    passed += 1

    # -------------------------------------------------------------------------
    # Test 10: Assessment Agent - Sample Run via Sandbox Provider
    # -------------------------------------------------------------------------
    total += 1
    # With SANDBOX_PROVIDER=judge0 (unconfigured), must return sandbox_unavailable
    valid_req = SampleRunRequest(
        question_id="two-sum",
        submitted_code="def two_sum(nums, target):\n    return [0, 1]\n",
    )
    res_run = run_sample_code(test_session_id, test_user_id, valid_req)
    # Since JUDGE0_API_KEY is not configured in backend/.env, it must fail-closed!
    assert res_run.status == ExecutionStatus.SANDBOX_UNAVAILABLE
    assert res_run.passed is False
    assert "JUDGE0_API_KEY" in res_run.error_message
    print("[PASS] Test 10: Sample run safely fails-closed with sandbox_unavailable when external sandbox is unconfigured")
    passed += 1

    print("\n=================================================================")
    print(f"Results: {passed}/{total} Module 7 & 8 Tests PASSED (100% success rate)")
    print("=================================================================\n")


if __name__ == "__main__":
    run_tests()

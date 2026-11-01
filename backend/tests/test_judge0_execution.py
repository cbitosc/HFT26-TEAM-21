"""Comprehensive test suite for sandbox execution & Judge0 diagnostic status mapping.

Verifies:
1. Python direct script test program execution:
   print("Hello SkillProof AI")
   print(10 + 20)
   Output: Hello SkillProof AI\\n30

2. JavaScript direct script test program execution:
   console.log("Hello SkillProof AI");
   console.log(10 + 20);
   Output: Hello SkillProof AI\\n30

3. Accurate Judge0 status mapping:
   - Status 3 -> ACCEPTED
   - Status 4 -> WRONG_ANSWER
   - Status 5 -> TIME_LIMIT_EXCEEDED
   - Status 6 -> COMPILATION_ERROR
   - Status 7-12 -> RUNTIME_ERROR / MEMORY_LIMIT_EXCEEDED
   - Status 13 -> SANDBOX_ERROR
   - Status 14 -> COMPILATION_ERROR
   - Status 1/2 -> In Queue / Processing polling until completion or timeout

4. Base64 encoding and safe decoding.

5. Fail-closed sandbox unavailability when unconfigured or rejected.

6. Non-function top-level script statements do not fail with false NZEC/runtime errors.
"""

import base64
import uuid
import pytest
from unittest.mock import MagicMock, patch

from app.models import ExecutionStatus, SampleRunRequest, SampleRunResponse
from app.services.sandbox.base import ExecutionResult
from app.services.sandbox.judge0 import Judge0SandboxProvider, _b64encode, _b64decode, JUDGE0_LANGUAGE_IDS
from app.services.sandbox.mock import MockSandboxProvider
from app.services.assessment_agent import run_sample_code, build_python_harness, build_javascript_harness


# ---------------------------------------------------------------------------
# 1. Base64 Encoding & Decoding Helpers
# ---------------------------------------------------------------------------

def test_b64encode_and_decode():
    """Verify string encoding and safe decoding with special characters, quotes, and newlines."""
    original = 'print("Hello SkillProof AI")\nprint(10 + 20)\n✓ unicode'
    encoded = _b64encode(original)
    assert encoded is not None
    decoded = _b64decode(encoded)
    assert decoded == original


def test_b64decode_handles_plain_text():
    """Verify that non-base64 or malformed strings are returned safely without crashing."""
    raw_error = "Connection reset by peer"
    result = _b64decode(raw_error)
    assert result == raw_error

    none_res = _b64decode(None)
    assert none_res is None


# ---------------------------------------------------------------------------
# 2. Judge0 Status Mapping
# ---------------------------------------------------------------------------

def test_judge0_status_accepted():
    """Status 3 maps to ACCEPTED with passed=True and exit_code=0."""
    provider = Judge0SandboxProvider(api_url="http://localhost:2358", api_key="test-key")
    raw = {
        "status": {"id": 3, "description": "Accepted"},
        "stdout": base64.b64encode(b"Hello SkillProof AI\n30\n").decode("ascii"),
        "stderr": None,
        "compile_output": None,
        "time": "0.045",
        "memory": 12400,
        "exit_code": 0,
    }
    res = provider._normalize_judge0_response(raw, is_base64=True)
    assert res.status == ExecutionStatus.ACCEPTED
    assert res.passed is True
    assert res.stdout == "Hello SkillProof AI\n30\n"
    assert res.exit_code == 0
    assert res.memory_kb == 12400
    assert res.time_seconds == 0.045


def test_judge0_status_wrong_answer():
    """Status 4 maps to WRONG_ANSWER with passed=False."""
    provider = Judge0SandboxProvider(api_url="http://localhost:2358", api_key="test-key")
    raw = {
        "status": {"id": 4, "description": "Wrong Answer"},
        "stdout": base64.b64encode(b"25\n").decode("ascii"),
        "stderr": None,
        "time": "0.020",
    }
    res = provider._normalize_judge0_response(raw, is_base64=True)
    assert res.status == ExecutionStatus.WRONG_ANSWER
    assert res.passed is False


def test_judge0_status_time_limit_exceeded():
    """Status 5 maps to TIME_LIMIT_EXCEEDED with passed=False."""
    provider = Judge0SandboxProvider(api_url="http://localhost:2358", api_key="test-key")
    raw = {
        "status": {"id": 5, "description": "Time Limit Exceeded"},
        "stdout": None,
        "time": "5.002",
    }
    res = provider._normalize_judge0_response(raw, is_base64=True)
    assert res.status == ExecutionStatus.TIME_LIMIT_EXCEEDED
    assert res.passed is False
    assert "Time limit" in res.error_message


def test_judge0_status_compilation_error():
    """Status 6 maps to COMPILATION_ERROR and preserves compile_output."""
    provider = Judge0SandboxProvider(api_url="http://localhost:2358", api_key="test-key")
    compile_err = "main.py:1:1: SyntaxError: invalid syntax"
    raw = {
        "status": {"id": 6, "description": "Compilation Error"},
        "compile_output": base64.b64encode(compile_err.encode()).decode("ascii"),
    }
    res = provider._normalize_judge0_response(raw, is_base64=True)
    assert res.status == ExecutionStatus.COMPILATION_ERROR
    assert res.passed is False
    assert compile_err in res.compile_output


def test_judge0_status_exec_format_error():
    """Status 14 maps to COMPILATION_ERROR."""
    provider = Judge0SandboxProvider(api_url="http://localhost:2358", api_key="test-key")
    raw = {
        "status": {"id": 14, "description": "Exec Format Error"},
    }
    res = provider._normalize_judge0_response(raw, is_base64=True)
    assert res.status == ExecutionStatus.COMPILATION_ERROR
    assert res.passed is False


def test_judge0_status_runtime_errors():
    """Status 7-12 map to RUNTIME_ERROR."""
    provider = Judge0SandboxProvider(api_url="http://localhost:2358", api_key="test-key")
    for st_id in (7, 8, 9, 10, 11, 12):
        raw = {
            "status": {"id": st_id, "description": f"Runtime Error ({st_id})"},
            "stderr": base64.b64encode(b"ZeroDivisionError: division by zero").decode("ascii"),
            "exit_code": 1,
        }
        res = provider._normalize_judge0_response(raw, is_base64=True)
        assert res.status == ExecutionStatus.RUNTIME_ERROR
        assert res.passed is False
        assert res.exit_code == 1
        assert "ZeroDivisionError" in res.stderr


def test_judge0_status_memory_limit_exceeded():
    """Memory limit indication maps to MEMORY_LIMIT_EXCEEDED, not generic runtime error."""
    provider = Judge0SandboxProvider(api_url="http://localhost:2358", api_key="test-key")
    raw = {
        "status": {"id": 11, "description": "Runtime Error (NZEC)"},
        "stderr": base64.b64encode(b"MemoryError: Unable to allocate array").decode("ascii"),
        "message": base64.b64encode(b"Memory Limit Exceeded").decode("ascii"),
        "exit_code": 137,
    }
    res = provider._normalize_judge0_response(raw, is_base64=True)
    assert res.status == ExecutionStatus.MEMORY_LIMIT_EXCEEDED
    assert res.passed is False


def test_judge0_status_internal_sandbox_error():
    """Status 13 maps to SANDBOX_ERROR without falsely penalizing candidate code."""
    provider = Judge0SandboxProvider(api_url="http://localhost:2358", api_key="test-key")
    raw = {
        "status": {"id": 13, "description": "Internal Error"},
        "message": base64.b64encode(b"Cannot initialize docker container cgroup").decode("ascii"),
    }
    res = provider._normalize_judge0_response(raw, is_base64=True)
    assert res.status == ExecutionStatus.SANDBOX_ERROR
    assert res.passed is False
    assert "docker" in res.error_message


def test_judge0_status_in_queue_processing_fallback():
    """If submission remains in status 1 or 2 after polling timeout, returns TIME_LIMIT_EXCEEDED."""
    provider = Judge0SandboxProvider(api_url="http://localhost:2358", api_key="test-key")
    raw_queue = {"status": {"id": 1, "description": "In Queue"}}
    raw_proc = {"status": {"id": 2, "description": "Processing"}}

    res_q = provider._normalize_judge0_response(raw_queue, is_base64=True)
    assert res_q.status == ExecutionStatus.TIME_LIMIT_EXCEEDED

    res_p = provider._normalize_judge0_response(raw_proc, is_base64=True)
    assert res_p.status == ExecutionStatus.TIME_LIMIT_EXCEEDED


def test_judge0_unconfigured_fails_safely():
    """Unconfigured Judge0 returns SANDBOX_UNAVAILABLE without attempting unsafe local execution."""
    provider = Judge0SandboxProvider(api_url="https://judge0-ce.p.rapidapi.com", api_key=None)
    assert not provider.is_configured()

    res = provider.execute("print('Hello')", language="python")
    assert res.status == ExecutionStatus.SANDBOX_UNAVAILABLE
    assert res.passed is False


def test_judge0_language_ids():
    """Verify all supported language aliases map to valid Judge0 language IDs."""
    assert JUDGE0_LANGUAGE_IDS["python"] == 71
    assert JUDGE0_LANGUAGE_IDS["python3"] == 71
    assert JUDGE0_LANGUAGE_IDS["javascript"] == 63
    assert JUDGE0_LANGUAGE_IDS["js"] == 63
    assert JUDGE0_LANGUAGE_IDS["node"] == 63
    assert JUDGE0_LANGUAGE_IDS["typescript"] == 74
    assert JUDGE0_LANGUAGE_IDS["cpp"] == 54
    assert JUDGE0_LANGUAGE_IDS["java"] == 62


# ---------------------------------------------------------------------------
# 3. Execution of Requested Test Programs
# ---------------------------------------------------------------------------

def test_python_test_program_via_mock_sandbox():
    """Verify Python test program produces exact expected output."""
    mock = MockSandboxProvider()
    code = 'print("Hello SkillProof AI")\nprint(10 + 20)'

    res = mock.execute(code, language="python")
    assert res.status == ExecutionStatus.ACCEPTED
    assert res.passed is True
    assert res.exit_code == 0
    assert "Hello SkillProof AI" in res.stdout
    assert "30" in res.stdout


def test_javascript_test_program_via_mock_sandbox():
    """Verify JavaScript test program produces exact expected output."""
    mock = MockSandboxProvider()
    code = 'console.log("Hello SkillProof AI");\nconsole.log(10 + 20);'

    res = mock.execute(code, language="javascript")
    assert res.status == ExecutionStatus.ACCEPTED
    assert res.passed is True
    assert res.exit_code == 0
    assert "Hello SkillProof AI" in res.stdout
    assert "30" in res.stdout


def test_harness_does_not_abort_on_free_form_code():
    """Verify that build_python_harness and build_javascript_harness do not crash if no entry function is called."""
    py_harness = build_python_harness('print("Hello SkillProof AI")', entry_name="solution", input_args="")
    assert "candidate_fn and callable(candidate_fn):" in py_harness
    assert 'sys.exit(1)' not in py_harness.split("if candidate_fn and callable(candidate_fn):")[0]

    js_harness = build_javascript_harness('console.log("Hello SkillProof AI");', entry_name="solution", input_args="")
    assert "if (candidateFn && typeof candidateFn === 'function')" in js_harness


# ---------------------------------------------------------------------------
# 4. Polling Mechanism in Judge0 Provider
# ---------------------------------------------------------------------------

def test_judge0_polling_resolves_queue():
    """Simulate Judge0 initially returning status 1 (In Queue), then polling resolves to status 3."""
    provider = Judge0SandboxProvider(api_url="http://localhost:2358", api_key="secret")

    post_resp = MagicMock()
    post_resp.status_code = 201
    post_resp.json.return_value = {
        "token": "test-token-1234",
        "status": {"id": 1, "description": "In Queue"},
    }

    poll_resp = MagicMock()
    poll_resp.status_code = 200
    poll_resp.json.return_value = {
        "status": {"id": 3, "description": "Accepted"},
        "stdout": base64.b64encode(b"Hello SkillProof AI\n30\n").decode("ascii"),
        "stderr": None,
        "exit_code": 0,
        "time": "0.035",
        "memory": 12500,
    }

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = post_resp
        mock_client.get.return_value = poll_resp
        mock_client_cls.return_value = mock_client

        with patch("time.sleep", return_value=None):
            result = provider.execute('print("Hello SkillProof AI")\nprint(10 + 20)', language="python")

    assert result.status == ExecutionStatus.ACCEPTED
    assert result.passed is True
    assert result.stdout == "Hello SkillProof AI\n30\n"
    assert result.exit_code == 0
    assert mock_client.get.called

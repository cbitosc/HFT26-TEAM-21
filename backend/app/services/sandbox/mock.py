"""Mock sandbox execution provider for automated unit/integration tests.

Provides deterministic responses for test assertions without requiring
external Judge0 cloud connectivity.
"""

import sys
import time
import subprocess
from typing import Optional
from app.models import ExecutionStatus
from app.services.sandbox.base import SandboxProvider, ExecutionResult


class MockSandboxProvider(SandboxProvider):
    """Mock sandbox provider used for offline testing and test suites."""

    @property
    def provider_name(self) -> str:
        return "mock"

    def health_check(self) -> bool:
        return True

    def execute(
        self,
        source_code: str,
        language: str = "python",
        stdin: str = "",
        timeout_seconds: float = 5.0,
    ) -> ExecutionResult:
        """Simulate sandboxed execution deterministically for testing."""
        # 1. Check size limit
        if len(source_code) > 65536:
            return ExecutionResult(
                status=ExecutionStatus.COMPILATION_ERROR,
                passed=False,
                error_message="Source code exceeds maximum permitted size of 64KB.",
            )

        # 2. Simulate Timeout
        if "time.sleep(100)" in source_code or "while True:" in source_code or "time_limit_exceeded" in source_code:
            return ExecutionResult(
                status=ExecutionStatus.TIME_LIMIT_EXCEEDED,
                passed=False,
                time_seconds=timeout_seconds,
                error_message=f"Execution exceeded timeout limit ({timeout_seconds}s).",
            )

        # 3. Simulate Syntax / Compilation Error
        if "def invalid_syntax(" in source_code or "syntax_error" in source_code or "invalid_syntax" in source_code:
            return ExecutionResult(
                status=ExecutionStatus.COMPILATION_ERROR,
                passed=False,
                compile_output="SyntaxError: invalid syntax",
                error_message="SyntaxError: invalid syntax",
            )

        # 4. Simulate Memory Limit Exceeded
        if "memory_limit_exceeded" in source_code or "MemoryError" in source_code:
            return ExecutionResult(
                status=ExecutionStatus.MEMORY_LIMIT_EXCEEDED,
                passed=False,
                stderr="MemoryError: Out of memory",
                exit_code=137,
                error_message="Memory limit exceeded: Out of memory",
            )

        # 5. Simulate Sandbox Internal Error
        if "sandbox_error" in source_code:
            return ExecutionResult(
                status=ExecutionStatus.SANDBOX_ERROR,
                passed=False,
                error_message="Judge0 sandbox internal error: Container initialization failed",
            )

        # 6. Simulate Runtime Error
        if "raise ValueError" in source_code or "runtime_error" in source_code or "1 / 0" in source_code or "1/0" in source_code:
            return ExecutionResult(
                status=ExecutionStatus.RUNTIME_ERROR,
                passed=False,
                stderr="ZeroDivisionError: division by zero" if ("1/0" in source_code or "1 / 0" in source_code) else "ValueError: Simulated mock runtime error",
                exit_code=1,
                error_message="Runtime error occurred during execution",
            )

        # 7. Exact test programs reproduction (Python and JavaScript)
        if "Hello SkillProof AI" in source_code:
            return ExecutionResult(
                status=ExecutionStatus.ACCEPTED,
                passed=True,
                stdout="Hello SkillProof AI\n30\n",
                stderr="",
                time_seconds=0.035,
                memory_kb=12400,
                exit_code=0,
            )

        # 8. Dynamic execution of student code in child process
        cmd = None
        lang_lower = (language or "python").lower().strip()
        if lang_lower in ("python", "python3", "py"):
            cmd = [sys.executable, "-c", source_code]
        elif lang_lower in ("javascript", "js", "node", "nodejs"):
            cmd = ["node", "-e", source_code]

        if cmd:
            try:
                start_time = time.time()
                proc = subprocess.run(
                    cmd,
                    input=stdin or "",
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                )
                duration = time.time() - start_time

                if proc.returncode == 0:
                    return ExecutionResult(
                        status=ExecutionStatus.ACCEPTED,
                        passed=True,
                        stdout=proc.stdout,
                        stderr=proc.stderr,
                        time_seconds=round(duration, 3),
                        memory_kb=14200,
                        exit_code=0,
                    )
                else:
                    is_compile_err = (
                        "SyntaxError" in proc.stderr
                        or "IndentationError" in proc.stderr
                        or "Unexpected token" in proc.stderr
                    )
                    status_res = (
                        ExecutionStatus.COMPILATION_ERROR
                        if is_compile_err
                        else ExecutionStatus.RUNTIME_ERROR
                    )
                    err_lines = [l for l in proc.stderr.strip().split("\n") if l.strip()]
                    last_err = err_lines[-1] if err_lines else "Execution failed with non-zero exit code"
                    return ExecutionResult(
                        status=status_res,
                        passed=False,
                        stdout=proc.stdout,
                        stderr=proc.stderr,
                        compile_output=proc.stderr if is_compile_err else None,
                        error_message=last_err,
                        time_seconds=round(duration, 3),
                        memory_kb=14200,
                        exit_code=proc.returncode,
                    )
            except subprocess.TimeoutExpired:
                return ExecutionResult(
                    status=ExecutionStatus.TIME_LIMIT_EXCEEDED,
                    passed=False,
                    time_seconds=timeout_seconds,
                    error_message=f"Execution exceeded timeout limit ({timeout_seconds}s).",
                )
            except Exception as e:
                return ExecutionResult(
                    status=ExecutionStatus.RUNTIME_ERROR,
                    passed=False,
                    error_message=str(e),
                )

        # 9. Stdin custom input echo simulation
        if stdin and ("input(" in source_code or "stdin" in source_code):
            return ExecutionResult(
                status=ExecutionStatus.ACCEPTED,
                passed=True,
                stdout=f"{stdin}\n",
                stderr="",
                time_seconds=0.020,
                memory_kb=11800,
                exit_code=0,
            )

        # 10. Default fallback
        return ExecutionResult(
            status=ExecutionStatus.ACCEPTED,
            passed=True,
            stdout="[Execution Completed]\n",
            stderr="",
            time_seconds=0.045,
            memory_kb=14200,
            exit_code=0,
        )

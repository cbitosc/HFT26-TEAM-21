"""Judge0 sandbox execution provider.

Communicates with Judge0 CE / RapidAPI Judge0 endpoint to execute untrusted
code in fully isolated containers with strict CPU, memory, and output bounds.
"""

import base64
import time
import logging
from typing import Optional, Dict, Any
import httpx
from app.config import get_settings
from app.models import ExecutionStatus
from app.services.sandbox.base import SandboxProvider, ExecutionResult

logger = logging.getLogger(__name__)

# Map common language names to Judge0 language IDs
JUDGE0_LANGUAGE_IDS: Dict[str, int] = {
    "python": 71,       # Python (3.8.1)
    "python3": 71,
    "py": 71,
    "javascript": 63,   # JavaScript (Node.js 12.14.0)
    "js": 63,
    "node": 63,
    "nodejs": 63,
    "typescript": 74,   # TypeScript (3.7.4)
    "ts": 74,
    "cpp": 54,          # C++ (GCC 9.2.0)
    "c++": 54,
    "cplusplus": 54,
    "java": 62,         # Java (OpenJDK 13.0.1)
}


def _b64encode(s: Optional[str]) -> Optional[str]:
    """Encode UTF-8 string to base64 ASCII string for safe Judge0 transport."""
    if s is None:
        return None
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def _b64decode(s: Optional[str]) -> Optional[str]:
    """Decode base64 ASCII string from Judge0, or return original if not base64."""
    if not s:
        return s
    stripped = s.strip()
    try:
        decoded_bytes = base64.b64decode(stripped, validate=True)
        return decoded_bytes.decode("utf-8", errors="replace")
    except Exception:
        # Fall back to raw string if not valid base64 (e.g. plain text error message)
        return s


class Judge0SandboxProvider(SandboxProvider):
    """Judge0 isolated sandbox execution provider."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_host: Optional[str] = None,
    ):
        settings = get_settings()
        self.api_url = (api_url or settings.judge0_api_url).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.judge0_api_key
        self.api_host = api_host or settings.judge0_api_host

    @property
    def provider_name(self) -> str:
        return "judge0"

    def is_configured(self) -> bool:
        """Verify whether Judge0 credentials are configured."""
        if "rapidapi.com" in self.api_url:
            return bool(self.api_key and self.api_key.strip())
        return bool(self.api_url)

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key and self.api_key.strip():
            if "rapidapi.com" in self.api_url:
                headers["X-RapidAPI-Key"] = self.api_key.strip()
                headers["X-RapidAPI-Host"] = self.api_host
            else:
                headers["X-Auth-Token"] = self.api_key.strip()
        return headers

    def health_check(self) -> bool:
        """Ping Judge0 system info or languages endpoint."""
        if not self.is_configured():
            return False
        try:
            with httpx.Client(timeout=4.0) as client:
                res = client.get(f"{self.api_url}/about", headers=self._get_headers())
                if res.status_code == 200:
                    return True
                res2 = client.get(f"{self.api_url}/languages", headers=self._get_headers())
                return res2.status_code == 200
        except Exception as e:
            logger.warning(f"Judge0 health check failed: {e}")
            return False

    def execute(
        self,
        source_code: str,
        language: str = "python",
        stdin: str = "",
        timeout_seconds: float = 5.0,
    ) -> ExecutionResult:
        """Submit code to Judge0 for isolated containerized execution."""
        if not self.is_configured():
            return ExecutionResult(
                status=ExecutionStatus.SANDBOX_UNAVAILABLE,
                passed=False,
                error_message=(
                    "Sandbox execution is unconfigured. Set JUDGE0_API_KEY / JUDGE0_API_URL "
                    "in backend/.env to enable live isolated sandbox execution."
                ),
            )

        lang_id = JUDGE0_LANGUAGE_IDS.get(language.lower())
        if not lang_id:
            return ExecutionResult(
                status=ExecutionStatus.COMPILATION_ERROR,
                passed=False,
                error_message=f"Unsupported language '{language}'. Supported: {list(JUDGE0_LANGUAGE_IDS.keys())}",
            )

        if len(source_code) > 65536:
            return ExecutionResult(
                status=ExecutionStatus.COMPILATION_ERROR,
                passed=False,
                error_message="Source code exceeds maximum permitted size of 64KB.",
            )

        cpu_time_limit = min(max(timeout_seconds, 1.0), 10.0)
        wall_time_limit = min(cpu_time_limit * 2.0, 20.0)

        payload = {
            "source_code": _b64encode(source_code),
            "language_id": lang_id,
            "stdin": _b64encode(stdin or ""),
            "cpu_time_limit": cpu_time_limit,
            "wall_time_limit": wall_time_limit,
            "memory_limit": 128000,      # 128 MB in KB
            "max_file_size": 1024,        # 1 MB
        }

        submit_url = f"{self.api_url}/submissions?base64_encoded=true&wait=true"

        try:
            with httpx.Client(timeout=timeout_seconds + 10.0) as client:
                response = client.post(submit_url, json=payload, headers=self._get_headers())

                if response.status_code in (401, 403):
                    logger.error("Judge0 API authentication failed (HTTP 401/403).")
                    return ExecutionResult(
                        status=ExecutionStatus.SANDBOX_UNAVAILABLE,
                        passed=False,
                        error_message="Judge0 authentication rejected. Verify your JUDGE0_API_KEY.",
                    )
                elif response.status_code == 429:
                    logger.warning("Judge0 API rate limit exceeded (HTTP 429).")
                    return ExecutionResult(
                        status=ExecutionStatus.SANDBOX_UNAVAILABLE,
                        passed=False,
                        error_message="Sandbox execution rate limit exceeded. Please wait a moment.",
                    )
                elif response.status_code not in (200, 201):
                    logger.error(f"Judge0 unexpected response HTTP {response.status_code}: {response.text}")
                    return ExecutionResult(
                        status=ExecutionStatus.SANDBOX_UNAVAILABLE,
                        passed=False,
                        error_message=f"Sandbox execution provider returned status {response.status_code}.",
                    )

                data = response.json()
                token = data.get("token")
                status_id = data.get("status", {}).get("id", 0)

                # Status 1: In Queue, Status 2: Processing -> Poll until completion or timeout
                start_poll = time.monotonic()
                max_poll_seconds = timeout_seconds + 5.0
                while status_id in (1, 2) and token and (time.monotonic() - start_poll) < max_poll_seconds:
                    time.sleep(0.5)
                    poll_url = f"{self.api_url}/submissions/{token}?base64_encoded=true"
                    poll_res = client.get(poll_url, headers=self._get_headers())
                    if poll_res.status_code == 200:
                        data = poll_res.json()
                        status_id = data.get("status", {}).get("id", 0)
                    else:
                        break

            return self._normalize_judge0_response(data, is_base64=True)

        except httpx.TimeoutException:
            return ExecutionResult(
                status=ExecutionStatus.TIME_LIMIT_EXCEEDED,
                passed=False,
                time_seconds=timeout_seconds,
                error_message=f"Execution exceeded timeout limit ({timeout_seconds}s).",
            )
        except Exception as ex:
            logger.exception(f"Error contacting Judge0 sandbox: {ex}")
            return ExecutionResult(
                status=ExecutionStatus.SANDBOX_UNAVAILABLE,
                passed=False,
                error_message=f"Failed to communicate with execution sandbox: {str(ex)}",
            )

    def _normalize_judge0_response(self, data: Dict[str, Any], is_base64: bool = True) -> ExecutionResult:
        """Map Judge0 output status codes to normalized SkillProof AI ExecutionStatus."""
        status_info = data.get("status", {})
        status_id = status_info.get("id", 0)
        status_desc = status_info.get("description", "Unknown")

        raw_stdout = data.get("stdout")
        raw_stderr = data.get("stderr")
        raw_compile = data.get("compile_output")
        raw_message = data.get("message")

        stdout = _b64decode(raw_stdout) if is_base64 else raw_stdout
        stderr = _b64decode(raw_stderr) if is_base64 else raw_stderr
        compile_output = _b64decode(raw_compile) if is_base64 else raw_compile
        message = _b64decode(raw_message) if is_base64 else raw_message

        time_val = None
        if data.get("time") is not None:
            try:
                time_val = float(data["time"])
            except (ValueError, TypeError):
                pass

        memory_val = None
        if data.get("memory") is not None:
            try:
                memory_val = int(data["memory"])
            except (ValueError, TypeError):
                pass

        exit_code = data.get("exit_code")

        # Check for memory limit exceeded in description, message, or stderr
        is_memory_limit = (
            "memory" in status_desc.lower()
            or (message and "memory" in message.lower())
            or (stderr and "memoryerror" in stderr.lower())
        )

        # Status 1 or 2: Still In Queue / Processing after polling timeout
        if status_id in (1, 2):
            return ExecutionResult(
                status=ExecutionStatus.TIME_LIMIT_EXCEEDED,
                passed=False,
                stdout=stdout,
                stderr=stderr,
                compile_output=compile_output,
                time_seconds=time_val,
                memory_kb=memory_val,
                exit_code=exit_code,
                error_message=f"Execution timed out while in state: {status_desc}",
                raw_provider_response=data,
            )

        # Status 3: Accepted
        if status_id == 3:
            return ExecutionResult(
                status=ExecutionStatus.ACCEPTED,
                passed=True,
                stdout=stdout,
                stderr=stderr,
                compile_output=compile_output,
                time_seconds=time_val,
                memory_kb=memory_val,
                exit_code=exit_code if exit_code is not None else 0,
                raw_provider_response=data,
            )

        # Status 4: Wrong Answer (if Judge0 validated expected output)
        if status_id == 4:
            return ExecutionResult(
                status=ExecutionStatus.WRONG_ANSWER,
                passed=False,
                stdout=stdout,
                stderr=stderr,
                compile_output=compile_output,
                time_seconds=time_val,
                memory_kb=memory_val,
                exit_code=exit_code,
                error_message="Output did not match expected answer.",
                raw_provider_response=data,
            )

        # Status 5: Time Limit Exceeded
        if status_id == 5:
            return ExecutionResult(
                status=ExecutionStatus.TIME_LIMIT_EXCEEDED,
                passed=False,
                stdout=stdout,
                stderr=stderr,
                compile_output=compile_output,
                time_seconds=time_val,
                memory_kb=memory_val,
                exit_code=exit_code,
                error_message="Time limit exceeded during execution.",
                raw_provider_response=data,
            )

        # Status 6: Compilation Error
        if status_id == 6:
            return ExecutionResult(
                status=ExecutionStatus.COMPILATION_ERROR,
                passed=False,
                stdout=stdout,
                stderr=stderr,
                compile_output=compile_output,
                time_seconds=time_val,
                memory_kb=memory_val,
                exit_code=exit_code,
                error_message=compile_output or stderr or "Compilation failed.",
                raw_provider_response=data,
            )

        # Status 14: Exec Format Error
        if status_id == 14:
            return ExecutionResult(
                status=ExecutionStatus.COMPILATION_ERROR,
                passed=False,
                stdout=stdout,
                stderr=stderr,
                compile_output=compile_output,
                time_seconds=time_val,
                memory_kb=memory_val,
                exit_code=exit_code,
                error_message="Exec format error: executable binary format invalid or unsupported.",
                raw_provider_response=data,
            )

        # Status 13: Internal Error (Judge0 sandbox internal issue)
        if status_id == 13:
            return ExecutionResult(
                status=ExecutionStatus.SANDBOX_ERROR,
                passed=False,
                stdout=stdout,
                stderr=stderr,
                compile_output=compile_output,
                time_seconds=time_val,
                memory_kb=memory_val,
                exit_code=exit_code,
                error_message=message or f"Judge0 sandbox internal error: {status_desc}",
                raw_provider_response=data,
            )

        # Memory limit exceeded check
        if is_memory_limit:
            return ExecutionResult(
                status=ExecutionStatus.MEMORY_LIMIT_EXCEEDED,
                passed=False,
                stdout=stdout,
                stderr=stderr,
                compile_output=compile_output,
                time_seconds=time_val,
                memory_kb=memory_val,
                exit_code=exit_code,
                error_message=f"Memory limit exceeded: {status_desc}",
                raw_provider_response=data,
            )

        # Status 7-12: Runtime Error
        if status_id in (7, 8, 9, 10, 11, 12):
            return ExecutionResult(
                status=ExecutionStatus.RUNTIME_ERROR,
                passed=False,
                stdout=stdout,
                stderr=stderr,
                compile_output=compile_output,
                time_seconds=time_val,
                memory_kb=memory_val,
                exit_code=exit_code,
                error_message=stderr or message or f"Runtime error: {status_desc}",
                raw_provider_response=data,
            )

        # Fallback for unrecognized status
        return ExecutionResult(
            status=ExecutionStatus.SANDBOX_ERROR,
            passed=False,
            stdout=stdout,
            stderr=stderr,
            compile_output=compile_output,
            time_seconds=time_val,
            memory_kb=memory_val,
            exit_code=exit_code,
            error_message=message or f"Execution completed with unexpected status ({status_id}): {status_desc}",
            raw_provider_response=data,
        )

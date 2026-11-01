"""Base abstraction for isolated code execution sandboxes.

SkillProof AI enforces isolated, sandboxed execution for all untrusted
student code. Neither FastAPI nor any local server process will execute
student submissions directly.
"""

from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel
from app.models import ExecutionStatus


class ExecutionResult(BaseModel):
    """Normalized result returned from an isolated execution sandbox."""
    status: str
    passed: bool = False
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    time_seconds: Optional[float] = None
    memory_kb: Optional[int] = None
    exit_code: Optional[int] = None
    error_message: Optional[str] = None
    raw_provider_response: Optional[dict] = None


class SandboxProvider(ABC):
    """Abstract base class for all sandbox execution providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the sandbox provider (e.g. 'judge0', 'mock')."""
        pass

    @abstractmethod
    def execute(
        self,
        source_code: str,
        language: str = "python",
        stdin: str = "",
        timeout_seconds: float = 5.0,
    ) -> ExecutionResult:
        """Execute source code in the isolated sandbox.

        Args:
            source_code: Source code to execute.
            language: Programming language identifier ('python', 'javascript', etc.).
            stdin: Standard input to feed to the program.
            timeout_seconds: Maximum wall-clock execution time allowed.

        Returns:
            ExecutionResult with standardized status, outputs, and performance metrics.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verify whether the sandbox provider endpoint is reachable and operational."""
        pass

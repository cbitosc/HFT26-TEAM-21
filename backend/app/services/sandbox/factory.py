"""Factory for obtaining the active SandboxProvider instance."""

from app.config import get_settings
from app.services.sandbox.base import SandboxProvider
from app.services.sandbox.judge0 import Judge0SandboxProvider
from app.services.sandbox.mock import MockSandboxProvider


def get_sandbox_provider() -> SandboxProvider:
    """Return configured sandbox provider based on settings."""
    settings = get_settings()
    provider_type = (settings.sandbox_provider or "judge0").lower().strip()

    if provider_type == "mock":
        return MockSandboxProvider()

    j0 = Judge0SandboxProvider(
        api_url=settings.judge0_api_url,
        api_key=settings.judge0_api_key,
        api_host=settings.judge0_api_host,
    )
    if not j0.is_configured():
        return MockSandboxProvider()

    return j0

import os
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables."""

    app_name: str = "SkillProof AI"
    app_env: str = "development"
    api_prefix: str = "/api"
    version: str = "1.0.0"

    # CORS configuration: default allows local Vite frontend and common development ports
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]

    # -----------------------------------------------------------------
    # Supabase configuration
    # These are loaded from backend/.env and must never be hardcoded.
    # -----------------------------------------------------------------
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # JWT verification settings.
    # Leave supabase_jwt_secret empty to use RS256/ES256 via JWKS (recommended).
    # Set supabase_jwt_algorithm to HS256 and provide the JWT secret only
    # if your Supabase project uses the legacy HS256 signing mode.
    supabase_jwt_secret: Optional[str] = None
    supabase_jwt_algorithm: str = "RS256"

    # Featherless AI configuration
    featherless_api_key: Optional[str] = None
    featherless_base_url: str = "https://api.featherless.ai/v1"
    featherless_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"

    # -----------------------------------------------------------------
    # Sandbox / Judge0 Code Execution Configuration (Module 7)
    # -----------------------------------------------------------------
    judge0_api_url: str = "https://judge0-ce.p.rapidapi.com"
    judge0_api_key: Optional[str] = None
    judge0_api_host: str = "judge0-ce.p.rapidapi.com"
    sandbox_provider: str = "judge0"  # "judge0" or "mock" for isolated testing

    model_config = SettingsConfigDict(
        env_file=(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")),
            ".env",
            "backend/.env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_supabase_configured(self) -> bool:
        """True when Supabase credentials are actually set (non-empty)."""
        return bool(self.supabase_url and self.supabase_service_role_key)

    @property
    def is_judge0_configured(self) -> bool:
        """True when Judge0 API key is set."""
        return bool(self.judge0_api_key and self.judge0_api_key.strip())

    @property
    def is_featherless_configured(self) -> bool:
        """True when Featherless AI API key is set."""
        return bool(self.featherless_api_key and self.featherless_api_key.strip())

    @property
    def jwks_uri(self) -> str:
        """JWKS public-key endpoint for this Supabase project."""
        return f"{self.supabase_url}/auth/v1/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton instance."""
    return Settings()

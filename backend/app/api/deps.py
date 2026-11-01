"""
FastAPI authentication and authorization dependencies for SkillProof AI.

Design principles:
- Fail-closed: any verification failure returns HTTP 401 / 403.
- Zero trust in JWT role claims: role is always fetched from the database.
- JWKS asymmetric verification (RS256/ES256) is the primary path.
- HS256 shared-secret fallback is available ONLY if explicitly configured.
- Service-role operations require the caller to be in public.platform_admins.
"""

from __future__ import annotations

import logging
from typing import Optional

import jwt
from jwt import PyJWKClient, PyJWKClientError, ExpiredSignatureError, InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import get_settings, Settings
from app.models import UserProfile

logger = logging.getLogger("skillproof.auth")

# ---------------------------------------------------------------------------
# Module-level JWKS client (cached and reused across requests)
# ---------------------------------------------------------------------------
_jwks_client: Optional[PyJWKClient] = None


def _get_jwks_client(settings: Settings) -> PyJWKClient:
    """Return a cached JWKS client; initialised lazily on first call."""
    global _jwks_client
    if _jwks_client is None and settings.supabase_url:
        _jwks_client = PyJWKClient(
            settings.jwks_uri,
            cache_jwk_set=True,
            lifespan=3600,
        )
    return _jwks_client  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Bearer token extractor
# ---------------------------------------------------------------------------
_bearer_scheme = HTTPBearer(auto_error=True)


def _extract_token(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    return credentials.credentials


# ---------------------------------------------------------------------------
# JWT verification
# ---------------------------------------------------------------------------

async def verify_supabase_jwt(
    token: str = Depends(_extract_token),
) -> dict:
    """
    Validates the Supabase JWT and returns the decoded payload.

    Flow:
      1. Attempt RS256/ES256 via JWKS (primary, fail-closed).
      2. If JWKS is unavailable AND HS256 is explicitly configured, fall back.
      3. Any other failure → HTTP 401.

    The JWT is never accepted if signature verification fails for any reason.
    """
    settings = get_settings()

    # Explicit rejection of guest session tokens on protected APIs (fail-closed)
    if token.startswith("guest_") or token.startswith("guest-") or token == "guest":
        logger.warning("Guest token rejected on protected API route: %s", token[:15])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Guest sessions have read-only demo access and cannot call protected backend APIs. Please sign in with an authenticated account.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Development and test token bypass
    if settings.app_env in ("development", "test"):
        if token == "dev-student-token" or token.startswith("dev-student-"):
            return {
                "sub": "00000000-0000-0000-0000-000000000001",
                "role": "authenticated",
                "email": "student@skillproof.ai",
            }
        elif token == "dev-recruiter-token" or token.startswith("dev-recruiter-"):
            return {
                "sub": "00000000-0000-0000-0000-000000000002",
                "role": "authenticated",
                "email": "recruiter@skillproof.ai",
            }
        elif token == "dev-college-admin-token" or token.startswith("dev-college-"):
            return {
                "sub": "00000000-0000-0000-0000-000000000003",
                "role": "authenticated",
                "email": "admin@college.edu",
            }
        elif token == "dev-admin-token" or token.startswith("dev-admin-"):
            return {
                "sub": "00000000-0000-0000-0000-000000000004",
                "role": "authenticated",
                "email": "platform-admin@skillproof.ai",
            }

    if not settings.supabase_url:
        logger.error("Supabase URL not configured. Cannot verify JWT.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not configured.",
        )

    # --- Primary path: JWKS asymmetric verification ---
    try:
        jwks_client = _get_jwks_client(settings)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience="authenticated",
            issuer=f"{settings.supabase_url}/auth/v1",
            leeway=30,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except PyJWKClientError as jwks_err:
        # JWKS retrieval failed — try HS256 fallback only if explicitly configured
        logger.warning("JWKS verification failure: %s", jwks_err)

        if (
            settings.supabase_jwt_algorithm == "HS256"
            and settings.supabase_jwt_secret
        ):
            try:
                return jwt.decode(
                    token,
                    settings.supabase_jwt_secret,
                    algorithms=["HS256"],
                    audience="authenticated",
                    issuer=f"{settings.supabase_url}/auth/v1",
                    leeway=30,
                    options={"require": ["exp", "iss", "aud", "sub"]},
                )
            except Exception:
                pass  # Fall through to generic rejection below

        # Fail closed: never accept on JWKS failure without valid fallback
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to verify token signature. Please try again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except Exception as exc:
        logger.error("Unexpected authentication error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# Profile resolution dependency
# ---------------------------------------------------------------------------

async def get_current_user_profile(
    payload: dict = Depends(verify_supabase_jwt),
) -> UserProfile:
    """
    Resolves the verified JWT sub claim to an authoritative database profile.
    Role is NEVER trusted from the JWT — only from the database record.
    """
    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing subject claim.",
        )

    settings = get_settings()
    # Development and test fallback users
    if settings.app_env in ("development", "test"):
        import uuid
        from datetime import datetime, timezone
        if user_id == "00000000-0000-0000-0000-000000000001":
            return UserProfile(
                id=uuid.UUID(user_id),
                email="student@skillproof.ai",
                full_name="Demo Student",
                requested_role="student",
                role="student",
                account_status="active",
                college_id=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        elif user_id == "00000000-0000-0000-0000-000000000002":
            return UserProfile(
                id=uuid.UUID(user_id),
                email="recruiter@skillproof.ai",
                full_name="Demo Recruiter",
                requested_role="recruiter",
                role="recruiter",
                account_status="active",
                college_id=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        elif user_id == "00000000-0000-0000-0000-000000000003":
            return UserProfile(
                id=uuid.UUID(user_id),
                email="admin@college.edu",
                full_name="College Administrator",
                requested_role="college_admin",
                role="college_admin",
                account_status="active",
                college_id=uuid.UUID("00000000-0000-0000-0000-000000000010"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        elif user_id == "00000000-0000-0000-0000-000000000004":
            return UserProfile(
                id=uuid.UUID(user_id),
                email="platform-admin@skillproof.ai",
                full_name="Platform Admin",
                requested_role="admin",
                role="admin",
                account_status="active",
                college_id=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

    try:
        result = (
            service_client()
            .table("profiles")
            .select("*")
            .eq("id", user_id)
            .single()
            .execute()
        )
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found.",
            )
        return UserProfile(**result.data)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Profile fetch error for user %s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve user profile.",
        )


# ---------------------------------------------------------------------------
# Role-based authorization
# ---------------------------------------------------------------------------

def require_role(*allowed_roles: str):
    """
    Factory returning a FastAPI dependency that enforces:
    - account_status == 'active'
    - profile.role in allowed_roles
    """
    async def role_checker(
        profile: UserProfile = Depends(get_current_user_profile),
    ) -> UserProfile:
        if profile.account_status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Account status is '{profile.account_status}'. "
                    "Active status required."
                ),
            )
        if profile.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Required role(s): {list(allowed_roles)}."
                ),
            )
        return profile

    return role_checker


# ---------------------------------------------------------------------------
# Platform Administrator authorization
# ---------------------------------------------------------------------------

async def require_platform_admin(
    profile: UserProfile = Depends(get_current_user_profile),
) -> UserProfile:
    """
    Verifies caller is registered in public.platform_admins as active.
    Used to protect admin approval/rejection endpoints.
    """
    from app.supabase_client import service_client

    try:
        result = (
            service_client()
            .table("platform_admins")
            .select("id")
            .eq("id", str(profile.id))
            .eq("is_active", True)
            .single()
            .execute()
        )
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Platform administrator credentials required.",
            )
        return profile
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Platform admin check error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not verify administrator status.",
        )

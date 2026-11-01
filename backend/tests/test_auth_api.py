"""
Automated unit & integration tests for SkillProof AI Module 2 Authentication API.

Uses httpx.AsyncClient with ASGITransport for pure asyncio execution
compatible with Python 3.14 without blocking threads.

Tests:
1. Root & Health check endpoints
2. Unauthenticated access enforcement (401 Unauthorized on protected routes)
3. Invalid / malformed JWT rejection (401 Fail-Closed)
4. Role-based access control dependency enforcement (Active status & Role checking)
5. Pydantic request models input validation
"""

import uuid
from datetime import datetime, timezone
import pytest
import pytest_asyncio
import httpx
from fastapi import HTTPException

from app.main import app
from app.models import (
    UserProfile,
    ProfileUpdateRequest,
    CollegeAdminRequestCreate,
    RecruiterRequestCreate,
    RejectionRequest,
)
from app.api.deps import require_role


@pytest_asyncio.fixture
async def client():
    """AsyncClient fixture using native ASGITransport."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# 1. Foundation & Health Endpoints
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_root_endpoint(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "SkillProof AI" in data["name"]


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


# ---------------------------------------------------------------------------
# 2. Authentication Enforcement (Fail-Closed)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_auth_me_without_token_returns_401(client):
    """Calling /api/auth/me without an Authorization header must return 401."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"] or "Bearer" in response.headers.get("www-authenticate", "")


@pytest.mark.asyncio
async def test_auth_me_with_invalid_token_returns_401(client):
    """Calling /api/auth/me with a fabricated / malformed JWT must return 401 or 503."""
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.payload"}
    )
    assert response.status_code in (401, 503)


@pytest.mark.asyncio
async def test_requests_unauthenticated_returns_401(client):
    """Verification request endpoints must reject unauthenticated callers."""
    response = await client.get("/api/requests/college-admin")
    assert response.status_code == 401

    response = await client.get("/api/requests/recruiter")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_endpoints_unauthenticated_returns_401(client):
    """Platform admin endpoints must reject unauthenticated callers."""
    response = await client.get("/api/admin/requests/college-admin")
    assert response.status_code == 401

    response = await client.get("/api/admin/audit-logs")
    assert response.status_code == 401

    response = await client.post(
        "/api/admin/approve/college-admin",
        json={"request_id": str(uuid.uuid4())}
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# 3. RBAC Dependency Logic Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_require_role_accepts_valid_role_and_active_status():
    """Authorized role + active account status must pass dependency check."""
    profile = UserProfile(
        id=uuid.uuid4(),
        email="student@example.com",
        full_name="Valid Student",
        requested_role="student",
        role="student",
        account_status="active",
        college_id=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    checker = require_role("student")
    result = await checker(profile)
    assert result.role == "student"
    assert result.account_status == "active"


@pytest.mark.asyncio
async def test_require_role_rejects_pending_account_status():
    """Pending account status must be rejected with HTTP 403 Forbidden."""
    profile = UserProfile(
        id=uuid.uuid4(),
        email="pending@example.com",
        full_name="Pending Admin",
        requested_role="college_admin",
        role="college_admin",
        account_status="pending_approval",
        college_id=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    checker = require_role("college_admin")
    with pytest.raises(HTTPException) as exc_info:
        await checker(profile)
    assert exc_info.value.status_code == 403
    assert "pending_approval" in exc_info.value.detail


@pytest.mark.asyncio
async def test_require_role_rejects_unauthorized_role():
    """Active student attempting to access recruiter endpoint must receive HTTP 403."""
    profile = UserProfile(
        id=uuid.uuid4(),
        email="student@example.com",
        full_name="Active Student",
        requested_role="student",
        role="student",
        account_status="active",
        college_id=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    checker = require_role("recruiter")
    with pytest.raises(HTTPException) as exc_info:
        await checker(profile)
    assert exc_info.value.status_code == 403
    assert "Access denied" in exc_info.value.detail


# ---------------------------------------------------------------------------
# 4. Pydantic Model Validation Tests
# ---------------------------------------------------------------------------

def test_profile_update_validation():
    """Blank or whitespace-only full_name must fail validation."""
    with pytest.raises(ValueError):
        ProfileUpdateRequest(full_name="   ")

    valid = ProfileUpdateRequest(full_name="  John Doe  ")
    assert valid.full_name == "John Doe"


def test_rejection_request_validation():
    """Short or empty rejection reason must fail validation."""
    with pytest.raises(ValueError):
        RejectionRequest(request_id=uuid.uuid4(), reason="no")

    valid = RejectionRequest(request_id=uuid.uuid4(), reason="Documentation was unverifiable.")
    assert valid.reason == "Documentation was unverifiable."

"""
Platform administrator endpoints.
All routes require the caller to be in public.platform_admins.
These endpoints invoke SECURITY DEFINER PostgreSQL functions via service_role
to atomically approve or reject verification requests.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import require_platform_admin
from app.models import (
    UserProfile,
    ApprovalRequest,
    RejectionRequest,
    AdminAuditLogResponse,
    SuccessResponse,
)
from app.supabase_client import service_client

logger = logging.getLogger("skillproof.admin")
router = APIRouter()


# ---------------------------------------------------------------------------
# Pending requests listing
# ---------------------------------------------------------------------------

@router.get(
    "/requests/college-admin",
    summary="List pending college admin requests",
)
async def list_pending_college_admin_requests(
    _admin: UserProfile = Depends(require_platform_admin),
) -> dict:
    """Lists all pending college administrator verification requests."""
    try:
        result = (
            service_client()
            .table("college_admin_requests")
            .select("*, profiles(email, full_name), colleges(name)")
            .eq("verification_status", "pending")
            .order("created_at")
            .execute()
        )
        return {"requests": result.data or []}
    except Exception as exc:
        logger.error("Error fetching college admin requests: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve pending requests.",
        )


@router.get(
    "/requests/recruiter",
    summary="List pending recruiter requests",
)
async def list_pending_recruiter_requests(
    _admin: UserProfile = Depends(require_platform_admin),
) -> dict:
    """Lists all pending recruiter verification requests."""
    try:
        result = (
            service_client()
            .table("recruiter_profiles")
            .select("*, profiles(email, full_name)")
            .eq("verification_status", "pending")
            .order("created_at")
            .execute()
        )
        return {"requests": result.data or []}
    except Exception as exc:
        logger.error("Error fetching recruiter requests: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve pending requests.",
        )


# ---------------------------------------------------------------------------
# Approval endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/approve/college-admin",
    response_model=SuccessResponse,
    summary="Approve a college admin request",
)
async def approve_college_admin(
    body: ApprovalRequest,
    admin: UserProfile = Depends(require_platform_admin),
) -> SuccessResponse:
    """
    Approves a pending college administrator verification request.
    Calls the hardened SECURITY DEFINER PostgreSQL function which:
    - Validates reviewer is in platform_admins
    - Acquires row locks to prevent concurrent duplicates
    - Atomically promotes the account to college_admin + active
    """
    try:
        result = service_client().rpc(
            "approve_college_admin_request",
            {"p_request_id": str(body.request_id), "p_reviewer_id": str(admin.id)},
        ).execute()

        return SuccessResponse(
            message=f"College admin request {body.request_id} approved successfully."
        )
    except Exception as exc:
        logger.error("Approve college admin error: %s", exc)
        error_msg = str(exc)
        if "not pending" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Request is no longer pending.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not approve request.",
        )


@router.post(
    "/approve/recruiter",
    response_model=SuccessResponse,
    summary="Approve a recruiter request",
)
async def approve_recruiter(
    body: ApprovalRequest,
    admin: UserProfile = Depends(require_platform_admin),
) -> SuccessResponse:
    """
    Approves a pending recruiter verification request via SECURITY DEFINER function.
    """
    try:
        result = service_client().rpc(
            "approve_recruiter_request",
            {"p_request_id": str(body.request_id), "p_reviewer_id": str(admin.id)},
        ).execute()

        return SuccessResponse(
            message=f"Recruiter request {body.request_id} approved successfully."
        )
    except Exception as exc:
        logger.error("Approve recruiter error: %s", exc)
        error_msg = str(exc)
        if "not pending" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Request is no longer pending.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not approve request.",
        )


# ---------------------------------------------------------------------------
# Rejection endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/reject",
    response_model=SuccessResponse,
    summary="Reject a verification request",
)
async def reject_request(
    body: RejectionRequest,
    request_type: str,
    admin: UserProfile = Depends(require_platform_admin),
) -> SuccessResponse:
    """
    Rejects a pending verification request (college_admin or recruiter).
    A non-empty rejection reason is mandatory.
    Calls the hardened SECURITY DEFINER PostgreSQL function.
    """
    if request_type not in ("college_admin", "recruiter"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="request_type must be 'college_admin' or 'recruiter'.",
        )
    try:
        service_client().rpc(
            "reject_verification_request",
            {
                "p_request_type": request_type,
                "p_request_id": str(body.request_id),
                "p_reviewer_id": str(admin.id),
                "p_reason": body.reason,
            },
        ).execute()

        return SuccessResponse(
            message=f"Request {body.request_id} rejected."
        )
    except Exception as exc:
        logger.error("Reject request error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not reject request.",
        )


# ---------------------------------------------------------------------------
# Audit logs listing (Item 3 Correction)
# ---------------------------------------------------------------------------

@router.get(
    "/audit-logs",
    response_model=List[AdminAuditLogResponse],
    summary="List administrative audit logs",
)
async def list_audit_logs(
    _admin: UserProfile = Depends(require_platform_admin),
) -> List[AdminAuditLogResponse]:
    """
    Lists append-only administrative audit log entries.
    Accessible strictly by authorized platform administrators.
    """
    try:
        result = (
            service_client()
            .table("admin_audit_logs")
            .select("*")
            .order("created_at", desc=True)
            .limit(100)
            .execute()
        )
        return [AdminAuditLogResponse(**row) for row in (result.data or [])]
    except Exception as exc:
        logger.error("Error fetching audit logs: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve audit logs.",
        )

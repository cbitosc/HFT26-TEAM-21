"""
Verification request routes.
Allows pending College Admins and Recruiters to submit and view their
own verification requests after registering with the appropriate role.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user_profile
from app.models import (
    UserProfile,
    CollegeAdminRequestCreate,
    CollegeAdminRequestResponse,
    RecruiterRequestCreate,
    RecruiterRequestResponse,
)
from app.supabase_client import service_client

logger = logging.getLogger("skillproof.requests")
router = APIRouter()


# ---------------------------------------------------------------------------
# College Admin Requests
# ---------------------------------------------------------------------------

@router.post(
    "/college-admin",
    response_model=CollegeAdminRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit college admin verification request",
)
async def submit_college_admin_request(
    body: CollegeAdminRequestCreate,
    profile: UserProfile = Depends(get_current_user_profile),
) -> CollegeAdminRequestResponse:
    """
    Submit a verification request for College Administrator access.
    Only users whose account_status is 'pending_approval' and
    requested_role is 'college_admin' may call this endpoint.
    """
    if profile.account_status != "pending_approval":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only accounts with pending_approval status may submit verification requests.",
        )
    if profile.requested_role != "college_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only for college administrator applicants.",
        )

    # Check no duplicate submission
    existing = (
        service_client()
        .table("college_admin_requests")
        .select("id")
        .eq("user_id", str(profile.id))
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A verification request already exists for this account.",
        )

    try:
        result = (
            service_client()
            .table("college_admin_requests")
            .insert({
                "user_id": str(profile.id),
                "college_id": str(body.college_id),
                "department": body.department,
                "designation": body.designation,
                "verification_status": "pending",
            })
            .execute()
        )
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create verification request.",
            )
        return CollegeAdminRequestResponse(**result.data[0])
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("College admin request error for %s: %s", profile.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not submit verification request.",
        )


@router.get(
    "/college-admin",
    response_model=CollegeAdminRequestResponse,
    summary="Get own college admin verification request",
)
async def get_college_admin_request(
    profile: UserProfile = Depends(get_current_user_profile),
) -> CollegeAdminRequestResponse:
    """Returns the caller's own college admin verification request if it exists."""
    try:
        result = (
            service_client()
            .table("college_admin_requests")
            .select("*")
            .eq("user_id", str(profile.id))
            .single()
            .execute()
        )
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No verification request found for this account.",
            )
        return CollegeAdminRequestResponse(**result.data)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Fetch college admin request error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve verification request.",
        )


# ---------------------------------------------------------------------------
# Recruiter Requests
# ---------------------------------------------------------------------------

@router.post(
    "/recruiter",
    response_model=RecruiterRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit recruiter verification request",
)
async def submit_recruiter_request(
    body: RecruiterRequestCreate,
    profile: UserProfile = Depends(get_current_user_profile),
) -> RecruiterRequestResponse:
    """
    Submit a verification request for Verified Recruiter access.
    Only users whose account_status is 'pending_approval' and
    requested_role is 'recruiter' may call this endpoint.
    """
    if profile.account_status != "pending_approval":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only accounts with pending_approval status may submit verification requests.",
        )
    if profile.requested_role != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only for recruiter applicants.",
        )

    # Check no duplicate submission
    existing = (
        service_client()
        .table("recruiter_profiles")
        .select("id")
        .eq("user_id", str(profile.id))
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A verification request already exists for this account.",
        )

    try:
        result = (
            service_client()
            .table("recruiter_profiles")
            .insert({
                "user_id": str(profile.id),
                "company_name": body.company_name,
                "work_email": body.work_email,
                "designation": body.designation,
                "company_website": body.company_website,
                "linkedin_url": body.linkedin_url,
                "verification_status": "pending",
            })
            .execute()
        )
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create verification request.",
            )
        return RecruiterRequestResponse(**result.data[0])
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Recruiter request error for %s: %s", profile.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not submit verification request.",
        )


@router.get(
    "/recruiter",
    response_model=RecruiterRequestResponse,
    summary="Get own recruiter verification request",
)
async def get_recruiter_request(
    profile: UserProfile = Depends(get_current_user_profile),
) -> RecruiterRequestResponse:
    """Returns the caller's own recruiter verification request if it exists."""
    try:
        result = (
            service_client()
            .table("recruiter_profiles")
            .select("*")
            .eq("user_id", str(profile.id))
            .single()
            .execute()
        )
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No verification request found for this account.",
            )
        return RecruiterRequestResponse(**result.data)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Fetch recruiter request error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve verification request.",
        )

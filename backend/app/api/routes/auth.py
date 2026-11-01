"""
Auth routes — profile self-service.
Actual login/signup is handled by Supabase JS on the frontend.
These endpoints verify the JWT and return authoritative server-side profile data.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user_profile
from app.models import UserProfile, ProfileResponse, ProfileUpdateRequest
from app.supabase_client import service_client

logger = logging.getLogger("skillproof.auth")
router = APIRouter()


@router.get("/me", response_model=ProfileResponse, summary="Get own profile")
async def get_me(
    profile: UserProfile = Depends(get_current_user_profile),
) -> ProfileResponse:
    """
    Returns the authenticated user's authoritative profile from the database.
    The role returned here is the single source of truth — never the JWT claim.
    """
    return ProfileResponse(
        id=profile.id,
        email=profile.email,
        full_name=profile.full_name,
        requested_role=profile.requested_role,
        role=profile.role,
        account_status=profile.account_status,
        college_id=profile.college_id,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.patch("/me", response_model=ProfileResponse, summary="Update own profile")
async def update_me(
    body: ProfileUpdateRequest,
    profile: UserProfile = Depends(get_current_user_profile),
) -> ProfileResponse:
    """
    Updates the authenticated user's profile.
    Only full_name may be changed; all other fields are server-controlled.
    """
    try:
        result = (
            service_client()
            .table("profiles")
            .update({"full_name": body.full_name})
            .eq("id", str(profile.id))
            .execute()
        )
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found.",
            )
        updated = result.data[0]
        return ProfileResponse(**updated)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Profile update error for %s: %s", profile.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update profile.",
        )

"""
Colleges listing route.
Public: returns all colleges for populating registration dropdown.
No authentication required — colleges are read-only public data.
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, status

from app.models import CollegeResponse
from app.supabase_client import service_client

logger = logging.getLogger("skillproof.colleges")
router = APIRouter()


@router.get("/", response_model=List[CollegeResponse], summary="List all colleges")
async def list_colleges() -> List[CollegeResponse]:
    """
    Returns all colleges available for selection during College Admin registration.
    Publicly accessible — no authentication required.
    """
    try:
        result = (
            service_client()
            .table("colleges")
            .select("id, name, code, domain")
            .order("name")
            .execute()
        )
        return [CollegeResponse(**row) for row in (result.data or [])]
    except Exception as exc:
        logger.error("Failed to fetch colleges: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve colleges.",
        )

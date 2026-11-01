"""
Portfolio API routes for SkillProof AI (Module 3).
Provides student portfolio upload, extraction, review, and confirmation.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from app.api.deps import require_role
from app.models import (
    UserProfile,
    PortfolioResponse,
    PortfolioConfirmRequest,
)
from app.services.portfolio_extractor import (
    validate_file,
    extract_portfolio_from_json,
    extract_portfolio_from_pdf,
    interpret_portfolio_with_featherless,
)
from app.services.portfolio_storage import (
    get_portfolio,
    save_portfolio,
)

logger = logging.getLogger("skillproof.portfolio.routes")
router = APIRouter()


@router.post(
    "/upload",
    response_model=PortfolioResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload and extract portfolio (PDF or JSON)",
)
async def upload_portfolio(
    file: UploadFile = File(...),
    student: UserProfile = Depends(require_role("student")),
) -> PortfolioResponse:
    """
    Accepts an authenticated student upload (.pdf or .json).
    Validates file integrity and size, extracts projects, skills, domains, and DSA topics.
    Saves the extracted information as an unconfirmed draft for candidate review.
    """
    filename = file.filename or "portfolio"
    logger.info("Processing portfolio upload for student %s: %s", student.id, filename)

    try:
        content = await file.read()
    except Exception as exc:
        logger.error("Error reading uploaded file: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded file payload.",
        )

    # 1. Validate file extension, size limit, and header magic bytes
    file_type = validate_file(filename, content)

    # 2. Extract content based on validated file type
    if file_type == "json":
        extracted_data = extract_portfolio_from_json(content)
    elif file_type == "pdf":
        extracted_data = extract_portfolio_from_pdf(content)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_type}",
        )

    # 3. Privacy-safe semantic enhancement with Featherless AI (with deterministic fallback)
    try:
        extracted_data = await interpret_portfolio_with_featherless(extracted_data)
    except Exception as exc:
        logger.info("Featherless portfolio interpretation skipped: %s", exc)

    # 4. Store as unconfirmed working draft
    saved = save_portfolio(
        user_id=student.id,
        portfolio_data=extracted_data,
        confirmed=False,
        raw_filename=filename,
        file_type=file_type,
    )

    return saved


@router.get(
    "/me",
    response_model=PortfolioResponse,
    summary="Get current student's portfolio",
)
async def get_my_portfolio(
    student: UserProfile = Depends(require_role("student")),
) -> PortfolioResponse:
    """
    Retrieves the current authenticated student's portfolio.
    Returns HTTP 404 if no portfolio has been uploaded yet.
    """
    portfolio = get_portfolio(student.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No portfolio found. Please upload a PDF or JSON portfolio file.",
        )
    return portfolio


@router.post(
    "/confirm",
    response_model=PortfolioResponse,
    summary="Confirm or update student portfolio",
)
async def confirm_portfolio(
    body: PortfolioConfirmRequest,
    student: UserProfile = Depends(require_role("student")),
) -> PortfolioResponse:
    """
    Confirms the student's reviewed and edited portfolio details.
    Marks the portfolio as confirmed while explicitly keeping skills as 'unverified'.
    This boundary defines the candidate's eligible assessment scope.
    """
    logger.info("Confirming portfolio for student %s", student.id)
    saved = save_portfolio(
        user_id=student.id,
        portfolio_data=body.data,
        confirmed=True,
    )
    return saved

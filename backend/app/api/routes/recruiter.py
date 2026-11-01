"""
FastAPI Routes for Recruiter Portal and Live Coding Interviews (Module 12).

Endpoints:
  - Student: Toggle and check recruiter discoverability consent, view interview invitations.
  - Recruiter: Candidate search/filtering, candidate dossier review, schedule interview, sync code, request code changes, finish interview.
  - Live Interview Room: Shared workspace synchronization, sandbox test execution.
  - Role enforcement: Recruiter routes require active recruiter; consent toggle requires student.
"""

from __future__ import annotations

import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, status

from app.api.deps import require_role
from app.models import (
    UserProfile,
    CandidateDiscoveryItem,
    CandidateDetailProfileResponse,
    RecruiterConsentToggleRequest,
    InterviewSessionCreate,
    InterviewSessionResponse,
    InterviewRespondRequest,
    InterviewSyncRequest,
    InterviewChangeRequest,
    InterviewFinishRequest,
)
from app.services import recruiter_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Student Consent Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/consent",
    summary="Get student's recruiter discoverability consent status",
)
def get_consent(
    student: UserProfile = Depends(require_role("student")),
):
    is_granted = recruiter_service.get_student_consent(student)
    return {"recruiter_discoverable": is_granted}


@router.post(
    "/consent",
    summary="Update or toggle recruiter discoverability consent",
)
def update_consent(
    payload: RecruiterConsentToggleRequest,
    student: UserProfile = Depends(require_role("student")),
):
    result = recruiter_service.set_student_consent(student, payload.recruiter_discoverable)
    return {"recruiter_discoverable": result}


@router.get(
    "/my-interviews",
    response_model=List[InterviewSessionResponse],
    summary="List interview invitations for the current student",
)
def get_my_interviews(
    student: UserProfile = Depends(require_role("student")),
):
    return recruiter_service.list_student_interviews(student)


# ---------------------------------------------------------------------------
# Recruiter Discovery Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/candidates",
    response_model=List[CandidateDiscoveryItem],
    summary="Search consenting candidates by domain, skill, or score",
)
def search_candidates(
    domain: Optional[str] = None,
    skill: Optional[str] = None,
    min_score: Optional[float] = None,
    difficulty: Optional[str] = None,
    recruiter: UserProfile = Depends(require_role("recruiter")),
):
    return recruiter_service.discover_candidates(
        recruiter=recruiter,
        domain=domain,
        skill=skill,
        min_score=min_score,
        difficulty=difficulty,
    )


@router.get(
    "/candidates/{candidate_id}",
    response_model=CandidateDetailProfileResponse,
    summary="View verified candidate assessment dossier (requires consent)",
)
def get_candidate_dossier(
    candidate_id: uuid.UUID,
    recruiter: UserProfile = Depends(require_role("recruiter")),
):
    return recruiter_service.get_candidate_dossier(recruiter, candidate_id)


# ---------------------------------------------------------------------------
# Live Coding Interview Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/interviews",
    response_model=InterviewSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a live interview with a consenting candidate",
)
def create_interview(
    payload: InterviewSessionCreate,
    recruiter: UserProfile = Depends(require_role("recruiter")),
):
    return recruiter_service.create_interview_session(recruiter, payload)


@router.get(
    "/interviews",
    response_model=List[InterviewSessionResponse],
    summary="List all interviews organized by the recruiter",
)
def list_interviews(
    recruiter: UserProfile = Depends(require_role("recruiter")),
):
    return recruiter_service.list_recruiter_interviews(recruiter)


@router.get(
    "/interviews/{session_id}",
    response_model=InterviewSessionResponse,
    summary="Get interview session details (recruiter or invited candidate)",
)
def get_interview(
    session_id: uuid.UUID,
    user: UserProfile = Depends(require_role("recruiter", "student")),
):
    return recruiter_service.get_interview_session(user, session_id)


@router.post(
    "/interviews/{session_id}/sync",
    response_model=InterviewSessionResponse,
    summary="Synchronize code in the shared interview workspace",
)
def sync_interview(
    session_id: uuid.UUID,
    payload: InterviewSyncRequest,
    user: UserProfile = Depends(require_role("recruiter", "student")),
):
    return recruiter_service.sync_interview_code(user, session_id, payload)


@router.post(
    "/interviews/{session_id}/request-change",
    response_model=InterviewSessionResponse,
    summary="Recruiter requests a code refactoring or change",
)
def request_code_change(
    session_id: uuid.UUID,
    payload: InterviewChangeRequest,
    recruiter: UserProfile = Depends(require_role("recruiter")),
):
    return recruiter_service.request_interview_code_change(recruiter, session_id, payload)


@router.post(
    "/interviews/{session_id}/execute",
    summary="Run interview code against isolated sandbox",
)
def execute_interview_sandbox(
    session_id: uuid.UUID,
    custom_input: Optional[str] = None,
    user: UserProfile = Depends(require_role("recruiter", "student")),
):
    return recruiter_service.execute_interview_sandbox(user, session_id, custom_input)


@router.post(
    "/interviews/{session_id}/respond",
    response_model=InterviewSessionResponse,
    summary="Candidate accepts or declines an interview invitation",
)
def respond_interview_invitation(
    session_id: uuid.UUID,
    payload: InterviewRespondRequest,
    student: UserProfile = Depends(require_role("student")),
):
    return recruiter_service.respond_to_interview_invitation(student, session_id, payload)


@router.post(
    "/interviews/{session_id}/finish",
    response_model=InterviewSessionResponse,
    summary="Finish interview and record recruiter feedback and outcome",
)
def finish_interview(
    session_id: uuid.UUID,
    payload: InterviewFinishRequest,
    recruiter: UserProfile = Depends(require_role("recruiter")),
):
    return recruiter_service.finish_interview_session(recruiter, session_id, payload)

"""
Assessment & Question Bank API routes for SkillProof AI (Modules 4, 5, 6, 9 & 10).
Provides endpoints for question bank exploration, assessment generation by the agent,
session retrieval, answer submission, performance summaries, and analytics.
"""

from __future__ import annotations

import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import require_role
from app.models import (
    UserProfile,
    AssessmentGenerateRequest,
    AssessmentSessionResponse,
    AssessmentSubmitRequest,
    AssessmentSummaryResponse,
    QuestionPublic,
    SampleRunRequest,
    SampleRunResponse,
    CodeTraceEventCreate,
    CodeTraceEventResponse,
    CodeTraceTimelineResponse,
    AssistantHintRequest,
    AssistantExplainErrorRequest,
    AssistantChatRequest,
    AssistantResponse,
    AnalyticsResponse,
)
from app.services.assistant_service import (
    get_progressive_hint,
    explain_error,
    chat_with_assistant,
    AssistantDisabledException,
    AssistantValidationException,
    AssistantRateLimitException,
)
from app.services.question_bank import (
    get_all_questions,
    get_question_by_id,
    to_public_question,
    filter_questions,
)
from app.services.assessment_agent import (
    coordinate_assessment,
    get_session,
    submit_and_evaluate_assessment,
    list_user_assessments,
    run_sample_code,
)
from app.services.codetrace_service import (
    log_codetrace_event,
    get_codetrace_timeline,
)
from app.services.analytics_service import compute_student_analytics

logger = logging.getLogger("skillproof.assessment.routes")
router = APIRouter()


# ---------------------------------------------------------------------------
# Module 4: Question Bank Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/questions",
    response_model=List[QuestionPublic],
    summary="List questions from verified question bank",
)
async def list_questions(
    difficulty: Optional[str] = None,
    domain: Optional[str] = None,
    topic: Optional[str] = None,
    _student: UserProfile = Depends(require_role("student")),
) -> List[QuestionPublic]:
    """
    Returns verified coding challenges matching filters.
    Strictly conceals reference solutions and hidden test cases.
    """
    questions = filter_questions(difficulty=difficulty, domain=domain, topic=topic)
    return [to_public_question(q) for q in questions]


@router.get(
    "/questions/{question_id}",
    response_model=QuestionPublic,
    summary="Get single question details",
)
async def get_question(
    question_id: str,
    _student: UserProfile = Depends(require_role("student")),
) -> QuestionPublic:
    """Retrieves a single question without reference solutions."""
    q = get_question_by_id(question_id)
    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found in verified bank.",
        )
    return to_public_question(q)


# ---------------------------------------------------------------------------
# Module 5 & 6: Assessment Agent & Student Assessment Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/generate",
    response_model=AssessmentSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate assessment matched to student portfolio",
)
async def generate_assessment(
    req: AssessmentGenerateRequest,
    student: UserProfile = Depends(require_role("student")),
) -> AssessmentSessionResponse:
    """
    Invokes the Assessment Agent:
    Reads student's confirmed portfolio, matches skills with verified questions,
    and returns a tailored assessment session.
    """
    return await coordinate_assessment(student.id, req)


@router.get(
    "/session/{session_id}",
    response_model=AssessmentSessionResponse,
    summary="Get active assessment session",
)
async def get_assessment_session(
    session_id: str,
    student: UserProfile = Depends(require_role("student")),
) -> AssessmentSessionResponse:
    """Retrieves an active assessment session for the student."""
    session_obj = get_session(session_id, student.id)
    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found or does not belong to you.",
        )
    return session_obj


@router.post(
    "/session/{session_id}/submit",
    response_model=AssessmentSummaryResponse,
    summary="Submit answers and evaluate assessment",
)
async def submit_assessment(
    session_id: str,
    body: AssessmentSubmitRequest,
    student: UserProfile = Depends(require_role("student")),
) -> AssessmentSummaryResponse:
    """
    Evaluates submitted code against test cases deterministically.
    Updates the session to completed and returns full performance summary.
    """
    try:
        summary = submit_and_evaluate_assessment(session_id, student.id, body)
        return summary
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err),
        )


@router.get(
    "/history",
    summary="List past assessment sessions",
)
async def get_assessment_history(
    student: UserProfile = Depends(require_role("student")),
) -> List[dict]:
    """Returns assessment history for the current student."""
    return list_user_assessments(student.id)


# ---------------------------------------------------------------------------
# Module 7: Isolated Code Execution (Sample Run)
# ---------------------------------------------------------------------------

@router.post(
    "/session/{session_id}/run-sample",
    response_model=SampleRunResponse,
    summary="Execute sample run in isolated container sandbox",
)
async def execute_sample_run(
    session_id: str,
    body: SampleRunRequest,
    student: UserProfile = Depends(require_role("student")),
) -> SampleRunResponse:
    """
    Submits code to the isolated execution sandbox to evaluate against sample test cases.
    Untrusted code is strictly executed inside isolated containers (Judge0 / Mock).
    """
    try:
        result = run_sample_code(session_id, student.id, body)
        return result
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err),
        )


# ---------------------------------------------------------------------------
# Module 8: CodeTrace Telemetry & Journey Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/session/{session_id}/codetrace",
    response_model=CodeTraceEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log CodeTrace coding journey event",
)
async def log_codetrace(
    session_id: str,
    event: CodeTraceEventCreate,
    student: UserProfile = Depends(require_role("student")),
) -> CodeTraceEventResponse:
    """
    Logs an incremental code snapshot, test execution event, or paste cadence.
    Records fine-grained version history for constructive problem-solving analysis.
    """
    try:
        sess_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id UUID format.",
        )

    # Verify session ownership
    sess_obj = get_session(session_id, student.id)
    if not sess_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found or does not belong to you.",
        )

    return log_codetrace_event(sess_uuid, student.id, event)


@router.get(
    "/session/{session_id}/codetrace",
    response_model=CodeTraceTimelineResponse,
    summary="Get CodeTrace coding journey timeline",
)
async def get_codetrace(
    session_id: str,
    student: UserProfile = Depends(require_role("student")),
) -> CodeTraceTimelineResponse:
    """
    Retrieves the chronological coding journey and diff progression for the session.
    """
    try:
        sess_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id UUID format.",
        )

    # Verify session ownership
    sess_obj = get_session(session_id, student.id)
    if not sess_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found or does not belong to you.",
        )

    return get_codetrace_timeline(sess_uuid, student.id)


# ---------------------------------------------------------------------------
# Module 9: Guarded AI Coding Assistant Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/session/{session_id}/assistant/hint",
    response_model=AssistantResponse,
    summary="Request progressive problem-solving hint",
)
async def request_hint(
    session_id: str,
    body: AssistantHintRequest,
    student: UserProfile = Depends(require_role("student")),
) -> AssistantResponse:
    """
    Returns progressive hints (Level 1, 2, or 3) for the active question.
    Derives tier and permissions exclusively from the server-side session.
    Strictly disabled on Novice Verified assessments (HTTP 403).
    """
    try:
        return await get_progressive_hint(session_id, student.id, body)
    except AssistantDisabledException as ade:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(ade))
    except AssistantRateLimitException as rle:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(rle))
    except AssistantValidationException as ave:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ave))


@router.post(
    "/session/{session_id}/assistant/explain-error",
    response_model=AssistantResponse,
    summary="Explain execution or compiler errors conceptually",
)
async def request_error_explanation(
    session_id: str,
    body: AssistantExplainErrorRequest,
    student: UserProfile = Depends(require_role("student")),
) -> AssistantResponse:
    """
    Explains runtime exceptions or compiler diagnostics conceptually without revealing code.
    Derives tier and permissions exclusively from the server-side session.
    Strictly disabled on Novice Verified assessments (HTTP 403).
    """
    try:
        return await explain_error(session_id, student.id, body)
    except AssistantDisabledException as ade:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(ade))
    except AssistantRateLimitException as rle:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(rle))
    except AssistantValidationException as ave:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ave))


@router.post(
    "/session/{session_id}/assistant/chat",
    response_model=AssistantResponse,
    summary="Chat with guarded AI Coding Assistant",
)
async def chat_assistant(
    session_id: str,
    body: AssistantChatRequest,
    student: UserProfile = Depends(require_role("student")),
) -> AssistantResponse:
    """
    Conversational problem-solving guidance under strict guardrails.
    Derives tier and permissions exclusively from the server-side session.
    Strictly disabled on Novice Verified assessments (HTTP 403).
    """
    try:
        return await chat_with_assistant(session_id, student.id, body)
    except AssistantDisabledException as ade:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(ade))
    except AssistantRateLimitException as rle:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(rle))
    except AssistantValidationException as ave:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ave))


# ---------------------------------------------------------------------------
# Module 10: Performance Analytics and Deterministic Scoring
# ---------------------------------------------------------------------------

@router.get(
    "/analytics",
    response_model=AnalyticsResponse,
    summary="Get student performance analytics and composite scoring report",
)
async def get_student_analytics(
    student: UserProfile = Depends(require_role("student")),
) -> AnalyticsResponse:
    """
    Returns a deterministic, auditable performance analytics report for the authenticated student.

    Scoring components:
    - Test Score Component (max 80): based on questions passed × difficulty weight.
    - AI Efficiency Component (max 20): deterministic CodeTrace signals (no LLM grading).

    Includes trend data, domain mastery, skill-tier breakdown, and hint utilization.
    Practice sessions are isolated and clearly labeled; verified sessions are weighted higher
    in the overall composite average.

    No LLM is used to evaluate or assign any grade in this endpoint.
    """
    return compute_student_analytics(student.id)



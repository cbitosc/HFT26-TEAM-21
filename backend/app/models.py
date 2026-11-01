"""Pydantic models for Module 2: Authentication and Role-Based Dashboards."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Shared / Base
# ---------------------------------------------------------------------------

class UserRole:
    STUDENT = "student"
    COLLEGE_ADMIN = "college_admin"
    RECRUITER = "recruiter"


class AccountStatus:
    ACTIVE = "active"
    PENDING = "pending_approval"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


# ---------------------------------------------------------------------------
# Profile Models
# ---------------------------------------------------------------------------

class UserProfile(BaseModel):
    """Authoritative user profile fetched from public.profiles."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    requested_role: str
    role: str
    account_status: str
    college_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class ProfileUpdateRequest(BaseModel):
    """Allowed user-driven profile update (full_name only)."""
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Display name shown on the platform.",
    )

    @field_validator("full_name")
    @classmethod
    def strip_and_validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("full_name must not be blank.")
        return stripped


class ProfileResponse(BaseModel):
    """Public-safe profile response shape."""
    id: uuid.UUID
    email: str
    full_name: str
    requested_role: str
    role: str
    account_status: str
    college_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# College Models
# ---------------------------------------------------------------------------

class CollegeResponse(BaseModel):
    """Response for a single college entry."""
    id: uuid.UUID
    name: str
    code: Optional[str] = None
    domain: Optional[str] = None


# ---------------------------------------------------------------------------
# College Admin Verification Request Models
# ---------------------------------------------------------------------------

class CollegeAdminRequestCreate(BaseModel):
    """Payload to submit a college administrator verification request."""
    college_id: uuid.UUID
    department: str = Field(..., min_length=1, max_length=200)
    designation: str = Field(..., min_length=1, max_length=200)

    @field_validator("department", "designation")
    @classmethod
    def strip_fields(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field must not be blank.")
        return stripped


class CollegeAdminRequestResponse(BaseModel):
    """Response for a college admin verification request."""
    id: uuid.UUID
    user_id: uuid.UUID
    college_id: uuid.UUID
    department: str
    designation: str
    verification_status: str
    rejection_reason: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Recruiter Verification Request Models
# ---------------------------------------------------------------------------

class RecruiterRequestCreate(BaseModel):
    """Payload to submit a recruiter verification request."""
    company_name: str = Field(..., min_length=1, max_length=300)
    work_email: EmailStr
    designation: str = Field(..., min_length=1, max_length=200)
    company_website: Optional[str] = Field(None, max_length=500)
    linkedin_url: Optional[str] = Field(None, max_length=500)

    @field_validator("company_name", "designation")
    @classmethod
    def strip_fields(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field must not be blank.")
        return stripped


class RecruiterRequestResponse(BaseModel):
    """Response for a recruiter verification request."""
    id: uuid.UUID
    user_id: uuid.UUID
    company_name: str
    work_email: str
    designation: str
    company_website: Optional[str] = None
    linkedin_url: Optional[str] = None
    verification_status: str
    rejection_reason: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Admin Approval/Rejection Models
# ---------------------------------------------------------------------------

class ApprovalRequest(BaseModel):
    """Admin request to approve a verification request."""
    request_id: uuid.UUID


class RejectionRequest(BaseModel):
    """Admin request to reject a verification request."""
    request_id: uuid.UUID
    reason: str = Field(..., min_length=5, max_length=1000)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, v: str) -> str:
        stripped = v.strip()
        if len(stripped) < 5:
            raise ValueError("Rejection reason must be at least 5 characters.")
        return stripped


# ---------------------------------------------------------------------------
# Admin Audit Log Models (Item 3)
# ---------------------------------------------------------------------------

class AdminAuditLogResponse(BaseModel):
    """Response representing an administrative audit log entry."""
    id: uuid.UUID
    request_id: uuid.UUID
    request_type: str
    applicant_id: Optional[uuid.UUID] = None
    applicant_email: Optional[str] = None
    reviewer_id: Optional[uuid.UUID] = None
    action: str
    rejection_reason: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# API response wrappers
# ---------------------------------------------------------------------------

class SuccessResponse(BaseModel):
    """Generic success response envelope."""
    success: bool = True
    message: str


# ---------------------------------------------------------------------------
# Portfolio Models (Module 3)
# ---------------------------------------------------------------------------

class ProjectItem(BaseModel):
    """Represents a project extracted or confirmed in a student portfolio."""
    name: str = ""
    description: str = ""
    technologies: List[str] = Field(default_factory=list)


class SkillsStructure(BaseModel):
    """Categorized skills."""
    programming_languages: List[str] = Field(default_factory=list)
    frameworks_and_tools: List[str] = Field(default_factory=list)


class PortfolioStructure(BaseModel):
    """Normalized portfolio structure required by SkillProof AI specifications."""
    projects: List[ProjectItem] = Field(default_factory=list)
    skills: SkillsStructure = Field(default_factory=SkillsStructure)
    domains: List[str] = Field(default_factory=list)
    dsa_topics: List[str] = Field(default_factory=list)


class PortfolioConfirmRequest(BaseModel):
    """Payload to confirm or update a student's portfolio data."""
    data: PortfolioStructure


class PortfolioResponse(BaseModel):
    """Student portfolio response envelope."""
    id: Optional[str] = None
    user_id: uuid.UUID
    confirmed: bool = False
    confirmed_at: Optional[datetime] = None
    skills_status: str = "unverified"
    data: PortfolioStructure
    raw_filename: Optional[str] = None
    file_type: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Question Bank Models (Module 4)
# ---------------------------------------------------------------------------

class TestCase(BaseModel):
    """Test case for validating question solutions."""
    input_data: str
    expected_output: str
    is_hidden: bool = False
    explanation: Optional[str] = None


class Question(BaseModel):
    """Full question entity containing verified reference solution and test cases."""
    id: str
    title: str
    difficulty: str  # "easy", "medium", "hard"
    domain: str      # e.g. "Backend Development", "Web Development", "Algorithms & DSA"
    topic: str       # e.g. "Arrays", "Hash Tables", "Trees", "REST APIs"
    language: str    # "python", "javascript", "typescript", etc.
    problem_statement: str
    constraints: Optional[str] = None
    starter_code: str
    sample_input: str
    sample_output: str
    reference_solution: str
    test_cases: List[TestCase] = Field(default_factory=list)
    is_verified: bool = True


class QuestionPublic(BaseModel):
    """Public question entity served to candidates (strictly conceals reference solution & hidden tests)."""
    id: str
    title: str
    difficulty: str
    domain: str
    topic: str
    language: str
    problem_statement: str
    constraints: Optional[str] = None
    starter_code: str
    sample_input: str
    sample_output: str
    public_test_cases: List[TestCase] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Assessment Agent & Session Models (Modules 5 & 6)
# ---------------------------------------------------------------------------

class AssessmentTier:
    NOVICE = "novice"   # Easy challenges, localized logic
    ADEPT = "adept"     # Medium challenges, multi-step algorithms
    MASTER = "master"   # Hard challenges, system design & complex algorithms


class AssessmentTrack:
    VERIFIED = "verified"  # Formal evaluation
    PRACTICE = "practice"  # Skill improvement sandbox (strictly isolated)


class AssessmentGenerateRequest(BaseModel):
    """Request to coordinate and assemble an assessment."""
    tier: str = "novice"           # "novice", "adept", "master"
    track: str = "verified"        # "verified", "practice"
    domain_filter: Optional[str] = None
    preferred_language: str = "python"


class CandidateSubmission(BaseModel):
    """Answer submission for a single question."""
    question_id: str
    submitted_code: str


class AssessmentSubmitRequest(BaseModel):
    """Submission payload for an active assessment."""
    submissions: List[CandidateSubmission]


class QuestionResult(BaseModel):
    """Grading result for an individual question in an assessment."""
    question_id: str
    title: str
    difficulty: str
    domain: str
    passed_tests: int
    total_tests: int
    all_passed: bool
    feedback: str


class AssessmentSessionResponse(BaseModel):
    """Active or generated assessment session."""
    session_id: str
    user_id: uuid.UUID
    tier: str
    track: str
    status: str  # "active", "completed", "expired"
    domain: str
    matched_skills: List[str] = Field(default_factory=list)
    questions: List[QuestionPublic]
    ai_guidance: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class AssessmentSummaryResponse(BaseModel):
    """Final assessment summary report."""
    session_id: str
    user_id: uuid.UUID
    tier: str
    track: str
    status: str
    score_percentage: float
    total_questions: int
    questions_passed: int
    results: List[QuestionResult]
    matched_skills: List[str] = Field(default_factory=list)
    demonstrated_skills: List[str] = Field(default_factory=list)
    skill_gaps: List[str] = Field(default_factory=list)
    created_at: datetime
    completed_at: Optional[datetime] = None
    verification_notice: str


# ---------------------------------------------------------------------------
# Module 7: Coding Workspace & Secure Sandbox Models
# ---------------------------------------------------------------------------

class ExecutionStatus:
    ACCEPTED = "accepted"
    WRONG_ANSWER = "wrong_answer"
    COMPILATION_ERROR = "compilation_error"
    RUNTIME_ERROR = "runtime_error"
    TIME_LIMIT_EXCEEDED = "time_limit_exceeded"
    MEMORY_LIMIT_EXCEEDED = "memory_limit_exceeded"
    SANDBOX_ERROR = "sandbox_error"
    SANDBOX_UNAVAILABLE = "sandbox_unavailable"


class SampleRunRequest(BaseModel):
    """Request payload to test code against sample test cases in isolated sandbox."""
    question_id: str
    submitted_code: str
    custom_input: Optional[str] = None


class SampleRunResponse(BaseModel):
    """Result of running code in sandbox against sample/custom inputs."""
    question_id: str
    status: str
    passed: bool
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    execution_time_ms: Optional[float] = None
    memory_kb: Optional[int] = None
    exit_code: Optional[int] = None
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    error_message: Optional[str] = None
    sandbox_provider: str = "judge0"


# ---------------------------------------------------------------------------
# Module 8: CodeTrace Telemetry & Journey Models
# ---------------------------------------------------------------------------

class CodeTraceEventCreate(BaseModel):
    """Client telemetry event to log."""
    question_id: str
    event_type: str = "snapshot"  # 'snapshot', 'sample_run', 'submission', 'paste_cadence'
    code_snapshot: str
    diff_summary: Optional[Dict[str, Any]] = Field(default_factory=dict)
    metrics: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CodeTraceEventResponse(BaseModel):
    """Recorded CodeTrace event."""
    id: uuid.UUID
    session_id: uuid.UUID
    user_id: uuid.UUID
    question_id: str
    event_type: str
    code_snapshot: str
    diff_summary: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class CodeTraceTimelineResponse(BaseModel):
    """Complete chronological coding journey timeline."""
    session_id: uuid.UUID
    total_events: int
    total_revisions: int
    sample_runs_count: int
    events: List[CodeTraceEventResponse]
    summary: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Module 9: Guarded AI Coding Assistant Models
# ---------------------------------------------------------------------------

class AssistantChatMessage(BaseModel):
    """Sanitized conversation history message for AI Assistant."""
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=2000)


class AssistantHintRequest(BaseModel):
    """Request for progressive problem-solving hints."""
    question_id: str
    current_code: str = Field(default="", max_length=65536)
    hint_level: int = Field(default=1, ge=1, le=3)


class AssistantExplainErrorRequest(BaseModel):
    """Request for conceptual analysis of execution or compiler errors."""
    question_id: str
    current_code: str = Field(default="", max_length=65536)
    error_message: str = Field(..., max_length=4000)


class AssistantChatRequest(BaseModel):
    """Request for guarded conversational problem-solving guidance."""
    question_id: str
    message: str = Field(..., min_length=1, max_length=2000)
    current_code: str = Field(default="", max_length=65536)
    history: List[AssistantChatMessage] = Field(default_factory=list, max_length=10)


class AssistantResponse(BaseModel):
    """Standardized AI Coding Assistant response with safety disclosures."""
    reply: str
    hint_level: Optional[int] = None
    mode: str = "guarded"  # 'guarded' | 'practice'
    is_guarded: bool = True
    source: str = "featherless"  # 'featherless' | 'fallback'
    advisory_notice: str = (
        "AI assistance is advisory and designed to guide your problem-solving. "
        "Complete code solutions and hidden tests are strictly concealed."
    )


# ---------------------------------------------------------------------------
# Module 10: Performance Analytics and Scoring Models
# ---------------------------------------------------------------------------

class TrendPoint(BaseModel):
    """A single data point in the longitudinal performance trend."""
    session_id: str
    date: str                       # ISO date string "YYYY-MM-DD"
    composite_score: float          # 0–100 deterministic composite
    test_score: float               # Test component of score (0–80)
    raw_correctness_pct: float = 0.0 # Pure unweighted test correctness (0–100%)
    ai_efficiency_score: float      # AI usage efficiency component (0–20)
    telemetry_status: str = "unknown" # "self_sufficient" | "assisted" | "unknown"
    tier: str                       # novice | adept | master
    track: str                      # verified | practice
    domain: str
    questions_passed: int
    total_questions: int


class DomainPerformance(BaseModel):
    """Pass/fail performance aggregated by technical domain."""
    domain: str
    sessions: int
    questions_attempted: int
    questions_passed: int
    pass_rate: float                # 0.0–100.0


class SkillMasteryItem(BaseModel):
    """Per-difficulty tier aggregated mastery metrics."""
    tier: str                       # novice | adept | master
    difficulty: str                 # easy | medium | hard
    sessions: int
    avg_composite_score: float
    best_composite_score: float
    total_questions: int
    total_passed: int


class HintUtilizationSummary(BaseModel):
    """Aggregated deterministic AI hint usage efficiency metrics."""
    total_hint_requests: int
    level_1_hints: int
    level_2_hints: int
    level_3_hints: int
    sessions_with_hints: int
    avg_hints_per_session: float
    ai_efficiency_avg: float        # Average AI efficiency score across sessions (0–20)


class AnalyticsResponse(BaseModel):
    """Full student performance analytics report — deterministic, auditable."""
    user_id: str
    generated_at: str               # ISO timestamp
    total_sessions: int
    verified_sessions: int
    practice_sessions: int
    overall_avg_composite: float    # Verified sessions average composite only
    best_composite_score: float     # Verified sessions best composite only
    overall_test_pass_rate: float   # Verified sessions test pass rate (0-100)
    practice_avg_composite: Optional[float] = None # Isolated practice average
    trend: List[TrendPoint]         # Chronological, most-recent last
    domain_performance: List[DomainPerformance]
    skill_mastery: List[SkillMasteryItem]
    hint_utilization: HintUtilizationSummary
    scoring_formula_note: str       # Transparent formula description


# ---------------------------------------------------------------------------
# Module 11: College Task Management Models
# ---------------------------------------------------------------------------

class CollegeTaskStatus:
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"
    ARCHIVED = "archived"


class CollegeTaskTestCase(BaseModel):
    input: str
    expected_output: str
    is_hidden: bool = False


class CollegeTaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5)
    domain: str = Field(..., min_length=2, max_length=100)
    difficulty: str = Field(..., description="easy, medium, hard or novice, adept, master")
    allowed_languages: List[str] = Field(default_factory=lambda: ["python"])
    deadline: Optional[datetime] = None
    duration_minutes: int = Field(default=60, gt=0, le=1440)
    instructions: Optional[str] = None
    starter_code: Optional[str] = "# Write your solution here\n"
    test_cases: List[CollegeTaskTestCase] = Field(default_factory=list)
    status: str = Field(default=CollegeTaskStatus.DRAFT)
    assigned_student_ids: List[uuid.UUID] = Field(default_factory=list)
    allow_late_submissions: bool = False

    @field_validator("difficulty")
    @classmethod
    def validate_diff(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ("easy", "medium", "hard", "novice", "adept", "master"):
            raise ValueError("Difficulty must be one of: easy, medium, hard, novice, adept, master")
        return clean

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ("draft", "published", "closed", "archived"):
            raise ValueError("Status must be one of: draft, published, closed, archived")
        return clean


class CollegeTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    difficulty: Optional[str] = None
    allowed_languages: Optional[List[str]] = None
    deadline: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    instructions: Optional[str] = None
    starter_code: Optional[str] = None
    test_cases: Optional[List[CollegeTaskTestCase]] = None
    status: Optional[str] = None
    assigned_student_ids: Optional[List[uuid.UUID]] = None
    allow_late_submissions: Optional[bool] = None


class CollegeTaskResponse(BaseModel):
    id: uuid.UUID
    college_id: uuid.UUID
    creator_id: uuid.UUID
    title: str
    description: str
    domain: str
    difficulty: str
    allowed_languages: List[str]
    deadline: Optional[datetime] = None
    duration_minutes: int
    instructions: Optional[str] = None
    starter_code: str
    test_cases: List[Dict[str, Any]] = Field(default_factory=list)
    status: str
    assigned_student_ids: List[uuid.UUID] = Field(default_factory=list)
    allow_late_submissions: bool
    created_at: datetime
    updated_at: datetime


class CollegeTaskSubmissionCreate(BaseModel):
    submitted_code: str = Field(..., min_length=1, max_length=65536)
    language: str = Field(default="python")


class CollegeTaskSubmissionResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    student_id: uuid.UUID
    college_id: uuid.UUID
    submitted_code: str
    language: str
    status: str
    score_percentage: float
    tests_passed: int
    total_tests: int
    results: List[Dict[str, Any]] = Field(default_factory=list)
    submitted_at: datetime


class CollegeTaskAnalyticsResponse(BaseModel):
    task_id: uuid.UUID
    title: str
    status: str
    deadline: Optional[datetime] = None
    total_assigned: int
    total_started: int
    total_completed: int
    total_pending: int
    avg_score: float
    pass_rate: float


# ---------------------------------------------------------------------------
# Module 12: Recruiter Portal & Live Interview Models
# ---------------------------------------------------------------------------

class RecruiterConsentToggleRequest(BaseModel):
    recruiter_discoverable: bool


class CandidateDiscoveryItem(BaseModel):
    candidate_id: uuid.UUID
    full_name: str
    college_name: Optional[str] = None
    verified_skills: List[str] = Field(default_factory=list)
    verified_domains: List[str] = Field(default_factory=list)
    verified_avg_score: float = 0.0
    verified_sessions_count: int = 0
    portfolio_claims: List[str] = Field(default_factory=list)  # Explicitly unverified claims
    recruiter_discoverable: bool = True


class CandidateDetailProfileResponse(BaseModel):
    candidate_id: uuid.UUID
    full_name: str
    college_name: Optional[str] = None
    verified_avg_composite: float
    verified_test_pass_rate: float
    verified_sessions_count: int
    verified_skills: List[str]
    domain_mastery: List[DomainPerformance]
    tier_mastery: List[SkillMasteryItem]
    verified_history: List[Dict[str, Any]]  # Date, title, tier, score
    portfolio_claims: List[Dict[str, Any]]  # Projects, tech claims with is_verified=false
    consent_status: bool = True


class InterviewSessionCreate(BaseModel):
    candidate_id: uuid.UUID
    title: str = Field(..., min_length=3, max_length=200)
    scheduled_at: Optional[datetime] = None
    task_description: str = Field(default="")
    initial_code: Optional[str] = "# Live Interview Shared Coding Workspace\n"
    language: str = Field(default="python")


class InterviewSyncRequest(BaseModel):
    code: str = Field(..., max_length=65536)
    status: Optional[str] = None
    client_version: Optional[int] = None


class InterviewChangeRequest(BaseModel):
    requested_change: str = Field(..., min_length=3, max_length=1000)
    instructions: Optional[str] = None


class InterviewFinishRequest(BaseModel):
    feedback: str = Field(..., min_length=1, max_length=2000)
    outcome: str = Field(..., description="passed, needs_review, rejected")

    @field_validator("outcome")
    @classmethod
    def validate_outcome(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ("passed", "needs_review", "rejected"):
            raise ValueError("Outcome must be one of: passed, needs_review, rejected")
        return clean


class InterviewRespondRequest(BaseModel):
    action: Literal["accept", "decline"]


class InterviewSessionResponse(BaseModel):
    id: uuid.UUID
    recruiter_id: uuid.UUID
    candidate_id: uuid.UUID
    title: str
    scheduled_at: datetime
    status: str  # scheduled, in_progress, completed, cancelled
    candidate_accepted: Optional[bool] = None
    task_description: str
    current_code: str
    language: str
    version: int = 1
    last_edited_by: Optional[uuid.UUID] = None
    requested_changes: List[Dict[str, Any]] = Field(default_factory=list)
    feedback: Optional[str] = None
    outcome: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    updated_at: datetime



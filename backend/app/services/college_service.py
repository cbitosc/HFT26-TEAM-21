"""
College Task Management Service (Module 11).

Provides:
  - College task authoring, publishing, closing, and archiving.
  - Multi-student assignment and deadline enforcement.
  - Student task solving and deterministic grading via sandbox.
  - Task-level and cohort-level analytics.
  - Strict multi-tenant isolation: administrators are confined to their own college.
  - Production guard: Local JSON storage disabled in production.
"""

from __future__ import annotations

import os
import json
import uuid
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from fastapi import HTTPException, status

from app.config import get_settings
from app.supabase_client import service_client
from app.models import (
    UserProfile,
    CollegeTaskCreate,
    CollegeTaskUpdate,
    CollegeTaskResponse,
    CollegeTaskSubmissionCreate,
    CollegeTaskSubmissionResponse,
    CollegeTaskAnalyticsResponse,
    CollegeTaskStatus,
)
from app.services.sandbox import get_sandbox_provider

logger = logging.getLogger("skillproof.college")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
TASKS_FILE = os.path.join(DATA_DIR, "college_tasks.json")
SUBMISSIONS_FILE = os.path.join(DATA_DIR, "college_submissions.json")

_tasks_lock = threading.Lock()
_submissions_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Data Access (Supabase primary + Dev fallback)
# ---------------------------------------------------------------------------

def _read_local_tasks() -> Dict[str, Any]:
    if not os.path.exists(TASKS_FILE):
        return {}
    with _tasks_lock:
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}


def _write_local_tasks(data: Dict[str, Any]):
    os.makedirs(DATA_DIR, exist_ok=True)
    with _tasks_lock:
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)


def _read_local_submissions() -> List[Dict[str, Any]]:
    if not os.path.exists(SUBMISSIONS_FILE):
        return []
    with _submissions_lock:
        try:
            with open(SUBMISSIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []


def _write_local_submissions(data: List[Dict[str, Any]]):
    os.makedirs(DATA_DIR, exist_ok=True)
    with _submissions_lock:
        with open(SUBMISSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# Administrator Task Operations
# ---------------------------------------------------------------------------

def create_college_task(admin: UserProfile, payload: CollegeTaskCreate) -> CollegeTaskResponse:
    """Creates a new coding assessment task for the administrator's college."""
    if not admin.college_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="College administrator profile has no associated college_id.",
        )

    task_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    task_dict = {
        "id": str(task_id),
        "college_id": str(admin.college_id),
        "creator_id": str(admin.id),
        "title": payload.title.strip(),
        "description": payload.description.strip(),
        "domain": payload.domain.strip(),
        "difficulty": payload.difficulty,
        "allowed_languages": payload.allowed_languages,
        "deadline": payload.deadline.isoformat() if payload.deadline else None,
        "duration_minutes": payload.duration_minutes,
        "instructions": payload.instructions or "",
        "starter_code": payload.starter_code or "# Write your solution here\n",
        "test_cases": [tc.model_dump() for tc in payload.test_cases],
        "status": payload.status,
        "assigned_student_ids": [str(sid) for sid in payload.assigned_student_ids],
        "allow_late_submissions": payload.allow_late_submissions,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    settings = get_settings()
    if settings.is_supabase_configured:
        try:
            client = service_client()
            client.table("college_tasks").insert(task_dict).execute()
        except Exception as e:
            logger.warning("Could not persist college task to Supabase: %s", e)
            if settings.app_env == "production":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database unavailable in production mode.",
                )

    if settings.app_env != "production":
        tasks = _read_local_tasks()
        tasks[str(task_id)] = task_dict
        _write_local_tasks(tasks)

    return _dict_to_task_response(task_dict)


def list_college_tasks(admin: UserProfile, status_filter: Optional[str] = None) -> List[CollegeTaskResponse]:
    """Lists all tasks belonging to the administrator's college."""
    if not admin.college_id:
        return []

    settings = get_settings()
    cid_str = str(admin.college_id)
    raw_tasks: List[Dict[str, Any]] = []

    if settings.is_supabase_configured:
        try:
            client = service_client()
            q = client.table("college_tasks").select("*").eq("college_id", cid_str)
            if status_filter:
                q = q.eq("status", status_filter)
            res = q.order("created_at", desc=True).execute()
            if res.data:
                raw_tasks = res.data
        except Exception as e:
            logger.warning("Supabase college_tasks query failed: %s", e)
            if settings.app_env == "production":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database unavailable in production mode.",
                )

    if not raw_tasks and settings.app_env != "production":
        all_local = _read_local_tasks()
        raw_tasks = [
            t for t in all_local.values()
            if t.get("college_id") == cid_str
            and (not status_filter or t.get("status") == status_filter)
        ]
        raw_tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return [_dict_to_task_response(t) for t in raw_tasks]


def get_college_task(admin_or_student: UserProfile, task_id: uuid.UUID) -> CollegeTaskResponse:
    """Retrieves a single task verifying authorization boundaries."""
    tid_str = str(task_id)
    raw = _fetch_raw_task(tid_str)
    if not raw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    # Authorization
    if admin_or_student.role == "college_admin":
        if str(admin_or_student.college_id) != raw.get("college_id"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access tasks from another college.")
    elif admin_or_student.role == "student":
        # Students can only access published/closed tasks assigned to them or their college
        if raw.get("status") not in ("published", "closed"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Task is not available to students.")
        assigned_ids = raw.get("assigned_student_ids") or []
        student_id_str = str(admin_or_student.id)
        is_same_college = (admin_or_student.college_id and str(admin_or_student.college_id) == raw.get("college_id"))
        is_assigned = (not assigned_ids) or (student_id_str in assigned_ids)
        if not (is_same_college and is_assigned):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Task is not assigned to you.")

    return _dict_to_task_response(raw)


def update_college_task_status(admin: UserProfile, task_id: uuid.UUID, new_status: str) -> CollegeTaskResponse:
    """Transitions task status (draft, published, closed, archived)."""
    clean_status = new_status.strip().lower()
    if clean_status not in ("draft", "published", "closed", "archived"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task status.")

    tid_str = str(task_id)
    raw = _fetch_raw_task(tid_str)
    if not raw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    if str(admin.college_id) != raw.get("college_id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot edit tasks from another college.")

    now = datetime.now(timezone.utc).isoformat()
    raw["status"] = clean_status
    raw["updated_at"] = now

    _save_raw_task(raw)
    return _dict_to_task_response(raw)


def assign_students_to_task(admin: UserProfile, task_id: uuid.UUID, student_ids: List[uuid.UUID]) -> CollegeTaskResponse:
    """Assigns specific students to a college task."""
    tid_str = str(task_id)
    raw = _fetch_raw_task(tid_str)
    if not raw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    if str(admin.college_id) != raw.get("college_id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot assign tasks from another college.")

    sid_strings = [str(sid) for sid in student_ids]
    current = set(raw.get("assigned_student_ids") or [])
    current.update(sid_strings)
    raw["assigned_student_ids"] = list(current)
    raw["updated_at"] = datetime.now(timezone.utc).isoformat()

    _save_raw_task(raw)
    return _dict_to_task_response(raw)


def get_task_analytics(admin: UserProfile, task_id: uuid.UUID) -> CollegeTaskAnalyticsResponse:
    """Computes task statistics (assigned, started, completed, avg score, pass rate)."""
    task = get_college_task(admin, task_id)
    tid_str = str(task_id)

    submissions = _get_task_submissions(tid_str)
    completed_subs = [s for s in submissions if s.get("status") in ("submitted", "graded")]

    assigned_count = len(task.assigned_student_ids) if task.assigned_student_ids else len(submissions)
    total_completed = len(completed_subs)
    total_started = len(submissions)
    total_pending = max(0, assigned_count - total_completed)

    scores = [s.get("score_percentage", 0.0) for s in completed_subs]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    passed_count = sum(1 for s in completed_subs if s.get("score_percentage", 0.0) >= 70.0)
    pass_rate = round((passed_count / total_completed * 100), 1) if total_completed > 0 else 0.0

    return CollegeTaskAnalyticsResponse(
        task_id=task.id,
        title=task.title,
        status=task.status,
        deadline=task.deadline,
        total_assigned=assigned_count,
        total_started=total_started,
        total_completed=total_completed,
        total_pending=total_pending,
        avg_score=avg_score,
        pass_rate=pass_rate,
    )


# ---------------------------------------------------------------------------
# Student Task Solving & Execution
# ---------------------------------------------------------------------------

def list_assigned_tasks_for_student(student: UserProfile) -> List[CollegeTaskResponse]:
    """Returns published/closed tasks assigned to the student or student's college."""
    settings = get_settings()
    student_id_str = str(student.id)
    college_id_str = str(student.college_id) if student.college_id else None

    raw_tasks: List[Dict[str, Any]] = []

    if settings.is_supabase_configured:
        try:
            client = service_client()
            q = client.table("college_tasks").select("*").in_("status", ["published", "closed"])
            res = q.order("created_at", desc=True).execute()
            if res.data:
                for t in res.data:
                    assigned = t.get("assigned_student_ids") or []
                    is_same_college = bool(college_id_str and t.get("college_id") == college_id_str)
                    is_eligible = is_same_college and (not assigned or student_id_str in assigned)
                    if is_eligible:
                        raw_tasks.append(t)
        except Exception as e:
            logger.warning("Supabase student tasks query failed: %s", e)
            if settings.app_env == "production":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database unavailable in production mode.",
                )

    if not raw_tasks and settings.app_env != "production":
        all_local = _read_local_tasks()
        for t in all_local.values():
            if t.get("status") in ("published", "closed"):
                assigned = t.get("assigned_student_ids") or []
                is_same_college = bool(college_id_str and t.get("college_id") == college_id_str)
                is_eligible = is_same_college and (not assigned or student_id_str in assigned)
                if is_eligible:
                    raw_tasks.append(t)
        raw_tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return [_dict_to_task_response(t) for t in raw_tasks]


def submit_college_task(
    student: UserProfile,
    task_id: uuid.UUID,
    payload: CollegeTaskSubmissionCreate,
) -> CollegeTaskSubmissionResponse:
    """
    Submits and deterministically evaluates a student's solution to an assigned task.
    Enforces deadline rules, runs tests via sandbox, and records the submission.
    """
    task = get_college_task(student, task_id)

    # Status check
    if task.status != "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task is '{task.status}'. Submissions are only accepted for 'published' tasks.",
        )

    # Deadline enforcement
    now = datetime.now(timezone.utc)
    if task.deadline and task.deadline < now and not task.allow_late_submissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task submission deadline ({task.deadline.isoformat()}) has passed.",
        )

    # Deterministic Evaluation
    test_cases = task.test_cases or []
    tests_passed = 0
    results: List[Dict[str, Any]] = []

    sandbox = get_sandbox_provider()
    for idx, tc in enumerate(test_cases):
        inp = tc.get("input", "")
        exp = tc.get("expected_output", "").strip()

        exec_res = sandbox.execute(
            source_code=payload.submitted_code,
            language=payload.language,
            stdin=inp,
            timeout_seconds=5.0,
        )

        actual = (exec_res.stdout or "").strip()
        passed = (exec_res.status == "accepted" and actual == exp)
        if passed:
            tests_passed += 1

        exec_time_ms = round(exec_res.time_seconds * 1000, 2) if exec_res.time_seconds else None

        results.append({
            "test_case_index": idx + 1,
            "passed": passed,
            "status": exec_res.status,
            "execution_time_ms": exec_time_ms,
            "expected_output": exp,
            "actual_output": actual if not tc.get("is_hidden") else ("Hidden" if not passed else actual),
        })

    total_tests = len(test_cases)
    score_pct = round((tests_passed / total_tests * 100), 1) if total_tests > 0 else 100.0

    sub_id = uuid.uuid4()
    sub_dict = {
        "id": str(sub_id),
        "task_id": str(task_id),
        "student_id": str(student.id),
        "college_id": str(task.college_id),
        "submitted_code": payload.submitted_code,
        "language": payload.language,
        "status": "submitted",
        "score_percentage": score_pct,
        "tests_passed": tests_passed,
        "total_tests": total_tests,
        "results": results,
        "submitted_at": now.isoformat(),
    }

    settings = get_settings()
    if settings.is_supabase_configured:
        try:
            client = service_client()
            client.table("college_task_submissions").insert(sub_dict).execute()
        except Exception as e:
            logger.warning("Could not persist college task submission to Supabase: %s", e)
            if settings.app_env == "production":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database unavailable in production mode.",
                )

    if settings.app_env != "production":
        subs = _read_local_submissions()
        subs.append(sub_dict)
        _write_local_submissions(subs)

    return CollegeTaskSubmissionResponse(
        id=sub_id,
        task_id=task_id,
        student_id=student.id,
        college_id=task.college_id,
        submitted_code=payload.submitted_code,
        language=payload.language,
        status="submitted",
        score_percentage=score_pct,
        tests_passed=tests_passed,
        total_tests=total_tests,
        results=results,
        submitted_at=now,
    )


def get_student_task_submissions(student: UserProfile, task_id: uuid.UUID) -> List[CollegeTaskSubmissionResponse]:
    """Returns past submissions for this student on the specified task."""
    tid_str = str(task_id)
    sid_str = str(student.id)
    subs = _get_task_submissions(tid_str)
    student_subs = [s for s in subs if s.get("student_id") == sid_str]

    return [
        CollegeTaskSubmissionResponse(
            id=uuid.UUID(str(s["id"])),
            task_id=uuid.UUID(str(s["task_id"])),
            student_id=uuid.UUID(str(s["student_id"])),
            college_id=uuid.UUID(str(s["college_id"])),
            submitted_code=s["submitted_code"],
            language=s.get("language", "python"),
            status=s.get("status", "submitted"),
            score_percentage=s.get("score_percentage", 0.0),
            tests_passed=s.get("tests_passed", 0),
            total_tests=s.get("total_tests", 0),
            results=s.get("results") or [],
            submitted_at=datetime.fromisoformat(s["submitted_at"]) if isinstance(s["submitted_at"], str) else s["submitted_at"],
        )
        for s in student_subs
    ]


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _fetch_raw_task(task_id_str: str) -> Optional[Dict[str, Any]]:
    settings = get_settings()
    if settings.is_supabase_configured:
        try:
            client = service_client()
            res = client.table("college_tasks").select("*").eq("id", task_id_str).single().execute()
            if res.data:
                return res.data
        except Exception:
            pass

    if settings.app_env != "production":
        tasks = _read_local_tasks()
        return tasks.get(task_id_str)
    return None


def _save_raw_task(raw: Dict[str, Any]):
    settings = get_settings()
    tid_str = raw["id"]
    if settings.is_supabase_configured:
        try:
            client = service_client()
            client.table("college_tasks").upsert(raw).execute()
        except Exception as e:
            logger.warning("Supabase task upsert failed: %s", e)
            if settings.app_env == "production":
                raise HTTPException(status_code=503, detail="Database unavailable in production.")

    if settings.app_env != "production":
        tasks = _read_local_tasks()
        tasks[tid_str] = raw
        _write_local_tasks(tasks)


def _get_task_submissions(task_id_str: str) -> List[Dict[str, Any]]:
    settings = get_settings()
    if settings.is_supabase_configured:
        try:
            client = service_client()
            res = client.table("college_task_submissions").select("*").eq("task_id", task_id_str).execute()
            if res.data:
                return res.data
        except Exception:
            pass

    if settings.app_env != "production":
        all_subs = _read_local_submissions()
        return [s for s in all_subs if s.get("task_id") == task_id_str]
    return []


def _dict_to_task_response(t: Dict[str, Any]) -> CollegeTaskResponse:
    dt = datetime.fromisoformat(t["created_at"]) if isinstance(t["created_at"], str) else t["created_at"]
    up_dt = datetime.fromisoformat(t["updated_at"]) if isinstance(t["updated_at"], str) else t["updated_at"]
    dl = datetime.fromisoformat(t["deadline"]) if t.get("deadline") and isinstance(t["deadline"], str) else t.get("deadline")

    assigned = [
        uuid.UUID(str(sid)) for sid in (t.get("assigned_student_ids") or [])
    ]

    return CollegeTaskResponse(
        id=uuid.UUID(str(t["id"])),
        college_id=uuid.UUID(str(t["college_id"])),
        creator_id=uuid.UUID(str(t["creator_id"])),
        title=t["title"],
        description=t["description"],
        domain=t["domain"],
        difficulty=t["difficulty"],
        allowed_languages=t.get("allowed_languages") or ["python"],
        deadline=dl,
        duration_minutes=t.get("duration_minutes", 60),
        instructions=t.get("instructions"),
        starter_code=t.get("starter_code", "# Write your solution here\n"),
        test_cases=t.get("test_cases") or [],
        status=t.get("status", "draft"),
        assigned_student_ids=assigned,
        allow_late_submissions=t.get("allow_late_submissions", False),
        created_at=dt,
        updated_at=up_dt,
    )

"""
FastAPI Routes for College Task Management (Module 11).

Endpoints:
  - Admin: Create, list, edit, status transition, student assignment, and task analytics.
  - Student: List assigned tasks, view task details, submit solutions, and review history.
  - Role enforcement: Admin routes require college_admin; student routes require student.
"""

from __future__ import annotations

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status

from app.api.deps import require_role
from app.models import (
    UserProfile,
    CollegeTaskCreate,
    CollegeTaskResponse,
    CollegeTaskSubmissionCreate,
    CollegeTaskSubmissionResponse,
    CollegeTaskAnalyticsResponse,
)
from app.services import college_service

router = APIRouter()


# ---------------------------------------------------------------------------
# College Administrator Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/tasks",
    response_model=CollegeTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new college task (Admin only)",
)
def create_task(
    payload: CollegeTaskCreate,
    admin: UserProfile = Depends(require_role("college_admin")),
):
    return college_service.create_college_task(admin, payload)


@router.get(
    "/tasks",
    response_model=List[CollegeTaskResponse],
    summary="List all tasks for the administrator's college",
)
def list_tasks(
    status: Optional[str] = None,
    admin: UserProfile = Depends(require_role("college_admin")),
):
    return college_service.list_college_tasks(admin, status_filter=status)


@router.get(
    "/tasks/{task_id}",
    response_model=CollegeTaskResponse,
    summary="Get college task details",
)
def get_task(
    task_id: uuid.UUID,
    user: UserProfile = Depends(require_role("college_admin", "student")),
):
    return college_service.get_college_task(user, task_id)


@router.put(
    "/tasks/{task_id}/status",
    response_model=CollegeTaskResponse,
    summary="Change task status (draft, published, closed, archived)",
)
def update_task_status(
    task_id: uuid.UUID,
    new_status: str,
    admin: UserProfile = Depends(require_role("college_admin")),
):
    return college_service.update_college_task_status(admin, task_id, new_status)


@router.post(
    "/tasks/{task_id}/assign",
    response_model=CollegeTaskResponse,
    summary="Assign task to specific students",
)
def assign_students(
    task_id: uuid.UUID,
    student_ids: List[uuid.UUID],
    admin: UserProfile = Depends(require_role("college_admin")),
):
    return college_service.assign_students_to_task(admin, task_id, student_ids)


@router.get(
    "/tasks/{task_id}/analytics",
    response_model=CollegeTaskAnalyticsResponse,
    summary="Get task-level completion and score analytics",
)
def get_task_analytics(
    task_id: uuid.UUID,
    admin: UserProfile = Depends(require_role("college_admin")),
):
    return college_service.get_task_analytics(admin, task_id)


# ---------------------------------------------------------------------------
# Student Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/my-tasks",
    response_model=List[CollegeTaskResponse],
    summary="List college tasks assigned to the current student",
)
def list_my_assigned_tasks(
    student: UserProfile = Depends(require_role("student")),
):
    return college_service.list_assigned_tasks_for_student(student)


@router.post(
    "/my-tasks/{task_id}/submit",
    response_model=CollegeTaskSubmissionResponse,
    summary="Submit and evaluate a solution for an assigned task",
)
def submit_task(
    task_id: uuid.UUID,
    payload: CollegeTaskSubmissionCreate,
    student: UserProfile = Depends(require_role("student")),
):
    return college_service.submit_college_task(student, task_id, payload)


@router.get(
    "/my-tasks/{task_id}/submissions",
    response_model=List[CollegeTaskSubmissionResponse],
    summary="Get previous submissions for this task",
)
def get_my_submissions(
    task_id: uuid.UUID,
    student: UserProfile = Depends(require_role("student")),
):
    return college_service.get_student_task_submissions(student, task_id)

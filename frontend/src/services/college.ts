/**
 * API service for Module 11: College Task Management
 */

import {
  CollegeTaskCreate,
  CollegeTaskResponse,
  CollegeTaskSubmissionCreate,
  CollegeTaskSubmissionResponse,
  CollegeTaskAnalyticsResponse,
} from '../types/college';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function getAuthHeaders(token: string) {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
}

export async function createCollegeTask(
  token: string,
  payload: CollegeTaskCreate,
): Promise<CollegeTaskResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/college/tasks`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to create college task.');
  }
  return resp.json();
}

export async function listCollegeTasks(
  token: string,
  statusFilter?: string,
): Promise<CollegeTaskResponse[]> {
  const url = new URL(`${API_BASE_URL}/api/college/tasks`);
  if (statusFilter) url.searchParams.set('status', statusFilter);

  const resp = await fetch(url.toString(), {
    headers: getAuthHeaders(token),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to list college tasks.');
  }
  return resp.json();
}

export async function getCollegeTask(
  token: string,
  taskId: string,
): Promise<CollegeTaskResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/college/tasks/${taskId}`, {
    headers: getAuthHeaders(token),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to retrieve college task.');
  }
  return resp.json();
}

export async function updateCollegeTaskStatus(
  token: string,
  taskId: string,
  newStatus: string,
): Promise<CollegeTaskResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/college/tasks/${taskId}/status?new_status=${newStatus}`, {
    method: 'PUT',
    headers: getAuthHeaders(token),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to update task status.');
  }
  return resp.json();
}

export async function getTaskAnalytics(
  token: string,
  taskId: string,
): Promise<CollegeTaskAnalyticsResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/college/tasks/${taskId}/analytics`, {
    headers: getAuthHeaders(token),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch task analytics.');
  }
  return resp.json();
}

export async function listMyAssignedTasks(
  token: string,
): Promise<CollegeTaskResponse[]> {
  const resp = await fetch(`${API_BASE_URL}/api/college/my-tasks`, {
    headers: getAuthHeaders(token),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch assigned tasks.');
  }
  return resp.json();
}

export async function submitCollegeTask(
  token: string,
  taskId: string,
  payload: CollegeTaskSubmissionCreate,
): Promise<CollegeTaskSubmissionResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/college/my-tasks/${taskId}/submit`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to submit college task.');
  }
  return resp.json();
}

export async function getMyTaskSubmissions(
  token: string,
  taskId: string,
): Promise<CollegeTaskSubmissionResponse[]> {
  const resp = await fetch(`${API_BASE_URL}/api/college/my-tasks/${taskId}/submissions`, {
    headers: getAuthHeaders(token),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch submissions.');
  }
  return resp.json();
}

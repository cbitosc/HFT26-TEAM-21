/**
 * API service for Module 12: Recruiter Portal & Live Interviews
 */

import {
  CandidateDiscoveryItem,
  CandidateDetailProfileResponse,
  InterviewSessionCreate,
  InterviewSessionResponse,
} from '../types/recruiter';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function getAuthHeaders(token: string) {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
}

export async function getStudentConsent(token: string): Promise<boolean> {
  const resp = await fetch(`${API_BASE_URL}/api/recruiter/consent`, {
    headers: getAuthHeaders(token),
  });
  if (!resp.ok) return false;
  const data = await resp.json();
  return Boolean(data.recruiter_discoverable);
}

export async function updateStudentConsent(token: string, discoverable: boolean): Promise<boolean> {
  const resp = await fetch(`${API_BASE_URL}/api/recruiter/consent`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ recruiter_discoverable: discoverable }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to update consent.');
  }
  const data = await resp.json();
  return Boolean(data.recruiter_discoverable);
}

export async function searchCandidates(
  token: string,
  filters?: { domain?: string; skill?: string; minScore?: number },
): Promise<CandidateDiscoveryItem[]> {
  const url = new URL(`${API_BASE_URL}/api/recruiter/candidates`);
  if (filters?.domain) url.searchParams.set('domain', filters.domain);
  if (filters?.skill) url.searchParams.set('skill', filters.skill);
  if (filters?.minScore !== undefined) url.searchParams.set('min_score', filters.minScore.toString());

  const resp = await fetch(url.toString(), {
    headers: getAuthHeaders(token),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to discover candidates.');
  }
  return resp.json();
}

export async function getCandidateDossier(
  token: string,
  candidateId: string,
): Promise<CandidateDetailProfileResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/recruiter/candidates/${candidateId}`, {
    headers: getAuthHeaders(token),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch candidate dossier.');
  }
  return resp.json();
}

export async function createInterview(
  token: string,
  payload: InterviewSessionCreate,
): Promise<InterviewSessionResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/recruiter/interviews`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to schedule interview.');
  }
  return resp.json();
}

export async function listRecruiterInterviews(token: string): Promise<InterviewSessionResponse[]> {
  const resp = await fetch(`${API_BASE_URL}/api/recruiter/interviews`, {
    headers: getAuthHeaders(token),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to list interviews.');
  }
  return resp.json();
}

export async function listMyInterviews(token: string): Promise<InterviewSessionResponse[]> {
  const resp = await fetch(`${API_BASE_URL}/api/recruiter/my-interviews`, {
    headers: getAuthHeaders(token),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to list student interviews.');
  }
  return resp.json();
}

export async function getInterview(
  token: string,
  sessionId: string,
): Promise<InterviewSessionResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/recruiter/interviews/${sessionId}`, {
    headers: getAuthHeaders(token),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to retrieve interview session.');
  }
  return resp.json();
}

export async function syncInterview(
  token: string,
  sessionId: string,
  code: string,
  status?: string,
  clientVersion?: number,
): Promise<InterviewSessionResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/recruiter/interviews/${sessionId}/sync`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ code, status, client_version: clientVersion }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to sync interview workspace.');
  }
  return resp.json();
}

export async function requestInterviewChange(
  token: string,
  sessionId: string,
  requestedChange: string,
  instructions?: string,
): Promise<InterviewSessionResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/recruiter/interviews/${sessionId}/request-change`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ requested_change: requestedChange, instructions }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to request code change.');
  }
  return resp.json();
}

export async function executeInterviewSandbox(
  token: string,
  sessionId: string,
  customInput?: string,
): Promise<{ status: string; passed: boolean; stdout?: string; stderr?: string; compile_output?: string; execution_time_ms?: number }> {
  const url = new URL(`${API_BASE_URL}/api/recruiter/interviews/${sessionId}/execute`);
  if (customInput) url.searchParams.set('custom_input', customInput);

  const resp = await fetch(url.toString(), {
    method: 'POST',
    headers: getAuthHeaders(token),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to execute interview code in sandbox.');
  }
  return resp.json();
}

export async function respondToInterview(
  token: string,
  sessionId: string,
  action: 'accept' | 'decline',
): Promise<InterviewSessionResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/recruiter/interviews/${sessionId}/respond`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ action }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to respond to interview invitation.');
  }
  return resp.json();
}

export async function finishInterview(
  token: string,
  sessionId: string,
  feedback: string,
  outcome: 'passed' | 'needs_review' | 'rejected',
): Promise<InterviewSessionResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/recruiter/interviews/${sessionId}/finish`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ feedback, outcome }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to finish interview.');
  }
  return resp.json();
}

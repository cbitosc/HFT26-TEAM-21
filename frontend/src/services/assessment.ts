/**
 * Assessment API client service (Modules 4, 5, 6).
 */

import { config } from '../config/env';
import {
  AssessmentGenerateParams,
  AssessmentSessionResponse,
  AssessmentSummaryResponse,
  CandidateSubmission,
  QuestionPublic,
  SampleRunRequest,
  SampleRunResponse,
  CodeTraceEventCreate,
  CodeTraceEvent,
  CodeTraceTimelineResponse,
  AssistantHintRequest,
  AssistantExplainErrorRequest,
  AssistantChatRequest,
  AssistantResponse,
  AnalyticsResponse,
} from '../types/assessment';

export async function generateAssessment(
  params: AssessmentGenerateParams,
  accessToken: string
): Promise<AssessmentSessionResponse> {
  const url = `${config.apiBaseUrl}/api/assessment/generate`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to generate assessment (HTTP ${response.status})`);
  }

  return response.json();
}

export async function fetchAssessmentSession(
  sessionId: string,
  accessToken: string
): Promise<AssessmentSessionResponse> {
  const url = `${config.apiBaseUrl}/api/assessment/session/${sessionId}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch assessment session (HTTP ${response.status})`);
  }

  return response.json();
}

export async function submitAssessment(
  sessionId: string,
  submissions: CandidateSubmission[],
  accessToken: string
): Promise<AssessmentSummaryResponse> {
  const url = `${config.apiBaseUrl}/api/assessment/session/${sessionId}/submit`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ submissions }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to submit assessment (HTTP ${response.status})`);
  }

  return response.json();
}

export async function fetchAssessmentHistory(accessToken: string): Promise<any[]> {
  const url = `${config.apiBaseUrl}/api/assessment/history`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    return [];
  }

  return response.json();
}

export async function fetchQuestions(
  accessToken: string,
  filters?: { difficulty?: string; domain?: string }
): Promise<QuestionPublic[]> {
  const query = new URLSearchParams();
  if (filters?.difficulty) query.append('difficulty', filters.difficulty);
  if (filters?.domain) query.append('domain', filters.domain);

  const url = `${config.apiBaseUrl}/api/assessment/questions?${query.toString()}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    return [];
  }

  return response.json();
}

// ---------------------------------------------------------------------------
// Module 7: Execute Sample Run (Isolated Sandbox)
// ---------------------------------------------------------------------------

export async function executeSampleRun(
  sessionId: string,
  params: SampleRunRequest,
  accessToken: string
): Promise<SampleRunResponse> {
  const url = `${config.apiBaseUrl}/api/assessment/session/${sessionId}/run-sample`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to run sample code (HTTP ${response.status})`);
  }

  return response.json();
}

// ---------------------------------------------------------------------------
// Module 8: CodeTrace Telemetry
// ---------------------------------------------------------------------------

export async function logCodeTraceEvent(
  sessionId: string,
  event: CodeTraceEventCreate,
  accessToken: string
): Promise<CodeTraceEvent> {
  const url = `${config.apiBaseUrl}/api/assessment/session/${sessionId}/codetrace`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(event),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to log CodeTrace event (HTTP ${response.status})`);
  }

  return response.json();
}

export async function fetchCodeTraceTimeline(
  sessionId: string,
  accessToken: string
): Promise<CodeTraceTimelineResponse> {
  const url = `${config.apiBaseUrl}/api/assessment/session/${sessionId}/codetrace`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to load CodeTrace timeline (HTTP ${response.status})`);
  }

  return response.json();
}

// ---------------------------------------------------------------------------
// Module 9: Guarded AI Coding Assistant
// ---------------------------------------------------------------------------

export async function requestAssistantHint(
  sessionId: string,
  params: AssistantHintRequest,
  accessToken: string
): Promise<AssistantResponse> {
  const url = `${config.apiBaseUrl}/api/assessment/session/${sessionId}/assistant/hint`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(params),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Assistant hint failed (HTTP ${response.status})`);
  }
  return response.json();
}

export async function requestErrorExplanation(
  sessionId: string,
  params: AssistantExplainErrorRequest,
  accessToken: string
): Promise<AssistantResponse> {
  const url = `${config.apiBaseUrl}/api/assessment/session/${sessionId}/assistant/explain-error`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(params),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Error explanation failed (HTTP ${response.status})`);
  }
  return response.json();
}

export async function requestAssistantChat(
  sessionId: string,
  params: AssistantChatRequest,
  accessToken: string
): Promise<AssistantResponse> {
  const url = `${config.apiBaseUrl}/api/assessment/session/${sessionId}/assistant/chat`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(params),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Assistant chat failed (HTTP ${response.status})`);
  }
  return response.json();
}


// ---------------------------------------------------------------------------
// Module 10: Performance Analytics
// ---------------------------------------------------------------------------

export async function fetchAnalytics(accessToken: string): Promise<AnalyticsResponse> {
  const url = `${config.apiBaseUrl}/api/assessment/analytics`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Accept': 'application/json',
    },
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to load analytics (HTTP ${response.status})`);
  }
  return response.json();
}

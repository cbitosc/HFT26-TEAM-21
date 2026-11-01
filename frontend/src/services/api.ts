import { config } from '../config/env';

export interface HealthResponse {
  name: string;
  status: string;
  message: string;
  environment: string;
  version: string;
}

export type ConnectionState = 'loading' | 'connected' | 'disconnected';

export interface HealthCheckResult {
  state: ConnectionState;
  data: HealthResponse | null;
  error: string | null;
  checkedAt: Date;
}

/**
 * Checks the connectivity and health status of the FastAPI backend service.
 * Aborts smoothly after a 5-second timeout if unreachable.
 */
export async function checkBackendHealth(): Promise<HealthCheckResult> {
  const url = `${config.apiBaseUrl}/api/health`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status} ${response.statusText}`);
    }

    const data: HealthResponse = await response.json();
    return {
      state: 'connected',
      data,
      error: null,
      checkedAt: new Date(),
    };
  } catch (err: unknown) {
    clearTimeout(timeoutId);
    let errorMessage = 'Could not reach backend service';
    if (err instanceof Error) {
      errorMessage = err.name === 'AbortError' ? 'Connection timed out (5s)' : err.message;
    }
    return {
      state: 'disconnected',
      data: null,
      error: errorMessage,
      checkedAt: new Date(),
    };
  }
}

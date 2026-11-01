/**
 * Portfolio API client service for SkillProof AI (Module 3).
 * Interacts with FastAPI /api/portfolio endpoints using the student's access token.
 */

import { config } from '../config/env';
import { PortfolioResponse, PortfolioStructure } from '../types/portfolio';

export async function fetchStudentPortfolio(accessToken: string): Promise<PortfolioResponse | null> {
  const url = `${config.apiBaseUrl}/api/portfolio/me`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Accept': 'application/json',
    },
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch portfolio (HTTP ${response.status})`);
  }

  return response.json();
}

export async function uploadStudentPortfolio(
  file: File,
  accessToken: string
): Promise<PortfolioResponse> {
  const url = `${config.apiBaseUrl}/api/portfolio/upload`;
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload failed (HTTP ${response.status})`);
  }

  return response.json();
}

export async function confirmStudentPortfolio(
  data: PortfolioStructure,
  accessToken: string
): Promise<PortfolioResponse> {
  const url = `${config.apiBaseUrl}/api/portfolio/confirm`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ data }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Confirmation failed (HTTP ${response.status})`);
  }

  return response.json();
}

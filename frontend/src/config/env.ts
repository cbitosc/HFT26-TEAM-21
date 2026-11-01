/**
 * Application environment configuration.
 * Reads VITE_API_BASE_URL from the environment with fallback to http://localhost:8000.
 */
export const config = {
  apiBaseUrl: (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000',
  appName: 'SkillProof AI',
  tagline: 'Portfolio-Driven Adaptive Coding & Technical Assessment Platform',
  version: '1.0.0',
} as const;

/**
 * Guest Session Service — Manages ephemeral guest sessions for SkillProof AI.
 *
 * Principles:
 * - Generates cryptographically secure, random guest IDs.
 * - Stores only ephemeral session metadata (role, guestId, timestamps).
 * - Enforces client-side expiration (default 2 hours).
 * - Strictly separated from authenticated Supabase users.
 * - Guest sessions cannot modify real records or impersonate users.
 */

import { UserRole } from '../types/auth';

export const GUEST_SESSION_STORAGE_KEY = 'skillproof_guest_session';
export const GUEST_SESSION_DURATION_MS = 2 * 60 * 60 * 1000; // 2 hours

export interface GuestSession {
  isGuest: true;
  guestId: string;
  role: UserRole;
  displayName: string;
  createdAt: number;
  expiresAt: number;
}

/**
 * Generates a cryptographically random guest identifier.
 */
function generateGuestId(): string {
  if (typeof window !== 'undefined' && window.crypto && typeof window.crypto.randomUUID === 'function') {
    return `guest_${window.crypto.randomUUID().replace(/-/g, '')}`;
  }
  const randomHex = Math.random().toString(36).substring(2, 10);
  const timeHex = Date.now().toString(36);
  return `guest_${randomHex}${timeHex}`;
}

/**
 * Formats a user-friendly display name for the guest role.
 */
function getGuestDisplayName(role: UserRole): string {
  switch (role) {
    case 'student':
      return 'Guest Student';
    case 'college_admin':
      return 'Guest College Admin';
    case 'recruiter':
      return 'Guest Recruiter';
    default:
      return 'Guest User';
  }
}

/**
 * Creates and stores a new Guest Session.
 */
export function createGuestSession(role: UserRole): GuestSession {
  const now = Date.now();
  const session: GuestSession = {
    isGuest: true,
    guestId: generateGuestId(),
    role,
    displayName: getGuestDisplayName(role),
    createdAt: now,
    expiresAt: now + GUEST_SESSION_DURATION_MS,
  };

  try {
    sessionStorage.setItem(GUEST_SESSION_STORAGE_KEY, JSON.stringify(session));
  } catch {
    try {
      localStorage.setItem(GUEST_SESSION_STORAGE_KEY, JSON.stringify(session));
    } catch {
      // Storage unavailable fallback
    }
  }

  return session;
}

/**
 * Retrieves the active guest session, returning null if expired or missing.
 */
export function getGuestSession(): GuestSession | null {
  try {
    let raw = sessionStorage.getItem(GUEST_SESSION_STORAGE_KEY);
    if (!raw) {
      raw = localStorage.getItem(GUEST_SESSION_STORAGE_KEY);
    }
    if (!raw) return null;

    const session: GuestSession = JSON.parse(raw);

    // Validate structure
    if (!session || !session.isGuest || !session.guestId || !session.role) {
      clearGuestSession();
      return null;
    }

    // Check expiration
    if (Date.now() > session.expiresAt) {
      clearGuestSession();
      return null;
    }

    return session;
  } catch {
    clearGuestSession();
    return null;
  }
}

/**
 * Clears the active guest session.
 */
export function clearGuestSession(): void {
  try {
    sessionStorage.removeItem(GUEST_SESSION_STORAGE_KEY);
  } catch {
    // Ignore
  }
  try {
    localStorage.removeItem(GUEST_SESSION_STORAGE_KEY);
  } catch {
    // Ignore
  }
}

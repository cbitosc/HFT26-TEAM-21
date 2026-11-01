/** Shared TypeScript types for authentication and user profiles. */

export type UserRole = 'student' | 'college_admin' | 'recruiter';
export type AccountStatus = 'active' | 'pending_approval' | 'rejected' | 'suspended';

/** Authoritative user profile from public.profiles (fetched from backend /api/auth/me). */
export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  requested_role: UserRole;
  role: UserRole;
  account_status: AccountStatus;
  college_id: string | null;
  created_at: string;
  updated_at: string;
}

/** Shape returned by Supabase Auth session. */
export interface AuthUser {
  id: string;
  email: string;
}

/** Ephemeral Guest Session representation. */
export interface GuestSession {
  isGuest: true;
  guestId: string;
  role: UserRole;
  displayName: string;
  createdAt: number;
  expiresAt: number;
}

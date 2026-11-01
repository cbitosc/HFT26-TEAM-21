/**
 * AuthContext — manages Supabase session, profile, and auth actions.
 *
 * Design principles:
 * - Role is fetched from the backend (/api/auth/me), never trusted from the JWT.
 * - session is the Supabase Auth session; profile is the database record.
 * - Exposes login, register, logout, and resetPassword helpers.
 * - Handles Supabase not-configured gracefully (shows a banner, auth is disabled).
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { Session, AuthError } from '@supabase/supabase-js';
import { supabase, isSupabaseConfigured } from '../lib/supabase';
import { UserProfile, UserRole } from '../types/auth';
import { config } from '../config/env';
import {
  createGuestSession,
  getGuestSession,
  clearGuestSession,
  GuestSession,
} from '../services/guestSession';

// ---------------------------------------------------------------------------
// Context shape
// ---------------------------------------------------------------------------

export interface AuthContextValue {
  /** Supabase auth session. null = unauthenticated, undefined = loading. */
  session: Session | null | undefined;
  /** Authoritative database profile. null = not loaded yet. */
  profile: UserProfile | null;
  /** Ephemeral Guest Session if exploring in guest mode. */
  guestSession: GuestSession | null;
  /** Whether the user is currently in an ephemeral guest session. */
  isGuest: boolean;
  /** True while the initial session or profile is being fetched. */
  isLoading: boolean;
  /** Whether Supabase env vars are configured. */
  isConfigured: boolean;
  /** Start an ephemeral guest session with selected role. */
  startGuestSession: (role: UserRole) => GuestSession;
  /** Exit active guest session cleanly. */
  exitGuestSession: () => void;
  /** Register a new user. Returns null on success, error message on failure. */
  register: (params: RegisterParams) => Promise<string | null>;
  /** Log in with email + password. Returns null on success, error message on failure. */
  login: (email: string, password: string) => Promise<string | null>;
  /** Log out the current session. */
  logout: () => Promise<void>;
  /** Send a password reset email. Returns null on success, error message on failure. */
  resetPassword: (email: string) => Promise<string | null>;
  /** Reload the profile from the backend (call after updates). */
  refreshProfile: () => Promise<void>;
  /** Fast-track sign in as a student for local development testing when Supabase is unconfigured. */
  loginAsDevStudent: () => void;
}

export interface RegisterParams {
  email: string;
  password: string;
  fullName: string;
  role: 'student' | 'college_admin' | 'recruiter';
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<Session | null | undefined>(undefined);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [guestSession, setGuestSession] = useState<GuestSession | null>(() => getGuestSession());
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const isMounted = useRef(true);

  const isGuest = !!guestSession;

  // Builds a synthetic profile for ephemeral guest mode
  const buildGuestProfile = useCallback((gs: GuestSession): UserProfile => {
    return {
      id: gs.guestId,
      email: `${gs.guestId}@guest.skillproof.internal`,
      full_name: `${gs.displayName} (Demo)`,
      requested_role: gs.role,
      role: gs.role,
      account_status: 'active',
      college_id: gs.role === 'college_admin' ? 'demo-college-001' : null,
      created_at: new Date(gs.createdAt).toISOString(),
      updated_at: new Date(gs.createdAt).toISOString(),
    };
  }, []);

  // -------------------------------------------------------------------------
  // Guest mode handlers
  // -------------------------------------------------------------------------
  const startGuestSession = useCallback((role: UserRole): GuestSession => {
    // Clear any conflicting active session
    clearGuestSession();
    const newGuest = createGuestSession(role);
    if (isMounted.current) {
      setGuestSession(newGuest);
      setProfile(buildGuestProfile(newGuest));
      setSession(null);
    }
    return newGuest;
  }, [buildGuestProfile]);

  const exitGuestSession = useCallback((): void => {
    clearGuestSession();
    if (isMounted.current) {
      setGuestSession(null);
      setProfile(null);
    }
  }, []);

  // -------------------------------------------------------------------------
  // Profile fetcher — calls the backend, which verifies the JWT and
  // returns the authoritative database record. Never trusts JWT role claims.
  // -------------------------------------------------------------------------
  const fetchProfile = useCallback(async (accessToken: string): Promise<void> => {
    try {
      const response = await fetch(`${config.apiBaseUrl}/api/auth/me`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          Accept: 'application/json',
        },
        signal: AbortSignal.timeout(8000),
      });

      if (!response.ok) {
        // 401/404 = profile not ready or token invalid — clear state cleanly
        if (isMounted.current) setProfile(null);
        return;
      }

      const data: UserProfile = await response.json();
      if (isMounted.current) setProfile(data);
    } catch {
      // Network or timeout — keep any previously loaded profile
      if (isMounted.current && !profile) setProfile(null);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const refreshProfile = useCallback(async (): Promise<void> => {
    const { data } = await supabase.auth.getSession();
    if (data.session?.access_token) {
      await fetchProfile(data.session.access_token);
    }
  }, [fetchProfile]);

  // -------------------------------------------------------------------------
  // Bootstrap: restore existing session on mount
  // -------------------------------------------------------------------------
  useEffect(() => {
    isMounted.current = true;

    // Check for active guest session first
    const activeGuest = getGuestSession();
    if (activeGuest) {
      setGuestSession(activeGuest);
      setProfile(buildGuestProfile(activeGuest));
      setSession(null);
      setIsLoading(false);
      return;
    }

    if (!isSupabaseConfigured) {
      setIsLoading(false);
      return;
    }

    supabase.auth.getSession().then(async ({ data }) => {
      if (!isMounted.current) return;
      setSession(data.session ?? null);
      if (data.session?.access_token) {
        await fetchProfile(data.session.access_token);
      }
      setIsLoading(false);
    });

    // Listen for auth state changes (login, logout, token refresh)
    const { data: listener } = supabase.auth.onAuthStateChange(
      async (_event, newSession) => {
        if (!isMounted.current) return;
        setSession(newSession ?? null);
        if (newSession?.access_token) {
          clearGuestSession();
          setGuestSession(null);
          await fetchProfile(newSession.access_token);
        } else {
          // If not in guest mode, clear profile
          if (!getGuestSession()) {
            setProfile(null);
          }
        }
        setIsLoading(false);
      }
    );

    return () => {
      isMounted.current = false;
      listener.subscription.unsubscribe();
    };
  }, [fetchProfile, buildGuestProfile]);

  // -------------------------------------------------------------------------
  // Auth actions
  // -------------------------------------------------------------------------

  const register = useCallback(
    async ({ email, password, fullName, role }: RegisterParams): Promise<string | null> => {
      if (!isSupabaseConfigured) return 'Authentication is not configured.';
      const { error } = await supabase.auth.signUp({
        email: email.trim().toLowerCase(),
        password,
        options: {
          data: {
            full_name: fullName.trim(),
            requested_role: role,
          },
        },
      });
      if (error) return _formatAuthError(error);
      return null;
    },
    []
  );

  const login = useCallback(
    async (email: string, password: string): Promise<string | null> => {
      if (!isSupabaseConfigured) return 'Authentication is not configured.';
      const { error } = await supabase.auth.signInWithPassword({
        email: email.trim().toLowerCase(),
        password,
      });
      if (error) return _formatAuthError(error);
      return null;
    },
    []
  );

  const logout = useCallback(async (): Promise<void> => {
    exitGuestSession();
    if (isSupabaseConfigured) {
      try {
        await supabase.auth.signOut();
      } catch {
        // Ignore network signout errors
      }
    }
    setProfile(null);
    setSession(null);
  }, [exitGuestSession]);

  const loginAsDevStudent = useCallback((): void => {
    const mockSession = {
      access_token: 'dev-student-token',
      token_type: 'bearer',
      user: {
        id: '00000000-0000-0000-0000-000000000001',
        email: 'student@skillproof.ai',
        app_metadata: {},
        user_metadata: {},
        aud: 'authenticated',
        created_at: new Date().toISOString(),
      },
    } as unknown as Session;

    const mockProfile: UserProfile = {
      id: '00000000-0000-0000-0000-000000000001',
      email: 'student@skillproof.ai',
      full_name: 'Demo Student',
      requested_role: 'student',
      role: 'student',
      account_status: 'active',
      college_id: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setSession(mockSession);
    setProfile(mockProfile);
  }, []);

  const resetPassword = useCallback(
    async (email: string): Promise<string | null> => {
      if (!isSupabaseConfigured) return 'Authentication is not configured.';
      const { error } = await supabase.auth.resetPasswordForEmail(
        email.trim().toLowerCase(),
        { redirectTo: `${window.location.origin}/reset-password` }
      );
      if (error) return _formatAuthError(error);
      return null;
    },
    []
  );

  // -------------------------------------------------------------------------
  // Context value (memoised to prevent unnecessary re-renders)
  // -------------------------------------------------------------------------

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      profile,
      guestSession,
      isGuest,
      isLoading,
      isConfigured: isSupabaseConfigured,
      startGuestSession,
      exitGuestSession,
      register,
      login,
      logout,
      resetPassword,
      refreshProfile,
      loginAsDevStudent,
    }),
    [
      session,
      profile,
      guestSession,
      isGuest,
      isLoading,
      startGuestSession,
      exitGuestSession,
      register,
      login,
      logout,
      resetPassword,
      refreshProfile,
      loginAsDevStudent,
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used inside <AuthProvider>');
  }
  return ctx;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function _formatAuthError(error: AuthError): string {
  const msg = error.message || '';
  const status = (error as unknown as { status?: number }).status;
  const code = (error as unknown as { code?: string }).code;

  // Supabase rate limit detection (429, email rate limits, request cooldowns)
  if (
    status === 429 ||
    code === 'over_email_send_rate_limit' ||
    code === 'over_request_rate_limit' ||
    msg.includes('rate limit') ||
    msg.includes('Too Many') ||
    msg.includes('60 seconds')
  ) {
    return 'Authentication rate limit reached. For security, Supabase limits rapid registration and verification requests. Please wait 60 seconds before trying again, or explore immediately using Guest Mode.';
  }
  if (msg.includes('Invalid login credentials'))
    return 'Incorrect email or password. Please try again.';
  if (msg.includes('Email not confirmed'))
    return 'Please confirm your email before logging in.';
  if (msg.includes('User already registered'))
    return 'An account with this email already exists.';
  if (msg.includes('Password should be'))
    return 'Password must be at least 6 characters.';
  return msg || 'An authentication error occurred.';
}

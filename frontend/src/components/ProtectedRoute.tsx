/**
 * ProtectedRoute — guards routes that require authentication and/or a specific role.
 *
 * Usage:
 *   <ProtectedRoute>                          — any authenticated user
 *   <ProtectedRoute requiredRole="student">   — must be active student
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { UserRole } from '../types/auth';
import { LoadingScreen } from './LoadingScreen';

interface ProtectedRouteProps {
  children: React.ReactNode;
  /** If set, the authenticated user must have this exact role. */
  requiredRole?: UserRole;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole,
}) => {
  const { session, profile, guestSession, isGuest, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingScreen message="Verifying session…" />;
  }

  // Not authenticated and not guest
  if (!session && !isGuest) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Ephemeral Guest Mode access check
  if (isGuest && guestSession) {
    if (requiredRole && guestSession.role !== requiredRole) {
      return <Navigate to="/unauthorized" replace />;
    }
    return <>{children}</>;
  }

  // Authenticated but profile not yet loaded
  if (!profile) {
    return <LoadingScreen message="Loading your profile…" />;
  }

  // Pending approval → redirect to pending page
  if (profile.account_status === 'pending_approval') {
    return <Navigate to="/dashboard/pending-approval" replace />;
  }

  // Rejected → redirect to rejected notice
  if (profile.account_status === 'rejected') {
    return <Navigate to="/dashboard/rejected" replace />;
  }

  // Suspended → redirect to suspended notice
  if (profile.account_status === 'suspended') {
    return <Navigate to="/dashboard/suspended" replace />;
  }

  // Role mismatch for role-protected routes
  if (requiredRole && profile.role !== requiredRole) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children}</>;
};

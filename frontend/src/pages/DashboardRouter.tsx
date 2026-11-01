/**
 * DashboardRouter — redirects authenticated users to their role-specific
 * dashboard, based on the authoritative profile from the backend.
 */

import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LoadingScreen } from '../components/LoadingScreen';

export const DashboardRouter: React.FC = () => {
  const { profile, guestSession, isGuest, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen message="Routing to your dashboard…" />;
  }

  // Guest mode routing
  if (isGuest && guestSession) {
    switch (guestSession.role) {
      case 'student':
        return <Navigate to="/dashboard/student" replace />;
      case 'college_admin':
        return <Navigate to="/dashboard/college" replace />;
      case 'recruiter':
        return <Navigate to="/dashboard/recruiter" replace />;
      default:
        return <Navigate to="/dashboard/student" replace />;
    }
  }

  if (!profile) {
    return <LoadingScreen message="Routing to your dashboard…" />;
  }

  // Status-based routing first
  if (profile.account_status === 'pending_approval') {
    return <Navigate to="/dashboard/pending-approval" replace />;
  }
  if (profile.account_status === 'rejected') {
    return <Navigate to="/dashboard/rejected" replace />;
  }
  if (profile.account_status === 'suspended') {
    return <Navigate to="/dashboard/suspended" replace />;
  }

  // Role-based routing
  switch (profile.role) {
    case 'student':
      return <Navigate to="/dashboard/student" replace />;
    case 'college_admin':
      return <Navigate to="/dashboard/college" replace />;
    case 'recruiter':
      return <Navigate to="/dashboard/recruiter" replace />;
    default:
      return <Navigate to="/dashboard/student" replace />;
  }
};

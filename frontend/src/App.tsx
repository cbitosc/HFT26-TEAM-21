/**
 * App — root component with full routing for Module 2.
 *
 * Routing structure:
 *   /                   → Landing page (original DashboardShell from Module 1)
 *   /login              → Login form
 *   /register           → Role selection + registration
 *   /forgot-password    → Password reset request
 *   /reset-password     → Password reset completion (via email link)
 *   /unauthorized       → Access denied page
 *   /dashboard          → Auto-redirect to role-specific dashboard
 *   /dashboard/student  → Student workspace (protected, role=student)
 *   /dashboard/college  → College admin workspace (protected, role=college_admin)
 *   /dashboard/recruiter→ Recruiter workspace (protected, role=recruiter)
 *   /dashboard/pending-approval → Pending verification notice
 *   /dashboard/rejected → Rejected notice
 *   /dashboard/suspended→ Suspended notice
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Module 1 — landing page
import { DashboardShell } from './pages/DashboardShell';
import { WelcomePage } from './pages/WelcomePage';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { checkBackendHealth, HealthCheckResult } from './services/api';

// Module 2 — auth pages
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/ResetPasswordPage';
import { UnauthorizedPage } from './pages/UnauthorizedPage';

// Module 2 — protected dashboards
import { DashboardLayout } from './pages/DashboardLayout';
import { DashboardRouter } from './pages/DashboardRouter';
import { StudentDashboard } from './pages/dashboards/StudentDashboard';
import { StudentPortfolioPage } from './pages/dashboards/StudentPortfolioPage';
import { AssessmentDashboard } from './pages/dashboards/AssessmentDashboard';
import { AssessmentWorkspacePage } from './pages/dashboards/AssessmentWorkspacePage';
import { AssessmentSummaryPage } from './pages/dashboards/AssessmentSummaryPage';
import { PerformanceAnalyticsPage } from './pages/dashboards/PerformanceAnalyticsPage';
import { CollegeAdminDashboard } from './pages/dashboards/CollegeAdminDashboard';
import { RecruiterDashboard } from './pages/dashboards/RecruiterDashboard';
import { LiveInterviewRoom } from './pages/dashboards/LiveInterviewRoom';
import { PendingApprovalPage } from './pages/dashboards/PendingApprovalPage';
import { RejectedPage } from './pages/dashboards/RejectedPage';
import { SuspendedPage } from './pages/dashboards/SuspendedPage';

import { ProtectedRoute } from './components/ProtectedRoute';

// ---------------------------------------------------------------------------
// Landing page wrapper — preserves Module 1 layout with health check
// ---------------------------------------------------------------------------

const LandingPage: React.FC = () => {
  const [healthResult, setHealthResult] = useState<HealthCheckResult>({
    state: 'loading',
    data: null,
    error: null,
    checkedAt: new Date(),
  });
  const [isChecking, setIsChecking] = useState<boolean>(false);

  const performHealthCheck = useCallback(async () => {
    setIsChecking(true);
    try {
      const result = await checkBackendHealth();
      setHealthResult(result);
    } finally {
      setIsChecking(false);
    }
  }, []);

  useEffect(() => {
    performHealthCheck();
  }, [performHealthCheck]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-sky-500 selection:text-white">
      <div>
        <Navbar
          connectionState={healthResult.state}
          onRefreshHealth={performHealthCheck}
          isChecking={isChecking}
        />
        <DashboardShell healthResult={healthResult} />
      </div>
      <Footer />
    </div>
  );
};

// ---------------------------------------------------------------------------
// App root
// ---------------------------------------------------------------------------

export const App: React.FC = () => (
  <Routes>
    {/* Public routes */}
    <Route path="/" element={<WelcomePage />} />
    <Route path="/diagnostics" element={<LandingPage />} />
    <Route path="/login" element={<LoginPage />} />
    <Route path="/register" element={<RegisterPage />} />
    <Route path="/forgot-password" element={<ForgotPasswordPage />} />
    <Route path="/reset-password" element={<ResetPasswordPage />} />
    <Route path="/unauthorized" element={<UnauthorizedPage />} />

    {/* Protected dashboard routes */}
    <Route
      path="/dashboard"
      element={
        <ProtectedRoute>
          <DashboardLayout />
        </ProtectedRoute>
      }
    >
      {/* Index route → auto redirect to role dashboard */}
      <Route index element={<DashboardRouter />} />

      {/* Role-specific dashboards */}
      <Route
        path="student"
        element={
          <ProtectedRoute requiredRole="student">
            <StudentDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="student/portfolio"
        element={
          <ProtectedRoute requiredRole="student">
            <StudentPortfolioPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="student/assessments"
        element={
          <ProtectedRoute requiredRole="student">
            <AssessmentDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="student/assessment/:sessionId"
        element={
          <ProtectedRoute requiredRole="student">
            <AssessmentWorkspacePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="student/assessment/:sessionId/summary"
        element={
          <ProtectedRoute requiredRole="student">
            <AssessmentSummaryPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="student/analytics"
        element={
          <ProtectedRoute requiredRole="student">
            <PerformanceAnalyticsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="college"
        element={
          <ProtectedRoute requiredRole="college_admin">
            <CollegeAdminDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="recruiter"
        element={
          <ProtectedRoute requiredRole="recruiter">
            <RecruiterDashboard />
          </ProtectedRoute>
        }
      />
    </Route>

    {/* Status pages — shown inside a minimal shell, need session but not active status */}
    <Route path="/dashboard/pending-approval" element={<PendingApprovalPage />} />
    <Route path="/dashboard/rejected" element={<RejectedPage />} />
    <Route path="/dashboard/suspended" element={<SuspendedPage />} />

    {/* Live Collaborative Interview Workspace (Module 12) */}
    <Route
      path="/interview/:id"
      element={
        <ProtectedRoute>
          <LiveInterviewRoom />
        </ProtectedRoute>
      }
    />

    {/* Fallback */}
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
);

export default App;

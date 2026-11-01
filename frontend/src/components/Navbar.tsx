/**
 * Navbar — top navigation bar.
 *
 * When authenticated: shows user name, role badge, and logout button.
 * When unauthenticated: shows Login and Register links.
 * Also supports displaying backend connection health badge when props are provided.
 *
 * Updated for Module 2. Preserved original design system and Module 1 telemetry.
 */

import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Terminal, Shield, LogOut, User } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './Button';
import { StatusBadge } from './StatusBadge';
import { ConnectionState } from '../services/api';

interface NavbarProps {
  connectionState?: ConnectionState;
  onRefreshHealth?: () => void;
  isChecking?: boolean;
}

const ROLE_LABELS: Record<string, string> = {
  student: 'Student',
  college_admin: 'College Admin',
  recruiter: 'Recruiter',
};

const ROLE_COLORS: Record<string, string> = {
  student: 'bg-sky-950 text-sky-400 border-sky-800/60',
  college_admin: 'bg-indigo-950 text-indigo-400 border-indigo-800/60',
  recruiter: 'bg-purple-950 text-purple-400 border-purple-800/60',
};

export const Navbar: React.FC<NavbarProps> = ({
  connectionState,
  onRefreshHealth,
  isChecking = false,
}) => {
  const { session, profile, guestSession, isGuest, logout, exitGuestSession, isLoading } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    if (isGuest) {
      exitGuestSession();
      navigate('/');
    } else {
      await logout();
      navigate('/login');
    }
  };

  const isAuthenticated = !isGuest && !!session && !!profile;

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link to={isAuthenticated || isGuest ? '/dashboard' : '/'} className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-sky-400 flex items-center justify-center shadow-lg shadow-sky-500/10">
            <Terminal className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-white tracking-tight">
                SkillProof<span className="text-sky-400">AI</span>
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Portfolio-Driven Adaptive Assessment
            </p>
          </div>
        </Link>

        {/* Right side */}
        <div className="flex items-center space-x-3">
          <div className="hidden md:flex items-center space-x-1 text-xs text-slate-400 border border-slate-800 px-3 py-1.5 rounded-lg bg-slate-900/50">
            <Shield className="w-3.5 h-3.5 text-sky-400 mr-1" />
            <span>Deterministic Grading</span>
          </div>

          {/* Connection Status Badge if passed (e.g. on landing page) */}
          {connectionState && (
            <StatusBadge
              state={connectionState}
              onRefresh={onRefreshHealth}
              isRefreshing={isChecking}
            />
          )}

          {isLoading ? (
            <div className="h-8 w-24 rounded-lg bg-slate-800 animate-pulse" />
          ) : isGuest && guestSession ? (
            <div className="flex items-center space-x-3">
              {/* Guest Role badge */}
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded border border-amber-500/40 bg-amber-500/10 text-amber-300">
                Guest {ROLE_LABELS[guestSession.role] || guestSession.role}
              </span>

              {/* Guest name */}
              <div className="hidden sm:flex items-center space-x-1.5 text-xs text-slate-300">
                <User className="w-3.5 h-3.5 text-amber-400" />
                <span className="max-w-[140px] truncate">{guestSession.displayName}</span>
              </div>

              {/* Exit demo */}
              <button
                onClick={handleLogout}
                className="text-xs text-amber-400 hover:text-amber-200 border border-amber-800/60 bg-amber-950/30 px-2.5 py-1 rounded-lg transition-colors flex items-center space-x-1"
                title="Exit Guest Mode"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Exit Demo</span>
              </button>

              <Link to="/login">
                <Button variant="ghost" className="text-xs py-1.5 px-3">
                  Sign in
                </Button>
              </Link>
            </div>
          ) : isAuthenticated ? (
            <div className="flex items-center space-x-3">
              {/* Role badge */}
              <span
                className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-1 rounded border ${
                  ROLE_COLORS[profile.role] || ROLE_COLORS.student
                }`}
              >
                {ROLE_LABELS[profile.role] || profile.role}
              </span>

              {/* User button */}
              <div className="hidden sm:flex items-center space-x-2 text-xs text-slate-300">
                <User className="w-3.5 h-3.5 text-slate-500" />
                <span className="max-w-[120px] truncate">{profile.full_name}</span>
              </div>

              <button
                onClick={handleLogout}
                className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                title="Sign out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <Link to="/login">
                <Button variant="ghost" className="text-xs py-1.5 px-3">
                  Sign in
                </Button>
              </Link>
              <Link to="/register">
                <Button variant="primary" className="text-xs py-1.5 px-3">
                  Register
                </Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

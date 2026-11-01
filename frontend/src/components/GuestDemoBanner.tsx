/**
 * GuestDemoBanner — Prominent notification banner displayed when viewing
 * any workspace in ephemeral Guest Mode.
 *
 * Ensures full transparency:
 * - Highlights that data is simulated and isolated.
 * - Informs the user that no real records or credentials are required.
 * - Provides quick actions to exit demo, switch demo roles, or register a permanent account.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, LogOut, UserPlus, ShieldAlert } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './Button';

const ROLE_DISPLAY_NAMES: Record<string, string> = {
  student: 'Student Candidate',
  college_admin: 'College Administrator',
  recruiter: 'Technical Recruiter',
};

export const GuestDemoBanner: React.FC = () => {
  const { isGuest, guestSession, exitGuestSession } = useAuth();
  const navigate = useNavigate();

  if (!isGuest || !guestSession) return null;

  const roleLabel = ROLE_DISPLAY_NAMES[guestSession.role] || guestSession.role;

  const handleExit = () => {
    exitGuestSession();
    navigate('/');
  };

  const handleSwitch = () => {
    navigate('/');
  };

  const handleRegister = () => {
    exitGuestSession();
    navigate('/register');
  };

  return (
    <div className="mb-6 rounded-2xl border border-amber-500/30 bg-gradient-to-r from-amber-950/40 via-slate-900/80 to-purple-950/40 p-4 shadow-xl shadow-amber-950/20 backdrop-blur-md">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Left message */}
        <div className="flex items-start sm:items-center space-x-3.5">
          <div className="w-9 h-9 rounded-xl bg-amber-500/20 border border-amber-500/30 text-amber-400 flex items-center justify-center flex-shrink-0 shadow-inner">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-extrabold uppercase tracking-wider text-amber-400 bg-amber-500/10 px-2.5 py-0.5 rounded-full border border-amber-500/20">
                Guest Demo Mode • {roleLabel}
              </span>
              <span className="hidden sm:inline-flex items-center text-[10px] text-slate-400 border border-slate-800 bg-slate-900/60 px-2 py-0.5 rounded">
                <ShieldAlert className="w-3 h-3 text-slate-400 mr-1" />
                Isolated Sample Data
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              You are exploring with simulated sample data. Submissions and grading here will not affect permanent college or recruiter records.
            </p>
          </div>
        </div>

        {/* Right action controls */}
        <div className="flex items-center space-x-2 flex-shrink-0">
          <button
            onClick={handleSwitch}
            className="text-xs text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700/80 px-3 py-1.5 rounded-lg border border-slate-700 transition-colors"
          >
            Switch Role
          </button>
          <button
            onClick={handleExit}
            className="text-xs text-amber-300 hover:text-amber-200 bg-amber-950/40 hover:bg-amber-900/40 px-3 py-1.5 rounded-lg border border-amber-700/50 flex items-center space-x-1.5 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Exit Demo</span>
          </button>
          <Button
            variant="primary"
            onClick={handleRegister}
            className="text-xs py-1.5 px-3 flex items-center space-x-1.5 shadow-md shadow-sky-500/20"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Create Real Account</span>
          </Button>
        </div>
      </div>
    </div>
  );
};

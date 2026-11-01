/**
 * PendingApprovalPage — shown to college_admin and recruiter users
 * whose account_status is 'pending_approval'.
 * Explains the verification process and provides logout.
 */

import React from 'react';
import { Clock, LogOut } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/Button';

export const PendingApprovalPage: React.FC = () => {
  const { profile, logout } = useAuth();

  const roleLabel =
    profile?.requested_role === 'college_admin'
      ? 'College Administrator'
      : profile?.requested_role === 'recruiter'
      ? 'Verified Recruiter'
      : 'Privileged';

  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4">
      <div className="max-w-md w-full rounded-2xl border border-amber-800/50 bg-amber-950/20 p-8 text-center space-y-6">
        <div className="mx-auto w-14 h-14 rounded-full bg-amber-900/50 flex items-center justify-center">
          <Clock className="w-7 h-7 text-amber-400" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-white mb-2">
            Verification Pending
          </h1>
          <p className="text-sm text-slate-300 leading-relaxed">
            Your <span className="text-amber-300 font-medium">{roleLabel}</span> account
            is currently awaiting administrator review. You will be notified
            once your verification request is processed.
          </p>
        </div>

        <div className="bg-amber-950/40 border border-amber-800/40 rounded-xl p-4 text-left text-xs text-slate-400 space-y-2">
          <p><strong className="text-slate-300">Email:</strong> {profile?.email}</p>
          <p><strong className="text-slate-300">Requested role:</strong> {roleLabel}</p>
          <p><strong className="text-slate-300">Status:</strong>{' '}
            <span className="text-amber-400 font-medium">Pending Approval</span>
          </p>
        </div>

        <Button variant="ghost" fullWidth onClick={logout}>
          <LogOut className="w-4 h-4" /> Sign out
        </Button>
      </div>
    </div>
  );
};

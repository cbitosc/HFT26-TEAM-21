/**
 * RejectedPage — shown when a user's verification request has been rejected.
 */

import React from 'react';
import { XCircle, LogOut } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/Button';

export const RejectedPage: React.FC = () => {
  const { profile, logout } = useAuth();

  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4">
      <div className="max-w-md w-full rounded-2xl border border-rose-800/50 bg-rose-950/20 p-8 text-center space-y-6">
        <div className="mx-auto w-14 h-14 rounded-full bg-rose-900/50 flex items-center justify-center">
          <XCircle className="w-7 h-7 text-rose-400" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-white mb-2">
            Verification Denied
          </h1>
          <p className="text-sm text-slate-300 leading-relaxed">
            Your verification request was not approved. If you believe this is an error,
            please contact the platform administrator.
          </p>
        </div>

        <div className="bg-rose-950/40 border border-rose-800/40 rounded-xl p-4 text-left text-xs text-slate-400 space-y-2">
          <p><strong className="text-slate-300">Email:</strong> {profile?.email}</p>
          <p><strong className="text-slate-300">Status:</strong>{' '}
            <span className="text-rose-400 font-medium">Rejected</span>
          </p>
        </div>

        <Button variant="ghost" fullWidth onClick={logout}>
          <LogOut className="w-4 h-4" /> Sign out
        </Button>
      </div>
    </div>
  );
};

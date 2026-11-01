/**
 * SuspendedPage — shown when an account has been suspended.
 */

import React from 'react';
import { Ban, LogOut } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/Button';

export const SuspendedPage: React.FC = () => {
  const { profile, logout } = useAuth();

  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4">
      <div className="max-w-md w-full rounded-2xl border border-slate-700 bg-slate-900/80 p-8 text-center space-y-6">
        <div className="mx-auto w-14 h-14 rounded-full bg-slate-800 flex items-center justify-center">
          <Ban className="w-7 h-7 text-slate-400" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-white mb-2">Account Suspended</h1>
          <p className="text-sm text-slate-300 leading-relaxed">
            Your account has been suspended. Please contact support for assistance.
          </p>
        </div>
        <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 text-left text-xs text-slate-400 space-y-2">
          <p><strong className="text-slate-300">Email:</strong> {profile?.email}</p>
          <p><strong className="text-slate-300">Status:</strong>{' '}
            <span className="text-slate-500 font-medium">Suspended</span>
          </p>
        </div>
        <Button variant="ghost" fullWidth onClick={logout}>
          <LogOut className="w-4 h-4" /> Sign out
        </Button>
      </div>
    </div>
  );
};

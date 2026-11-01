/**
 * UnauthorizedPage — shown when a user tries to access a role-protected
 * route they don't have permissions for.
 */

import React from 'react';
import { ShieldAlert } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/Button';

export const UnauthorizedPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4">
      <div className="max-w-md w-full rounded-2xl border border-slate-800 bg-slate-900/70 p-8 text-center space-y-6">
        <div className="mx-auto w-14 h-14 rounded-full bg-rose-950/50 flex items-center justify-center">
          <ShieldAlert className="w-7 h-7 text-rose-400" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-white mb-2">Access Denied</h1>
          <p className="text-sm text-slate-300">
            You do not have permission to access this page. If you believe
            this is an error, please contact support.
          </p>
        </div>
        <Button variant="secondary" fullWidth onClick={() => navigate('/dashboard')}>
          Return to Dashboard
        </Button>
      </div>
    </div>
  );
};

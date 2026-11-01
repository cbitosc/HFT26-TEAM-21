import React from 'react';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { ConnectionState } from '../services/api';

interface StatusBadgeProps {
  state: ConnectionState;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  state,
  onRefresh,
  isRefreshing,
}) => {
  return (
    <div className="flex items-center space-x-2">
      <div
        className={`inline-flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
          state === 'connected'
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
            : state === 'loading'
            ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
            : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
        }`}
      >
        {state === 'connected' && (
          <>
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Backend Connected</span>
          </>
        )}

        {state === 'loading' && (
          <>
            <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-300" />
            <span>Checking Backend...</span>
          </>
        )}

        {state === 'disconnected' && (
          <>
            <span className="relative flex h-2 w-2">
              <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
            </span>
            <XCircle className="w-3.5 h-3.5 text-rose-400" />
            <span>Backend Disconnected</span>
          </>
        )}
      </div>

      {onRefresh && (
        <button
          onClick={onRefresh}
          disabled={isRefreshing || state === 'loading'}
          className="text-xs px-2.5 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 disabled:opacity-50 transition-colors"
          title="Retry backend health check"
        >
          {isRefreshing ? 'Checking...' : 'Check Again'}
        </button>
      )}
    </div>
  );
};

/**
 * LoadingScreen — full-page loading indicator shown during auth bootstrap.
 */

import React from 'react';
import { Terminal } from 'lucide-react';

interface LoadingScreenProps {
  message?: string;
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({
  message = 'Loading…',
}) => (
  <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-400">
    <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-600 to-sky-400 flex items-center justify-center shadow-xl shadow-sky-500/20 mb-6 animate-pulse">
      <Terminal className="w-7 h-7 text-white" />
    </div>
    <p className="text-sm font-medium text-slate-300">{message}</p>
    <div className="mt-4 flex space-x-1">
      <span className="w-2 h-2 rounded-full bg-sky-500 animate-bounce [animation-delay:0ms]" />
      <span className="w-2 h-2 rounded-full bg-sky-500 animate-bounce [animation-delay:150ms]" />
      <span className="w-2 h-2 rounded-full bg-sky-500 animate-bounce [animation-delay:300ms]" />
    </div>
  </div>
);

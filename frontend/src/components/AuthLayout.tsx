/**
 * AuthLayout — Premium SaaS split-screen authentication wrapper.
 * Features:
 * - Deep navy, indigo, and subtle violet gradient aesthetic.
 * - Responsive split-screen with branding, tagline, and AI assessment preview on the left.
 * - Clean, elegant glassmorphic authentication card on the right.
 * - Live backend connectivity verification with clear error handling.
 */

import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Terminal,
  ShieldCheck,
  Cpu,
  Code2,
  CheckCircle2,
  RefreshCw,
  AlertTriangle,
  Sparkles,
} from 'lucide-react';
import { checkBackendHealth } from '../services/api';
import { config } from '../config/env';

interface AuthLayoutProps {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ title, subtitle, children }) => {
  const [backendState, setBackendState] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const [backendError, setBackendError] = useState<string | null>(null);

  const verifyHealth = useCallback(async () => {
    setBackendState('checking');
    try {
      const res = await checkBackendHealth();
      if (res.state === 'connected') {
        setBackendState('connected');
        setBackendError(null);
      } else {
        setBackendState('disconnected');
        setBackendError(res.error || `Unable to reach ${config.apiBaseUrl}/api/health`);
      }
    } catch {
      setBackendState('disconnected');
      setBackendError(`Unable to reach backend at ${config.apiBaseUrl}`);
    }
  }, []);

  useEffect(() => {
    verifyHealth();
  }, [verifyHealth]);

  return (
    <div className="min-h-screen w-full flex bg-[#070B19] text-slate-100 font-sans selection:bg-indigo-500 selection:text-white">
      {/* =========================================================================
          LEFT PANEL: Visual identity, branding, tagline & AI/code preview
          Visible on lg screens (1024px and up)
      ========================================================================= */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-5/12 flex-col justify-between p-12 relative overflow-hidden bg-gradient-to-br from-[#090D22] via-[#0D1532] to-[#14102C] border-r border-indigo-950/60">
        {/* Ambient Gradient Background Glows */}
        <div className="absolute -top-32 -left-32 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-1/3 -right-24 w-80 h-80 bg-violet-600/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 left-1/4 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Top: Brand Logo */}
        <div className="relative z-10">
          <Link to="/" className="inline-flex items-center space-x-3 group">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-sky-400 p-0.5 shadow-lg shadow-indigo-500/30 group-hover:shadow-indigo-500/50 transition-all duration-300">
              <div className="w-full h-full bg-[#090D22] rounded-[10px] flex items-center justify-center">
                <Terminal className="w-5 h-5 text-indigo-400 group-hover:text-indigo-300 transition-colors" />
              </div>
            </div>
            <div>
              <span className="font-bold text-xl tracking-tight text-white flex items-center gap-1">
                SkillProof <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 via-indigo-400 to-violet-400">AI</span>
              </span>
              <span className="block text-[10px] uppercase tracking-widest text-indigo-300 font-semibold">
                Adaptive Assessment
              </span>
            </div>
          </Link>
        </div>

        {/* Middle: Tagline & Interactive Platform Showcase */}
        <div className="relative z-10 my-auto py-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold mb-6">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
            <span>Next-Gen Technical Verification</span>
          </div>

          <h2 className="text-3xl xl:text-4xl font-extrabold text-white tracking-tight leading-tight mb-4">
            Your Skills. <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-300 via-sky-300 to-violet-300">
              Your Proof.
            </span> <br />
            Your Future.
          </h2>

          <p className="text-sm xl:text-base text-slate-300 leading-relaxed mb-8 max-w-lg">
            Portfolio-driven adaptive technical assessments with deterministic sandbox grading,
            anti-cheating CodeTrace telemetry, and recruiter-verified skill dossiers.
          </p>

          {/* Code & Evaluation Preview Card */}
          <div className="rounded-2xl border border-indigo-500/20 bg-slate-900/80 backdrop-blur-md p-5 shadow-2xl shadow-indigo-950/60 max-w-md">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-rose-500/80" />
                <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                <span className="text-[11px] font-mono text-slate-400 pl-2">Session #SP-8821</span>
              </div>
              <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[10px] font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                <span>Isolated Sandbox</span>
              </div>
            </div>

            <div className="font-mono text-xs text-slate-300 space-y-1 bg-[#050814]/90 p-3.5 rounded-xl border border-slate-800/80 mb-3.5">
              <div className="text-slate-500"># Evaluating student solution...</div>
              <div className="text-indigo-300"><span className="text-violet-400">def</span> <span className="text-sky-300">solve_stream</span>(tasks: <span className="text-amber-300">List</span>[<span className="text-amber-300">Task</span>]):</div>
              <div className="text-emerald-400 pl-4">✓ Assertions passed: 3/3 (100%)</div>
              <div className="text-sky-400 pl-4">⚡ Time: 24ms | Memory: 14MB</div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="flex items-center gap-1.5 text-slate-300">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Deterministic Grading</span>
              </div>
              <div className="flex items-center gap-1.5 text-slate-300">
                <Cpu className="w-3.5 h-3.5 text-sky-400" />
                <span>CodeTrace Telemetry</span>
              </div>
              <div className="flex items-center gap-1.5 text-slate-300">
                <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
                <span>TrustGuard Verification</span>
              </div>
              <div className="flex items-center gap-1.5 text-slate-300">
                <Code2 className="w-3.5 h-3.5 text-violet-400" />
                <span>Zero LLM Grading Bias</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Security / Trust Footer */}
        <div className="relative z-10 pt-6 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
          <span>Enterprise-Grade Security</span>
          <div className="flex items-center gap-3">
            <span>256-bit TLS</span>
            <span>•</span>
            <span>Row-Level Security</span>
          </div>
        </div>
      </div>

      {/* =========================================================================
          RIGHT PANEL: Authentication Form Card
      ========================================================================= */}
      <div className="flex-1 flex flex-col justify-center items-center p-6 sm:p-12 lg:p-16 relative overflow-y-auto">
        {/* Subtle Ambient Radial Glow */}
        <div className="absolute top-1/4 right-1/4 w-80 h-80 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

        {/* Mobile Header Branding (Visible only on < lg) */}
        <div className="lg:hidden w-full max-w-md mb-8 flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-600 to-sky-400 flex items-center justify-center shadow-md shadow-indigo-500/20">
              <Terminal className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-lg text-white">
              SkillProof<span className="text-sky-400">AI</span>
            </span>
          </Link>
          <span className="text-[11px] font-medium text-slate-400">Technical Assessment</span>
        </div>

        {/* Main Authentication Card */}
        <div className="w-full max-w-md rounded-3xl border border-slate-800/80 bg-slate-900/70 backdrop-blur-xl p-8 sm:p-10 shadow-2xl shadow-black/60 relative z-10">
          {/* Backend Connection Status Banner (shown ONLY if backend is unreachable) */}
          {backendState === 'disconnected' && (
            <div className="mb-6 p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-start gap-3">
              <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold text-amber-200">Backend Disconnected</p>
                <p className="text-[11px] text-amber-300/80 mt-0.5">
                  {backendError || `Could not reach ${config.apiBaseUrl}. Ensure FastAPI backend is running.`}
                </p>
                <button
                  type="button"
                  onClick={verifyHealth}
                  className="mt-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 text-[11px] font-medium transition"
                >
                  <RefreshCw className="w-3 h-3" />
                  <span>Retry Connection</span>
                </button>
              </div>
            </div>
          )}

          {/* Card Header */}
          <div className="mb-8">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              {title}
            </h1>
            <p className="text-sm text-slate-400 mt-2 leading-relaxed">
              {subtitle}
            </p>
          </div>

          {/* Form Content (Passed from child page) */}
          <div>{children}</div>
        </div>

        {/* Card Footer / Legal */}
        <div className="w-full max-w-md mt-6 text-center text-xs text-slate-400 flex items-center justify-center gap-4">
          <Link to="/" className="hover:text-slate-300 transition-colors">Privacy Policy</Link>
          <span>•</span>
          <Link to="/" className="hover:text-slate-300 transition-colors">Terms of Service</Link>
          <span>•</span>
          <span className="text-slate-400">© 2026 SkillProof AI</span>
        </div>
      </div>
    </div>
  );
};

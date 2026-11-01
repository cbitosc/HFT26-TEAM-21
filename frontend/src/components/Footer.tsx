import React from 'react';
import { Terminal, Database, Cpu, ShieldCheck } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-slate-800 bg-slate-950 py-10 mt-16 text-slate-400 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-sky-400" />
            <span className="font-semibold text-slate-200">
              SkillProof AI Architecture Baseline
            </span>
            <span className="text-slate-600">|</span>
            <span>Module 1: Foundation</span>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-[11px]">
            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-900 border border-slate-800">
              <Cpu className="w-3 h-3 text-sky-400" />
              <span>React 18 + Vite</span>
            </span>
            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-900 border border-slate-800">
              <Terminal className="w-3 h-3 text-emerald-400" />
              <span>FastAPI + Python</span>
            </span>
            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-900 border border-slate-800">
              <Database className="w-3 h-3 text-indigo-400" />
              <span>Supabase RLS</span>
            </span>
            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-900 border border-slate-800">
              <ShieldCheck className="w-3 h-3 text-purple-400" />
              <span>Judge0 Sandboxing</span>
            </span>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-between border-t border-slate-900 pt-6 text-slate-400 text-[11px]">
          <p>© 2026 SkillProof AI Platform. Built with a zero-cost / free-tier first philosophy.</p>
          <p className="mt-2 sm:mt-0">Deterministic Evaluation • Guarded AI Assistance</p>
        </div>
      </div>
    </footer>
  );
};

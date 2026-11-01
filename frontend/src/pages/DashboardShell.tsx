import React from 'react';
import {
  GraduationCap,
  Building2,
  Briefcase,
  Layers,
  ArrowUpRight,
  Server,
  Activity,
} from 'lucide-react';
import { RoleCard } from '../components/RoleCard';
import { HealthCheckResult } from '../services/api';
import { config } from '../config/env';

interface DashboardShellProps {
  healthResult: HealthCheckResult;
}

export const DashboardShell: React.FC<DashboardShellProps> = ({ healthResult }) => {
  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-12">
      {/* Hero Welcome Section */}
      <section className="text-center sm:text-left space-y-4">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium bg-sky-950/80 border border-sky-800/60 text-sky-300">
          <Layers className="w-3.5 h-3.5" />
          <span>Module 1 Completed: Project Foundation & Communication Active</span>
        </div>

        <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
          Prove Your Skills. <br className="hidden sm:inline" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-brand-500">
            Showcase Your Ability.
          </span>
        </h1>

        <p className="max-w-3xl text-base sm:text-lg text-slate-300 leading-relaxed">
          {config.tagline}. An AI-assisted platform evaluating software engineering candidates on verified practical code execution, problem solving, and portfolio evidence.
        </p>
      </section>

      {/* Backend Live Telemetry Diagnostic Panel */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-slate-800 flex items-center justify-center text-sky-400">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">
                Backend API Telemetry
              </h2>
              <p className="text-xs text-slate-400">
                Live communication channel with FastAPI backend service
              </p>
            </div>
          </div>

          <div className="text-xs font-mono text-slate-400 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 flex items-center space-x-2">
            <Activity className="w-3.5 h-3.5 text-sky-400" />
            <span>Target: {config.apiBaseUrl}/api/health</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80">
            <span className="text-slate-400 block mb-1">Connection State</span>
            <span
              className={`font-semibold capitalize ${
                healthResult.state === 'connected'
                  ? 'text-emerald-400'
                  : healthResult.state === 'loading'
                  ? 'text-amber-400'
                  : 'text-rose-400'
              }`}
            >
              {healthResult.state}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80">
            <span className="text-slate-400 block mb-1">Service Status</span>
            <span className="font-semibold text-slate-200">
              {healthResult.data?.status ? (
                <span className="text-emerald-400 uppercase font-mono">
                  {healthResult.data.status}
                </span>
              ) : (
                <span className="text-slate-500 italic">Unavailable</span>
              )}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80">
            <span className="text-slate-400 block mb-1">Reported Message</span>
            <span className="text-slate-300 truncate block" title={healthResult.data?.message || healthResult.error || 'N/A'}>
              {healthResult.data?.message || (
                <span className="text-rose-400">{healthResult.error || 'N/A'}</span>
              )}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80">
            <span className="text-slate-400 block mb-1">Last Diagnostic Check</span>
            <span className="text-slate-400 font-mono">
              {healthResult.checkedAt.toLocaleTimeString()}
            </span>
          </div>
        </div>
      </section>

      {/* Role-Based Experience Placeholders */}
      <section className="space-y-6">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-sky-400">
            Platform Roles & Architecture
          </span>
          <h2 className="text-2xl font-bold text-white tracking-tight mt-1">
            Role-Based Workspaces (Planned for Module 2)
          </h2>
          <p className="text-sm text-slate-400 max-w-2xl mt-1">
            SkillProof AI structures specialized evaluation and administrative workflows for three distinct user types. Full authentication and dashboard views will activate in Module 2.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Student */}
          <RoleCard
            role="Student Archetype"
            title="Candidate Workspace"
            description="Upload verified project portfolios, take personalized skill-bounded assessments, practice DSA topics, and receive guarded progressive AI guidance."
            icon={GraduationCap}
            accentColor="bg-sky-500/10 border-sky-500/30 text-sky-400"
            features={[
              "Portfolio ingestion (.json, .pdf, .docx)",
              "Three tiered assessments (Novice, Adept, Master)",
              "Monaco editor & deterministic test grading",
              "CodeTrace problem-solving timeline",
            ]}
          />

          {/* College Administrator */}
          <RoleCard
            role="Academic Cohorts"
            title="College Administrator"
            description="Manage student cohorts and batches, deploy curriculum-aligned technical assessments, assign challenges with deadlines, and monitor class performance."
            icon={Building2}
            accentColor="bg-indigo-500/10 border-indigo-500/30 text-indigo-400"
            features={[
              "Batch & cohort enrollment management",
              "Custom assessment authoring & assignment",
              "Departmental coding challenge validation",
              "Cohort analytics and weakness diagnostics",
            ]}
          />

          {/* Recruiter */}
          <RoleCard
            role="Technical Hiring"
            title="Verified Recruiter"
            description="Discover candidates through verified technical proofs, review CodeTrace dossiers with explicit consent, and run live collaborative pair-coding interviews."
            icon={Briefcase}
            accentColor="bg-purple-500/10 border-purple-500/30 text-purple-400"
            features={[
              "Demonstrated skill-based candidate discovery",
              "Candidate consent-governed assessment reports",
              "Live interactive code workspace",
              "Dynamic requirement refactoring interviews",
            ]}
          />
        </div>
      </section>

      {/* 13-Module Progression Roadmap Overview */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-white">
              System Development Progression
            </h3>
            <p className="text-xs text-slate-400">
              Tracking the 13 sequential modules specified in <code className="text-slate-300 font-mono">PROJECT_REQUIREMENTS.md</code>
            </p>
          </div>
          <div className="text-xs text-slate-400 hidden sm:flex items-center space-x-1">
            <span>Next: Module 2 (Authentication)</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-sky-400" />
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-3 rounded-lg bg-sky-950/40 border border-sky-800/60">
            <span className="text-[10px] font-mono text-sky-400 font-bold block">PHASE 1</span>
            <span className="font-medium text-slate-200">Foundation</span>
            <span className="text-[11px] text-emerald-400 block mt-1">● Module 1 Active</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
            <span className="text-[10px] font-mono text-slate-500 font-bold block">PHASE 2</span>
            <span className="font-medium text-slate-300">Assessment Intelligence</span>
            <span className="text-[11px] text-slate-500 block mt-1">Modules 4–8</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
            <span className="text-[10px] font-mono text-slate-500 font-bold block">PHASE 3</span>
            <span className="font-medium text-slate-300">Assistance & Analytics</span>
            <span className="text-[11px] text-slate-500 block mt-1">Modules 9–10</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
            <span className="text-[10px] font-mono text-slate-500 font-bold block">PHASE 4</span>
            <span className="font-medium text-slate-300">Portals & Interviews</span>
            <span className="text-[11px] text-slate-500 block mt-1">Modules 11–13</span>
          </div>
        </div>
      </section>
    </main>
  );
};

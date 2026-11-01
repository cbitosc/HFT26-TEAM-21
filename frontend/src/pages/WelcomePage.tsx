/**
 * WelcomePage — Modern Entry Experience for SkillProof AI.
 *
 * Requirements:
 * - Replaces login-first experience with a frictionless, role-based guest entry.
 * - Heading: "Welcome to SkillProof AI"
 * - Subtitle: "Explore. Practice. Prove your skills."
 * - Three selectable roles: Student, College Administrator, Recruiter.
 * - Each role features an icon, short description, features, and direct launch button.
 * - Secondary option: "Already have an account? Sign in" linking to /login.
 * - Zero mandatory email/password fields on entry.
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  GraduationCap,
  Building2,
  Briefcase,
  Terminal,
  Sparkles,
  ArrowRight,
  Shield,
  Code2,
  Cpu,
  Lock,
  Layers,
  CheckCircle2,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/Button';
import { StatusBadge } from '../components/StatusBadge';
import { checkBackendHealth, HealthCheckResult } from '../services/api';
import { UserRole } from '../types/auth';

interface RoleOption {
  role: UserRole;
  title: string;
  badge: string;
  description: string;
  icon: React.ElementType;
  gradient: string;
  borderColor: string;
  textColor: string;
  buttonClass: string;
  features: string[];
}

const ROLES: RoleOption[] = [
  {
    role: 'student',
    title: 'Student Candidate',
    badge: 'Immediate Guest Demo',
    description:
      'Solve verified algorithmic challenges in Monaco editor, explore portfolio claim extraction, test progressive AI hints, and inspect CodeTrace problem-solving telemetry.',
    icon: GraduationCap,
    gradient: 'from-sky-500/10 via-sky-500/5 to-transparent',
    borderColor: 'border-sky-500/30 hover:border-sky-400',
    textColor: 'text-sky-400',
    buttonClass: 'bg-sky-600 hover:bg-sky-500 text-white shadow-sky-600/30',
    features: [
      'Interactive Monaco coding workspace',
      'Automated sample test-case runner',
      'Progressive AI assistant hints',
      'CodeTrace problem-solving metrics',
    ],
  },
  {
    role: 'college_admin',
    title: 'College Administrator',
    badge: 'Institutional Demo',
    description:
      'Explore curriculum-aligned coding task deployment, cohort assignment, automated submission grading with test cases, and class weakness diagnostics.',
    icon: Building2,
    gradient: 'from-indigo-500/10 via-indigo-500/5 to-transparent',
    borderColor: 'border-indigo-500/30 hover:border-indigo-400',
    textColor: 'text-indigo-400',
    buttonClass: 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/30',
    features: [
      'Custom task creation & test authoring',
      'Departmental submission evaluation',
      'Class cohort analytics & pass rates',
      'Safe isolated demo sandbox',
    ],
  },
  {
    role: 'recruiter',
    title: 'Technical Recruiter',
    badge: 'Hiring Portal Demo',
    description:
      'Discover verified candidates by empirical code execution scores, review candidate dossiers with CodeTrace telemetry, and test the collaborative pair-coding interview room.',
    icon: Briefcase,
    gradient: 'from-purple-500/10 via-purple-500/5 to-transparent',
    borderColor: 'border-purple-500/30 hover:border-purple-400',
    textColor: 'text-purple-400',
    buttonClass: 'bg-purple-600 hover:bg-purple-500 text-white shadow-purple-600/30',
    features: [
      'Verified skill candidate discovery',
      'Consent-governed candidate dossiers',
      'CodeTrace keystroke telemetry audit',
      'Live collaborative pair-coding room',
    ],
  },
];

export const WelcomePage: React.FC = () => {
  const { startGuestSession } = useAuth();
  const navigate = useNavigate();

  const [healthResult, setHealthResult] = useState<HealthCheckResult>({
    state: 'loading',
    data: null,
    error: null,
    checkedAt: new Date(),
  });
  const [isChecking, setIsChecking] = useState(false);

  useEffect(() => {
    setIsChecking(true);
    checkBackendHealth()
      .then(res => setHealthResult(res))
      .finally(() => setIsChecking(false));
  }, []);

  const handleSelectRole = (role: UserRole) => {
    startGuestSession(role);
    switch (role) {
      case 'student':
        navigate('/dashboard/student');
        break;
      case 'college_admin':
        navigate('/dashboard/college');
        break;
      case 'recruiter':
        navigate('/dashboard/recruiter');
        break;
      default:
        navigate('/dashboard/student');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-sky-500 selection:text-white">
      {/* Top Navbar */}
      <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-sky-400 flex items-center justify-center shadow-lg shadow-sky-500/10">
              <Terminal className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-white tracking-tight">
                  SkillProof<span className="text-sky-400">AI</span>
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Portfolio-Driven Adaptive Assessment
              </p>
            </div>
          </Link>

          <div className="flex items-center space-x-3">
            {/* Backend status badge */}
            <StatusBadge
              state={healthResult.state}
              onRefresh={() => {
                setIsChecking(true);
                checkBackendHealth().then(r => setHealthResult(r)).finally(() => setIsChecking(false));
              }}
              isRefreshing={isChecking}
            />

            <div className="flex items-center space-x-2">
              <Link to="/login">
                <Button variant="ghost" className="text-xs py-1.5 px-3">
                  Sign in
                </Button>
              </Link>
              <Link to="/register">
                <Button variant="primary" className="text-xs py-1.5 px-3">
                  Register
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-16 space-y-16">
        {/* Hero Section */}
        <section className="text-center space-y-5 max-w-3xl mx-auto">
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-sky-950/80 border border-sky-800/60 text-sky-300 shadow-inner">
            <Sparkles className="w-3.5 h-3.5 text-sky-400 animate-pulse" />
            <span>Instant Demo Access • No Registration Required</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-black text-white tracking-tight leading-tight">
            Welcome to{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 via-indigo-300 to-purple-400">
              SkillProof AI
            </span>
          </h1>

          <p className="text-xl sm:text-2xl font-medium text-slate-200">
            Explore. Practice. Prove your skills.
          </p>

          <p className="text-sm sm:text-base text-slate-400 leading-relaxed max-w-2xl mx-auto">
            Experience our adaptive technical assessment platform. Select a role below to launch an instant guest session with simulated coding challenges, portfolio analysis, and live telemetry.
          </p>
        </section>

        {/* 3 Role Selection Cards */}
        <section className="space-y-6">
          <div className="text-center">
            <span className="text-xs font-bold uppercase tracking-wider text-sky-400">
              Choose an Experience to Begin
            </span>
            <h2 className="text-2xl font-extrabold text-white mt-1">
              Select Your Workspace
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {ROLES.map(opt => {
              const Icon = opt.icon;
              return (
                <div
                  key={opt.role}
                  className={`rounded-2xl border ${opt.borderColor} bg-gradient-to-b ${opt.gradient} bg-slate-900/60 p-7 flex flex-col justify-between space-y-6 transition-all duration-300 hover:shadow-2xl hover:scale-[1.02] backdrop-blur-sm group`}
                >
                  <div className="space-y-4">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                      <div className={`w-12 h-12 rounded-xl bg-slate-800/80 border border-slate-700/80 flex items-center justify-center ${opt.textColor} shadow-md group-hover:scale-110 transition-transform`}>
                        <Icon className="w-6 h-6" />
                      </div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 bg-slate-800/90 border border-slate-700 px-2.5 py-1 rounded-full">
                        {opt.badge}
                      </span>
                    </div>

                    <div>
                      <h3 className="text-xl font-bold text-white group-hover:text-sky-300 transition-colors">
                        {opt.title}
                      </h3>
                      <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                        {opt.description}
                      </p>
                    </div>

                    {/* Features bullet list */}
                    <ul className="space-y-2 pt-2 border-t border-slate-800/80">
                      {opt.features.map((feat, idx) => (
                        <li key={idx} className="flex items-center space-x-2 text-xs text-slate-300">
                          <CheckCircle2 className={`w-3.5 h-3.5 ${opt.textColor} flex-shrink-0`} />
                          <span>{feat}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Launch Button */}
                  <button
                    onClick={() => handleSelectRole(opt.role)}
                    className={`w-full py-3 px-4 rounded-xl font-semibold text-xs tracking-wide shadow-lg flex items-center justify-center space-x-2 transition-all transform active:scale-95 ${opt.buttonClass}`}
                  >
                    <span>Explore as {opt.title}</span>
                    <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                  </button>
                </div>
              );
            })}
          </div>
        </section>

        {/* Secondary Authentication Option */}
        <section className="rounded-2xl border border-slate-800/80 bg-slate-900/40 p-8 backdrop-blur-sm">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 text-center md:text-left">
            <div className="space-y-1.5 max-w-xl">
              <div className="flex items-center justify-center md:justify-start space-x-2">
                <Lock className="w-4 h-4 text-sky-400" />
                <h3 className="text-base font-bold text-white">
                  Already have an account?
                </h3>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Sign in to access your permanent student portfolio, verified assessment history, college task deadlines, or approved recruiter candidate discovery.
              </p>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-3">
              <Link to="/login">
                <Button variant="primary" className="text-xs py-2 px-5 shadow-lg shadow-sky-500/20">
                  Sign In to Account
                </Button>
              </Link>
              <Link to="/register">
                <Button variant="secondary" className="text-xs py-2 px-5">
                  Create Account
                </Button>
              </Link>
            </div>
          </div>
        </section>

        {/* Platform Pillars */}
        <section className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-slate-800/60 text-xs">
          <div className="flex items-center space-x-2.5 p-3 rounded-xl bg-slate-900/30 border border-slate-800/60">
            <Shield className="w-4 h-4 text-sky-400 flex-shrink-0" />
            <span className="text-slate-300 font-medium">100% Deterministic Grading</span>
          </div>
          <div className="flex items-center space-x-2.5 p-3 rounded-xl bg-slate-900/30 border border-slate-800/60">
            <Code2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <span className="text-slate-300 font-medium">CodeTrace Telemetry</span>
          </div>
          <div className="flex items-center space-x-2.5 p-3 rounded-xl bg-slate-900/30 border border-slate-800/60">
            <Cpu className="w-4 h-4 text-indigo-400 flex-shrink-0" />
            <span className="text-slate-300 font-medium">Guarded AI Assistance</span>
          </div>
          <div className="flex items-center space-x-2.5 p-3 rounded-xl bg-slate-900/30 border border-slate-800/60">
            <Layers className="w-4 h-4 text-purple-400 flex-shrink-0" />
            <span className="text-slate-300 font-medium">Consent-Governed Discovery</span>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500 bg-slate-950/60">
        <p>SkillProof AI • Portfolio-Driven Adaptive Technical Assessment Platform • Zero Cost Architecture</p>
      </footer>
    </div>
  );
};

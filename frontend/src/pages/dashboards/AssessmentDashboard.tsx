/**
 * AssessmentDashboard — Module 6: Assessment Hub & Skill Improvement Launcher.
 * Allows candidates to launch Verified Assessments or Practice Sessions across Novice, Adept, and Master tiers.
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Code2,
  Sparkles,
  ShieldCheck,
  BookOpen,
  ArrowRight,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Award,
  Layers,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { fetchStudentPortfolio } from '../../services/portfolio';
import { generateAssessment, fetchAssessmentHistory } from '../../services/assessment';
import { PortfolioResponse } from '../../types/portfolio';
import { Button } from '../../components/Button';
import { Alert } from '../../components/Alert';
import { DEMO_STUDENT_PORTFOLIO } from '../../services/demoData';

export const AssessmentDashboard: React.FC = () => {
  const { session, isGuest } = useAuth();
  const token = session?.access_token || '';
  const navigate = useNavigate();

  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [isStarting, setIsStarting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Configuration choices
  const [track, setTrack] = useState<'verified' | 'practice'>('verified');
  const [tier, setTier] = useState<'novice' | 'adept' | 'master'>('novice');
  const [selectedDomain, setSelectedDomain] = useState<string>('Algorithms & DSA');

  const DOMAIN_OPTIONS = [
    'Algorithms & DSA',
    'Backend Development',
    'Web Development',
    'Cloud Computing',
  ];

  useEffect(() => {
    if (isGuest) {
      setPortfolio(DEMO_STUDENT_PORTFOLIO);
      setHistory([
        {
          session_id: 'demo-session-sample',
          tier: 'novice',
          track: 'practice',
          domain: 'Algorithms & DSA',
          status: 'completed',
          score_percentage: 85.0,
          created_at: new Date(Date.now() - 86400000).toISOString(),
        },
      ]);
      return;
    }

    if (!token) return;
    Promise.all([
      fetchStudentPortfolio(token).catch(() => null),
      fetchAssessmentHistory(token).catch(() => []),
    ]).then(([pData, hData]) => {
      if (pData) {
        setPortfolio(pData);
        if (pData.data.domains && pData.data.domains.length > 0) {
          setSelectedDomain(pData.data.domains[0]);
        }
      }
      setHistory(hData);
    });
  }, [token, isGuest]);

  const handleStartAssessment = async () => {
    if (isGuest) {
      navigate('/dashboard/student/assessment/demo-session-guest');
      return;
    }

    if (!token) return;
    setIsStarting(true);
    setError(null);

    try {
      const sessionRes = await generateAssessment(
        {
          tier,
          track,
          domain_filter: selectedDomain,
          preferred_language: 'python',
        },
        token
      );
      navigate(`/dashboard/student/assessment/${sessionRes.session_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Could not generate assessment session.');
      setIsStarting(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium bg-indigo-950/80 border border-indigo-800/60 text-indigo-300">
          <Code2 className="w-3.5 h-3.5" />
          <span>Modules 5 & 6 · Adaptive Evaluation</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
          Coding Assessment & Skill Improvement
        </h1>
        <p className="text-sm text-slate-400 max-w-2xl">
          Take portfolio-aligned verified coding assessments to prove verified competency, or sharpen your skills in isolated practice mode.
        </p>
      </div>

      {error && <Alert variant="error" message={error} />}

      {/* Portfolio Alignment Notice */}
      {portfolio && portfolio.confirmed ? (
        <div className="rounded-xl border border-emerald-900/60 bg-emerald-950/20 p-4 flex items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
            <div className="text-xs text-slate-300">
              <span className="font-semibold text-white">Portfolio Boundary Active:</span> Challenges are dynamically aligned with your {portfolio.data.skills.programming_languages.length + portfolio.data.skills.frameworks_and_tools.length} claimed skills and {portfolio.data.domains.length} technical domains.
            </div>
          </div>
          <Link
            to="/dashboard/student/portfolio"
            className="text-xs text-emerald-400 hover:text-emerald-300 font-semibold whitespace-nowrap transition"
          >
            Review Scope →
          </Link>
        </div>
      ) : (
        <div className="rounded-xl border border-amber-900/60 bg-amber-950/20 p-4 flex items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" />
            <div className="text-xs text-slate-300">
              <span className="font-semibold text-white">Portfolio Not Yet Confirmed:</span> Assessments will default to fundamental diagnostic challenges. Confirm your portfolio to personalize assessment topics.
            </div>
          </div>
          <Link
            to="/dashboard/student/portfolio"
            className="text-xs text-amber-400 hover:text-amber-300 font-semibold whitespace-nowrap transition"
          >
            Upload Portfolio →
          </Link>
        </div>
      )}

      {/* Launcher Configuration Card */}
      <section className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 sm:p-8 space-y-8">
        {/* Track Selection */}
        <div className="space-y-3">
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            1. Select Evaluation Track
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div
              onClick={() => setTrack('verified')}
              className={`p-5 rounded-xl border cursor-pointer transition flex items-start space-x-4 ${
                track === 'verified'
                  ? 'border-sky-500 bg-sky-950/30 ring-1 ring-sky-500/50'
                  : 'border-slate-800 hover:border-slate-700 bg-slate-950/40'
              }`}
            >
              <div className="w-10 h-10 rounded-lg bg-sky-950 flex items-center justify-center text-sky-400 flex-shrink-0">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <h3 className="text-sm font-semibold text-white">Verified Assessment</h3>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-800">
                    Formal Track
                  </span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Deterministic grading recorded directly in your candidate proof dossier for recruiter review.
                </p>
              </div>
            </div>

            <div
              onClick={() => setTrack('practice')}
              className={`p-5 rounded-xl border cursor-pointer transition flex items-start space-x-4 ${
                track === 'practice'
                  ? 'border-indigo-500 bg-indigo-950/30 ring-1 ring-indigo-500/50'
                  : 'border-slate-800 hover:border-slate-700 bg-slate-950/40'
              }`}
            >
              <div className="w-10 h-10 rounded-lg bg-indigo-950 flex items-center justify-center text-indigo-400 flex-shrink-0">
                <BookOpen className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <h3 className="text-sm font-semibold text-white">Skill Improvement (Practice)</h3>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                    Isolated
                  </span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Zero risk sandbox. Practice trial runs are kept strictly isolated and never impact your formal verified score.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Tier Selection */}
        <div className="space-y-3">
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            2. Choose Difficulty Tier
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              {
                id: 'novice',
                title: 'Novice (Easy)',
                description: 'Single-function algorithms, string parsing & core logic.',
                icon: Layers,
                accent: 'text-emerald-400',
                border: 'hover:border-emerald-700',
                active: 'border-emerald-500 bg-emerald-950/20 ring-1 ring-emerald-500/40',
              },
              {
                id: 'adept',
                title: 'Adept (Medium)',
                description: 'Multi-step algorithms, sliding window, tree traversals & caching.',
                icon: Flame,
                accent: 'text-amber-400',
                border: 'hover:border-amber-700',
                active: 'border-amber-500 bg-amber-950/20 ring-1 ring-amber-500/40',
              },
              {
                id: 'master',
                title: 'Master (Hard)',
                description: 'System design algorithms, monotonic stacks, heaps & distributed consensus.',
                icon: Award,
                accent: 'text-rose-400',
                border: 'hover:border-rose-700',
                active: 'border-rose-500 bg-rose-950/20 ring-1 ring-rose-500/40',
              },
            ].map(item => {
              const Icon = item.icon;
              const isSelected = tier === item.id;
              return (
                <div
                  key={item.id}
                  onClick={() => setTier(item.id as any)}
                  className={`p-4 rounded-xl border cursor-pointer transition space-y-2 ${
                    isSelected ? item.active : `border-slate-800 ${item.border} bg-slate-950/40`
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <Icon className={`w-4 h-4 ${item.accent}`} />
                    <h4 className="text-xs font-bold text-white">{item.title}</h4>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">{item.description}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Domain Filter */}
        <div className="space-y-3">
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            3. Target Technical Domain
          </label>
          <div className="flex flex-wrap items-center gap-2">
            {DOMAIN_OPTIONS.map(dom => (
              <button
                key={dom}
                type="button"
                onClick={() => setSelectedDomain(dom)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  selectedDomain === dom
                    ? 'bg-sky-600 text-white shadow-md shadow-sky-600/20'
                    : 'bg-slate-800 text-slate-400 hover:text-white border border-slate-700'
                }`}
              >
                {dom}
              </button>
            ))}
          </div>
        </div>

        {/* Launch Action */}
        <div className="pt-4 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="text-xs text-slate-400 space-y-0.5">
            <p className="font-semibold text-white">Assembled by SkillProof AI Assessment Agent</p>
            <p>Pulls 2–3 pre-verified questions with automated test suites.</p>
          </div>
          <Button
            variant="primary"
            className="py-3 px-8 text-sm font-bold"
            onClick={handleStartAssessment}
            isLoading={isStarting}
          >
            <Sparkles className="w-4 h-4 mr-2" />
            Start Assessment Now
          </Button>
        </div>
      </section>

      {/* Assessment History Section */}
      <section className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="text-base font-semibold text-white flex items-center space-x-2">
          <Clock className="w-4 h-4 text-slate-400" />
          <span>Past Assessment Runs</span>
        </h2>

        {history.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-6 text-center">
            No assessment attempts yet. Select your tier above and start your first evaluation!
          </p>
        ) : (
          <div className="space-y-3">
            {history.map(item => (
              <div
                key={item.session_id}
                className="p-4 rounded-lg border border-slate-800 bg-slate-950/50 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-semibold text-white capitalize">
                      {item.tier} Assessment
                    </span>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                        item.track === 'verified'
                          ? 'bg-sky-950 text-sky-400 border border-sky-800'
                          : 'bg-indigo-950 text-indigo-400 border border-indigo-800'
                      }`}
                    >
                      {item.track}
                    </span>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                        item.status === 'completed'
                          ? 'bg-emerald-950 text-emerald-400'
                          : 'bg-amber-950 text-amber-400'
                      }`}
                    >
                      {item.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Domain: {item.domain} · Started:{' '}
                    {new Date(item.created_at).toLocaleDateString()} at{' '}
                    {new Date(item.created_at).toLocaleTimeString()}
                  </p>
                </div>

                <div className="flex items-center space-x-3">
                  {item.status === 'completed' && item.score_percentage !== undefined && (
                    <span className="text-sm font-bold text-emerald-400">
                      Score: {item.score_percentage}%
                    </span>
                  )}
                  <Link
                    to={
                      item.status === 'completed'
                        ? `/dashboard/student/assessment/${item.session_id}/summary`
                        : `/dashboard/student/assessment/${item.session_id}`
                    }
                    className="inline-flex items-center space-x-1 text-xs font-semibold text-sky-400 hover:text-sky-300 transition"
                  >
                    <span>{item.status === 'completed' ? 'View Results' : 'Resume'}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

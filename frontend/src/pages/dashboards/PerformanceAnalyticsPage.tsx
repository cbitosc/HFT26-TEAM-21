/**
 * PerformanceAnalyticsPage — Module 10: Performance Analytics and Deterministic Scoring.
 *
 * Renders a comprehensive student performance dashboard using Recharts:
 *  - Composite score trend (line chart) across sessions
 *  - Domain pass-rate breakdown (horizontal bar chart)
 *  - Tier mastery comparison (grouped bar chart)
 *  - AI hint utilization distribution (bar chart)
 *  - Transparent scoring formula disclosure
 *
 * All data is computed deterministically on the backend — no LLM grading.
 * Practice sessions are clearly labeled and separated from verified results.
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart2,
  TrendingUp,
  Target,
  Lightbulb,
  ShieldCheck,
  BookOpen,
  Info,
  ArrowRight,
  Loader2,
  Award,
  CheckCircle2,
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts';
import { useAuth } from '../../contexts/AuthContext';
import { fetchAnalytics } from '../../services/assessment';
import { AnalyticsResponse, TrendPoint, DomainPerformance, SkillMasteryItem } from '../../types/assessment';
import { Alert } from '../../components/Alert';
import { DEMO_STUDENT_ANALYTICS } from '../../services/demoData';

// ---------------------------------------------------------------------------
// Palette helpers
// ---------------------------------------------------------------------------

const TIER_COLORS: Record<string, string> = {
  novice: '#38bdf8',   // sky-400
  adept: '#a78bfa',    // violet-400
  master: '#f59e0b',   // amber-400
};

const DOMAIN_COLORS = ['#38bdf8', '#a78bfa', '#34d399', '#f59e0b', '#f87171', '#818cf8'];

const scoreBand = (score: number) => {
  if (score >= 80) return { label: 'Excellent', color: 'text-emerald-400' };
  if (score >= 60) return { label: 'Good', color: 'text-sky-400' };
  if (score >= 40) return { label: 'Developing', color: 'text-amber-400' };
  return { label: 'Needs Work', color: 'text-rose-400' };
};

// ---------------------------------------------------------------------------
// Stat card
// ---------------------------------------------------------------------------

const StatCard: React.FC<{
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}> = ({ label, value, sub, color = 'text-white' }) => (
  <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 space-y-1">
    <p className="text-[11px] text-slate-400 font-medium uppercase tracking-wider">{label}</p>
    <p className={`text-2xl font-black ${color}`}>{value}</p>
    {sub && <p className="text-[11px] text-slate-500">{sub}</p>}
  </div>
);

// ---------------------------------------------------------------------------
// Custom Recharts Tooltip
// ---------------------------------------------------------------------------

const TrendTooltip: React.FC<any> = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs space-y-1 shadow-lg">
      <p className="font-semibold text-white">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name}: <span className="font-bold">{typeof p.value === 'number' ? p.value.toFixed(1) : p.value}</span>
        </p>
      ))}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export const PerformanceAnalyticsPage: React.FC = () => {
  const { session, isGuest } = useAuth();
  const token = session?.access_token || '';

  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isGuest) {
      setAnalytics(DEMO_STUDENT_ANALYTICS);
      setIsLoading(false);
      return;
    }

    if (!token) return;
    setIsLoading(true);
    fetchAnalytics(token)
      .then(data => {
        setAnalytics(data);
        setIsLoading(false);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load analytics.');
        setIsLoading(false);
      });
  }, [token, isGuest]);

  if (isLoading) {
    return (
      <div className="p-16 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
        <Loader2 className="w-8 h-8 animate-spin text-sky-400" />
        <p className="text-sm">Computing deterministic performance analytics…</p>
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="space-y-4 max-w-xl mx-auto py-12 text-center">
        <Alert variant="error" message={error || 'Analytics could not be loaded.'} />
        {analytics?.total_sessions === 0 && (
          <p className="text-xs text-slate-400">Complete at least one assessment to see your analytics.</p>
        )}
        <Link to="/dashboard/student/assessments" className="text-sky-400 text-xs font-semibold">
          Go to Assessments
        </Link>
      </div>
    );
  }

  // Empty state
  if (analytics.total_sessions === 0) {
    return (
      <div className="space-y-6 max-w-2xl mx-auto py-12 text-center">
        <BarChart2 className="w-12 h-12 text-slate-600 mx-auto" />
        <div>
          <h2 className="text-xl font-bold text-white">No Assessment Data Yet</h2>
          <p className="text-sm text-slate-400 mt-2">
            Complete at least one assessment to generate your performance analytics report.
          </p>
        </div>
        <Link
          to="/dashboard/student/assessments"
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold transition"
        >
          <span>Start an Assessment</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    );
  }

  const band = scoreBand(analytics.overall_avg_composite);

  // Prepare trend chart data (max 10 most recent)
  const trendData = analytics.trend.slice(-10).map((t: TrendPoint, idx: number) => ({
    name: `#${analytics.trend.length > 10 ? analytics.trend.length - 10 + idx + 1 : idx + 1}`,
    date: t.date,
    'Composite Score': t.composite_score,
    'Test Score': t.test_score,
    'AI Efficiency': t.ai_efficiency_score,
    tier: t.tier,
    track: t.track,
    domain: t.domain,
  }));

  // Domain bar chart data
  const domainData = analytics.domain_performance.map((d: DomainPerformance) => ({
    name: d.domain.length > 18 ? d.domain.slice(0, 16) + '…' : d.domain,
    fullName: d.domain,
    'Pass Rate': d.pass_rate,
    sessions: d.sessions,
  }));

  // Tier mastery data
  const tierOrder = ['novice', 'adept', 'master'];
  const masteryData = tierOrder
    .map(tier => analytics.skill_mastery.find((m: SkillMasteryItem) => m.tier === tier))
    .filter(Boolean)
    .map((m: SkillMasteryItem | undefined) => ({
      name: m!.tier.charAt(0).toUpperCase() + m!.tier.slice(1),
      tier: m!.tier,
      'Avg Score': m!.avg_composite_score,
      'Best Score': m!.best_composite_score,
      sessions: m!.sessions,
    }));

  // Hint distribution data
  const hintData = [
    { name: 'Level 1\nNudge', value: analytics.hint_utilization.level_1_hints, fill: '#38bdf8' },
    { name: 'Level 2\nStrategy', value: analytics.hint_utilization.level_2_hints, fill: '#a78bfa' },
    { name: 'Level 3\nPseudocode', value: analytics.hint_utilization.level_3_hints, fill: '#f59e0b' },
  ];

  return (
    <div className="space-y-8 max-w-6xl mx-auto">

      {/* Page Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium bg-emerald-950/80 border border-emerald-800/60 text-emerald-300">
          <BarChart2 className="w-3.5 h-3.5" />
          <span>Performance Analytics — Module 10</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
          Your Skill Analytics Dashboard
        </h1>
        <p className="text-sm text-slate-400">
          Deterministic composite scores across {analytics.total_sessions} assessment session{analytics.total_sessions !== 1 ? 's' : ''}
          {' '}·{' '}
          <span className="text-slate-500 text-xs">
            Generated {new Date(analytics.generated_at).toLocaleString()}
          </span>
        </p>
      </div>

      {/* Top Summary Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard
          label="Verified Composite"
          value={analytics.verified_sessions > 0 ? `${analytics.overall_avg_composite}%` : 'N/A'}
          sub={analytics.verified_sessions > 0 ? band.label : 'No verified sessions'}
          color={band.color}
        />
        <StatCard
          label="Verified Best"
          value={analytics.verified_sessions > 0 ? `${analytics.best_composite_score}%` : 'N/A'}
          sub="Single verified session"
          color="text-emerald-400"
        />
        <StatCard
          label="Verified Pass Rate"
          value={analytics.verified_sessions > 0 ? `${analytics.overall_test_pass_rate}%` : 'N/A'}
          sub="Across verified tests"
        />
        <StatCard
          label="Total Sessions"
          value={analytics.total_sessions}
          sub={`${analytics.verified_sessions} verified · ${analytics.practice_sessions} practice`}
        />
        <StatCard
          label="Hints Requested"
          value={analytics.hint_utilization.total_hint_requests}
          sub={`${analytics.hint_utilization.avg_hints_per_session} avg/session`}
        />
        <StatCard
          label="AI Efficiency"
          value={`${analytics.hint_utilization.ai_efficiency_avg}/20`}
          sub="Avg across sessions"
          color="text-indigo-300"
        />
      </div>

      {/* Track separation notice */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="rounded-xl border border-sky-900/60 bg-sky-950/20 p-4 flex items-start space-x-3">
          <ShieldCheck className="w-5 h-5 text-sky-400 flex-shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <p className="font-semibold text-white">Verified Sessions: {analytics.verified_sessions}</p>
            <p className="text-slate-400">Composite average derived strictly from verified assessments. Practice sessions never pollute candidate scores.</p>
          </div>
        </div>
        <div className="rounded-xl border border-indigo-900/60 bg-indigo-950/20 p-4 flex items-start space-x-3">
          <BookOpen className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <p className="font-semibold text-white">
              Practice Sessions: {analytics.practice_sessions}
              {analytics.practice_avg_composite !== null && analytics.practice_avg_composite !== undefined
                ? ` · Avg: ${analytics.practice_avg_composite}%`
                : ''}
            </p>
            <p className="text-slate-400">Strictly isolated from verified candidate scores. Practice data never inflates your recruiter-facing ratings.</p>
          </div>
        </div>
      </div>

      {/* ── Chart 1: Composite Score Trend ── */}
      {trendData.length > 0 && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-sky-400" />
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
              Composite Score Trend (last {trendData.length} sessions)
            </h2>
          </div>
          <p className="text-xs text-slate-500">
            Composite = Test Score (max 80) + AI Efficiency (max 20). Hover for details.
          </p>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={trendData} margin={{ top: 8, right: 16, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip content={<TrendTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
              <ReferenceLine y={60} stroke="#475569" strokeDasharray="4 2" label={{ value: 'Good', fill: '#475569', fontSize: 10 }} />
              <Line
                type="monotone"
                dataKey="Composite Score"
                stroke="#38bdf8"
                strokeWidth={2.5}
                dot={{ fill: '#38bdf8', r: 4 }}
                activeDot={{ r: 6 }}
              />
              <Line
                type="monotone"
                dataKey="Test Score"
                stroke="#34d399"
                strokeWidth={1.5}
                strokeDasharray="5 3"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="AI Efficiency"
                stroke="#a78bfa"
                strokeWidth={1.5}
                strokeDasharray="3 3"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* ── Chart 2: Domain Pass Rate ── */}
      {domainData.length > 0 && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center space-x-2">
            <Target className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
              Domain Pass Rate
            </h2>
          </div>
          <p className="text-xs text-slate-500">
            Percentage of questions passed per technical domain across all sessions.
          </p>
          <ResponsiveContainer width="100%" height={Math.max(180, domainData.length * 48)}>
            <BarChart
              data={domainData}
              layout="vertical"
              margin={{ top: 4, right: 40, left: 8, bottom: 4 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }}
                tickFormatter={(v) => `${v}%`} />
              <YAxis dataKey="name" type="category" width={120} tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip content={<TrendTooltip />} />
              <Bar dataKey="Pass Rate" radius={[0, 4, 4, 0]} maxBarSize={24}>
                {domainData.map((_entry, index) => (
                  <Cell key={`domain-${index}`} fill={DOMAIN_COLORS[index % DOMAIN_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* ── Chart 3: Tier Mastery ── */}
      {masteryData.length > 0 && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center space-x-2">
            <Award className="w-4 h-4 text-amber-400" />
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
              Tier Mastery Comparison
            </h2>
          </div>
          <p className="text-xs text-slate-500">
            Average and best composite scores per difficulty tier.
          </p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={masteryData} margin={{ top: 8, right: 16, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip content={<TrendTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
              <Bar dataKey="Avg Score" maxBarSize={32} radius={[4, 4, 0, 0]}>
                {masteryData.map((entry) => (
                  <Cell key={entry.name} fill={TIER_COLORS[entry.tier] || '#64748b'} fillOpacity={0.8} />
                ))}
              </Bar>
              <Bar dataKey="Best Score" maxBarSize={32} radius={[4, 4, 0, 0]}>
                {masteryData.map((entry) => (
                  <Cell key={entry.name} fill={TIER_COLORS[entry.tier] || '#64748b'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          {/* Tier detail cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
            {masteryData.map((m) => (
              <div key={m.name} className="bg-slate-950/60 border border-slate-800 rounded-xl p-3 space-y-1">
                <div className="flex items-center space-x-2">
                  <span
                    className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: TIER_COLORS[m.tier] || '#64748b' }}
                  />
                  <p className="text-xs font-bold text-white capitalize">{m.name}</p>
                </div>
                <p className="text-[11px] text-slate-400">{m.sessions} session{m.sessions !== 1 ? 's' : ''}</p>
                <p className="text-[11px] text-slate-400">Avg: <span className="font-semibold text-white">{m['Avg Score']}%</span></p>
                <p className="text-[11px] text-slate-400">Best: <span className="font-semibold text-emerald-400">{m['Best Score']}%</span></p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Chart 4: AI Hint Utilization ── */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center space-x-2">
          <Lightbulb className="w-4 h-4 text-indigo-400" />
          <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
            AI Hint Utilization
          </h2>
        </div>
        <p className="text-xs text-slate-500">
          Distribution of hint requests by depth level. Deeper hints indicate more structured problem decomposition.
        </p>

        {analytics.hint_utilization.total_hint_requests === 0 ? (
          <div className="text-center py-6 space-y-1">
            <Lightbulb className="w-8 h-8 text-slate-700 mx-auto" />
            <p className="text-xs text-slate-500">No AI hints were requested in any session.</p>
          </div>
        ) : (
          <>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={hintData} margin={{ top: 8, right: 16, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Tooltip content={<TrendTooltip />} />
                <Bar dataKey="value" maxBarSize={40} radius={[4, 4, 0, 0]} name="Hints">
                  {hintData.map((entry, index) => (
                    <Cell key={index} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            <div className="grid grid-cols-3 gap-3">
              <div className="text-center bg-slate-950/60 border border-sky-900/40 rounded-xl p-3">
                <p className="text-xs font-bold text-sky-300">Level 1 (Nudge)</p>
                <p className="text-2xl font-black text-white">{analytics.hint_utilization.level_1_hints}</p>
              </div>
              <div className="text-center bg-slate-950/60 border border-violet-900/40 rounded-xl p-3">
                <p className="text-xs font-bold text-violet-300">Level 2 (Strategy)</p>
                <p className="text-2xl font-black text-white">{analytics.hint_utilization.level_2_hints}</p>
              </div>
              <div className="text-center bg-slate-950/60 border border-amber-900/40 rounded-xl p-3">
                <p className="text-xs font-bold text-amber-300">Level 3 (Pseudocode)</p>
                <p className="text-2xl font-black text-white">{analytics.hint_utilization.level_3_hints}</p>
              </div>
            </div>
          </>
        )}

        {/* AI Efficiency score explanation */}
        <div className="mt-2 p-3 rounded-lg bg-indigo-950/30 border border-indigo-900/40 flex items-start space-x-2">
          <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0 mt-0.5" />
          <div className="text-[11px] text-indigo-300 leading-relaxed">
            <span className="font-semibold">AI Usage Efficiency Score:</span>{' '}
            <span className="text-indigo-400 font-bold">{analytics.hint_utilization.ai_efficiency_avg}/20</span>{' '}
            average. Derived deterministically: self-sufficient solvers receive full baseline (20/20); assisted solvers
            are rewarded for active test verification and constructive code progression following guidance. No LLM grading used.
          </div>
        </div>
      </div>

      {/* Scoring Formula Transparency Panel */}
      <div className="rounded-xl border border-slate-700/60 bg-slate-900/40 p-5 space-y-3">
        <div className="flex items-start space-x-3">
          <Info className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-2">
            <p className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Transparent Scoring Formula
            </p>
            <p className="text-xs text-slate-400 leading-relaxed">
              {analytics.scoring_formula_note}
            </p>
          </div>
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="pt-4 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Link
          to="/dashboard/student"
          className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-400 hover:text-white transition"
        >
          <span>← Back to Dashboard</span>
        </Link>
        <Link
          to="/dashboard/student/assessments"
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold transition"
        >
          <span>Take New Assessment</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};

/**
 * AssessmentSummaryPage — Modules 6 & 8: Assessment Results & CodeTrace Journey.
 * Displays transparent, deterministic performance metrics, pass/fail test assertions,
 * and CodeTrace timeline reconstructing the candidate's development journey.
 */

import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Award,
  CheckCircle2,
  XCircle,
  ShieldCheck,
  BookOpen,
  ArrowRight,
  RotateCcw,
  Loader2,
  GitCommit,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import {
  fetchAssessmentSession,
  fetchCodeTraceTimeline,
} from '../../services/assessment';
import {
  CodeTraceTimelineResponse,
  CodeTraceEvent,
} from '../../types/assessment';
import { Alert } from '../../components/Alert';

export const AssessmentSummaryPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { session } = useAuth();
  const token = session?.access_token || '';

  const [summary, setSummary] = useState<any | null>(null);
  const [timeline, setTimeline] = useState<CodeTraceTimelineResponse | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<CodeTraceEvent | null>(null);
  const [showTimeline, setShowTimeline] = useState<boolean>(true);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId || !token) return;
    setIsLoading(true);

    Promise.all([
      fetchAssessmentSession(sessionId, token),
      fetchCodeTraceTimeline(sessionId, token).catch(() => null),
    ])
      .then(([sessionData, timelineData]) => {
        setSummary(sessionData);
        setTimeline(timelineData);
        setIsLoading(false);
      })
      .catch((err: any) => {
        setError(err.message || 'Could not load assessment summary.');
        setIsLoading(false);
      });
  }, [sessionId, token]);

  if (isLoading) {
    return (
      <div className="p-16 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
        <Loader2 className="w-8 h-8 animate-spin text-sky-400" />
        <p className="text-sm">Retrieving assessment results & CodeTrace timeline…</p>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="space-y-4 max-w-xl mx-auto py-12 text-center">
        <Alert variant="error" message={error || 'Assessment report could not be found.'} />
        <Link to="/dashboard/student/assessments" className="text-sky-400 text-xs font-semibold">
          Return to Assessment Hub
        </Link>
      </div>
    );
  }

  const score = summary.score_percentage ?? 0;
  const isPractice = summary.track === 'practice';
  const results = summary.results || [];

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium bg-emerald-950/80 border border-emerald-800/60 text-emerald-300">
          <Award className="w-3.5 h-3.5" />
          <span>Evaluation Complete</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
          Assessment Performance Report
        </h1>
        <p className="text-sm text-slate-400">
          Transparent, deterministic score breakdown verified across public and hidden test suites.
        </p>
      </div>

      {/* Main Score Hero Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 flex flex-col sm:flex-row sm:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <span
              className={`text-xs font-mono px-2.5 py-0.5 rounded-full border ${
                isPractice
                  ? 'bg-indigo-950/80 text-indigo-300 border-indigo-800'
                  : 'bg-sky-950/80 text-sky-300 border-sky-800'
              }`}
            >
              {isPractice ? 'Skill Improvement Sandbox' : 'Verified Assessment Track'}
            </span>
            <span className="text-xs font-mono text-slate-400 uppercase">
              {summary.tier} Tier
            </span>
          </div>

          <h2 className="text-lg font-bold text-white capitalize">
            {summary.domain || 'Algorithms & Technical Challenges'}
          </h2>

          <p className="text-xs text-slate-400">
            Completed on {new Date(summary.completed_at || summary.created_at).toLocaleDateString()} at{' '}
            {new Date(summary.completed_at || summary.created_at).toLocaleTimeString()}
          </p>
        </div>

        {/* Circular / Badge Score */}
        <div className="flex items-center space-x-4 bg-slate-950/60 px-6 py-4 rounded-xl border border-slate-800/80">
          <div className="text-right">
            <div className="text-3xl font-black text-white">{score}%</div>
            <div className="text-[11px] text-slate-400 font-medium">
              Overall Correctness
            </div>
          </div>
          <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center text-emerald-400">
            {score >= 70 ? (
              <CheckCircle2 className="w-7 h-7 text-emerald-400" />
            ) : (
              <Award className="w-7 h-7 text-amber-400" />
            )}
          </div>
        </div>
      </div>

      {/* Track Policy Alert */}
      <div
        className={`rounded-xl border p-4 flex items-start space-x-3 ${
          isPractice
            ? 'border-indigo-900/60 bg-indigo-950/20'
            : 'border-sky-900/60 bg-sky-950/20'
        }`}
      >
        {isPractice ? (
          <BookOpen className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
        ) : (
          <ShieldCheck className="w-5 h-5 text-sky-400 flex-shrink-0 mt-0.5" />
        )}
        <div className="text-xs text-slate-300 space-y-1">
          <p className="font-semibold text-white">
            {isPractice ? 'Practice Track Data Isolation:' : 'Verified Assessment Recording:'}
          </p>
          <p className="text-slate-400 leading-relaxed">
            {isPractice
              ? 'This session was conducted in isolated skill-improvement mode. Practice metrics, iterative trial runs, and practice attempts are kept strictly isolated and never inflate or modify verified recruiter candidate profiles.'
              : 'This assessment was evaluated with 100% deterministic test suites. Your verified proficiency score is logged in your candidate proof dossier.'}
          </p>
        </div>
      </div>

      {/* Question Results Breakdown */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">
          Individual Challenge Breakdown
        </h3>

        {results.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-4">Detailed test assertions are being compiled.</p>
        ) : (
          <div className="space-y-3">
            {results.map((res: any, idx: number) => (
              <div
                key={res.question_id || idx}
                className="p-5 rounded-xl border border-slate-800 bg-slate-900/50 space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div className="flex items-center space-x-3">
                    {res.all_passed ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                    ) : (
                      <XCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
                    )}
                    <div>
                      <h4 className="text-sm font-semibold text-white">{res.title}</h4>
                      <p className="text-xs text-slate-400">{res.domain}</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span
                      className={`text-xs font-mono px-2.5 py-0.5 rounded font-semibold ${
                        res.all_passed
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : 'bg-rose-950 text-rose-400 border border-rose-800'
                      }`}
                    >
                      {res.passed_tests}/{res.total_tests} Tests Passed
                    </span>
                  </div>
                </div>

                <div className="bg-slate-950/80 p-3 rounded-lg border border-slate-800/80 font-mono text-xs">
                  <span className="text-slate-500 block text-[10px]">Feedback & Output:</span>
                  <span className={res.all_passed ? 'text-emerald-300' : 'text-slate-300'}>
                    {res.feedback}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Module 8: CodeTrace Coding Journey Timeline */}
      <div className="space-y-4 pt-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <GitCommit className="w-4 h-4 text-sky-400" />
            <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">
              CodeTrace Coding Journey
            </h3>
          </div>
          <button
            type="button"
            onClick={() => setShowTimeline(prev => !prev)}
            className="text-xs text-slate-400 hover:text-white flex items-center space-x-1"
          >
            <span>{showTimeline ? 'Collapse' : 'Expand'}</span>
            {showTimeline ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>

        {showTimeline && (
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-6">
            {/* Journey Meta Statistics */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800">
                <span className="text-[11px] text-slate-400 block font-medium">Revisions & Snapshots</span>
                <span className="text-xl font-bold text-white">
                  {timeline?.total_revisions || 0}
                </span>
              </div>
              <div className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800">
                <span className="text-[11px] text-slate-400 block font-medium">Sample Sandbox Runs</span>
                <span className="text-xl font-bold text-emerald-400">
                  {timeline?.sample_runs_count || 0}
                </span>
              </div>
              <div className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800">
                <span className="text-[11px] text-slate-400 block font-medium">Telemetry Verification</span>
                <span className="text-xs font-mono text-sky-400 font-semibold block mt-1">
                  100% Student Owned
                </span>
              </div>
            </div>

            {/* Timeline Stream */}
            {timeline?.events && timeline.events.length > 0 ? (
              <div className="space-y-3 relative pl-6 border-l-2 border-slate-800 ml-2">
                {timeline.events.map((ev, index) => {
                  const isSelected = selectedEvent?.id === ev.id;
                  const dateStr = new Date(ev.created_at).toLocaleTimeString();
                  return (
                    <div
                      key={ev.id || index}
                      onClick={() => setSelectedEvent(isSelected ? null : ev)}
                      className={`relative p-3.5 rounded-xl border transition cursor-pointer ${
                        isSelected
                          ? 'border-sky-500 bg-slate-850 shadow-md'
                          : 'border-slate-800 bg-slate-950/40 hover:bg-slate-900/60'
                      }`}
                    >
                      {/* Timeline dot */}
                      <span
                        className={`absolute -left-[31px] top-4 w-3 h-3 rounded-full border-2 border-slate-900 ${
                          ev.event_type === 'sample_run'
                            ? 'bg-emerald-400'
                            : ev.event_type === 'submission'
                            ? 'bg-sky-400'
                            : 'bg-indigo-400'
                        }`}
                      />

                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center space-x-2">
                          <span
                            className={`font-mono text-[10px] px-2 py-0.5 rounded uppercase font-semibold ${
                              ev.event_type === 'sample_run'
                                ? 'bg-emerald-950 text-emerald-400'
                                : ev.event_type === 'submission'
                                ? 'bg-sky-950 text-sky-400'
                                : 'bg-slate-800 text-slate-300'
                            }`}
                          >
                            {ev.event_type}
                          </span>
                          <span className="font-semibold text-white">{ev.question_id}</span>
                        </div>
                        <span className="text-slate-500 font-mono text-[11px]">{dateStr}</span>
                      </div>

                      {/* Diff summary line */}
                      {ev.diff_summary && (
                        <div className="mt-2 text-[11px] font-mono text-slate-400 flex items-center space-x-3">
                          {ev.diff_summary.added_lines !== undefined && (
                            <span className="text-emerald-400">+{ev.diff_summary.added_lines} lines</span>
                          )}
                          {ev.diff_summary.deleted_lines !== undefined && (
                            <span className="text-rose-400">-{ev.diff_summary.deleted_lines} lines</span>
                          )}
                          {ev.metrics?.execution_time_ms !== undefined && (
                            <span className="text-sky-300">{ev.metrics.execution_time_ms}ms runtime</span>
                          )}
                        </div>
                      )}

                      {/* Expanded Code Preview */}
                      {isSelected && (
                        <div className="mt-3 pt-3 border-t border-slate-800 space-y-2">
                          <span className="text-[10px] uppercase font-mono text-slate-500 block">
                            Code Snapshot at {dateStr}:
                          </span>
                          <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-xs font-mono overflow-x-auto max-h-48 whitespace-pre leading-relaxed">
                            {ev.code_snapshot}
                          </pre>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic py-2">
                No telemetry snapshots recorded for this session.
              </p>
            )}
          </div>
        )}
      </div>

      {/* Bottom Actions */}
      <div className="pt-4 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Link
          to="/dashboard/student/assessments"
          className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-400 hover:text-white transition"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Return to Assessment Hub</span>
        </Link>

        <Link
          to="/dashboard/student/assessments"
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold transition"
        >
          <span>Take Another Challenge</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};

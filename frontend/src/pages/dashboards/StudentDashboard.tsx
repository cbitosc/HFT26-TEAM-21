/**
 * StudentDashboard — primary workspace for active students.
 * Shows quick status, portfolio setup progress, capability gateways, assigned tasks, and recruiter consent.
 */

import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  GraduationCap,
  FileUp,
  Code2,
  BarChart3,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  Building2,
  Video,
  Clock,
  RefreshCw,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { fetchStudentPortfolio } from '../../services/portfolio';
import {
  getStudentConsent,
  updateStudentConsent,
  listMyInterviews,
  respondToInterview,
} from '../../services/recruiter';
import { listMyAssignedTasks } from '../../services/college';
import { PortfolioResponse } from '../../types/portfolio';
import { CollegeTaskResponse } from '../../types/college';
import { InterviewSessionResponse } from '../../types/recruiter';
import {
  DEMO_STUDENT_PORTFOLIO,
  DEMO_STUDENT_TASKS,
  DEMO_STUDENT_INTERVIEWS,
} from '../../services/demoData';

export const StudentDashboard: React.FC = () => {
  const { profile, session, isGuest } = useAuth();
  const token = session?.access_token || 'dev-student-token';

  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [consent, setConsent] = useState<boolean>(false);
  const [isUpdatingConsent, setIsUpdatingConsent] = useState<boolean>(false);
  const [tasks, setTasks] = useState<CollegeTaskResponse[]>([]);
  const [interviews, setInterviews] = useState<InterviewSessionResponse[]>([]);
  const [isRespondingId, setIsRespondingId] = useState<string | null>(null);

  const refreshInterviews = useCallback(async () => {
    if (isGuest) return;
    if (token) {
      try {
        const res = await listMyInterviews(token);
        setInterviews(res);
      } catch {
        // silent
      }
    }
  }, [token, isGuest]);

  useEffect(() => {
    if (isGuest) {
      setPortfolio(DEMO_STUDENT_PORTFOLIO);
      setConsent(true);
      setTasks(DEMO_STUDENT_TASKS);
      setInterviews(DEMO_STUDENT_INTERVIEWS);
      return;
    }

    if (token) {
      fetchStudentPortfolio(token)
        .then(data => setPortfolio(data))
        .catch(() => setPortfolio(null));

      getStudentConsent(token)
        .then(val => setConsent(val))
        .catch(() => setConsent(false));

      listMyAssignedTasks(token)
        .then(res => setTasks(res))
        .catch(() => setTasks([]));

      refreshInterviews();
    }
  }, [token, isGuest, refreshInterviews]);

  const handleRespondInterview = async (sessionId: string, action: 'accept' | 'decline') => {
    setIsRespondingId(sessionId);
    if (isGuest) {
      setInterviews(prev =>
        prev.map(inv =>
          inv.id === sessionId
            ? {
                ...inv,
                candidate_accepted: action === 'accept',
                status: action === 'accept' ? 'scheduled' : 'cancelled',
              }
            : inv
        )
      );
      setIsRespondingId(null);
      return;
    }

    try {
      await respondToInterview(token, sessionId, action);
      await refreshInterviews();
    } catch (err) {
      console.error('Failed to respond to interview:', err);
    } finally {
      setIsRespondingId(null);
    }
  };

  const handleToggleConsent = async () => {
    if (isGuest) {
      setConsent(!consent);
      return;
    }

    setIsUpdatingConsent(true);
    try {
      const updated = await updateStudentConsent(token, !consent);
      setConsent(updated);
    } catch {
      // Toggle failure silent
    } finally {
      setIsUpdatingConsent(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Welcome */}
      <section className="space-y-2">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium bg-sky-950/80 border border-sky-800/60 text-sky-300">
          <GraduationCap className="w-3.5 h-3.5" />
          <span>Student Dashboard</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
          Welcome, {profile?.full_name || 'Student'}
        </h1>
        <p className="text-sm text-slate-400 max-w-xl">
          Your workspace for portfolio uploads, adaptive assessments, coding practice, college tasks, and verified recruiter discovery.
        </p>
      </section>

      {/* Recruiter Discoverability Consent Banner */}
      <section className="rounded-xl border border-purple-900/60 bg-purple-950/20 p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start space-x-3">
          <ShieldCheck className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Recruiter Discoverability Consent
              </h3>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                  consent ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-slate-800 text-slate-400'
                }`}
              >
                {consent ? 'CONSENT GRANTED' : 'DISCOVERY PAUSED'}
              </span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed max-w-2xl">
              Allow verified partner recruiters to view your verified skill achievements and invite you to pair-coding interviews.
              Practice sandbox sessions and private contacts are strictly isolated and never shared.
            </p>
          </div>
        </div>

        <button
          onClick={handleToggleConsent}
          disabled={isUpdatingConsent}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition self-start sm:self-auto ${
            consent
              ? 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700'
              : 'bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-600/20'
          }`}
        >
          {isUpdatingConsent ? 'Updating…' : consent ? 'Revoke Consent' : 'Enable Recruiter Discovery'}
        </button>
      </section>

      {/* Scheduled Live Interviews */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
            <Video className="w-4 h-4 text-emerald-400" />
            <span>Interview Invitations ({interviews.length})</span>
          </h2>
          <button
            onClick={refreshInterviews}
            className="text-xs text-slate-400 hover:text-white inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700/80 transition"
            title="Refresh interview status"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Refresh</span>
          </button>
        </div>

        {interviews.length === 0 ? (
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-6 text-center space-y-2">
            <Video className="w-8 h-8 text-slate-600 mx-auto" />
            <p className="text-sm font-semibold text-slate-300">No Interview Invitations Yet</p>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              When a verified partner recruiter reviews your skill achievements and schedules a live coding interview, it will appear here. Make sure Recruiter Discoverability is enabled above!
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {interviews.map(inv => {
              const isAccepted = inv.candidate_accepted || inv.status === 'in_progress';
              const isPending = inv.status === 'scheduled' && !inv.candidate_accepted;
              const isCancelled = inv.status === 'cancelled';
              const isCompleted = inv.status === 'completed';

              return (
                <div
                  key={inv.id}
                  className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 space-y-3 flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      {isPending ? (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800 animate-pulse">
                          INVITATION RECEIVED
                        </span>
                      ) : isAccepted ? (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                          {inv.status === 'in_progress' ? 'IN PROGRESS' : 'INVITATION ACCEPTED'}
                        </span>
                      ) : isCancelled ? (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                          DECLINED / CANCELLED
                        </span>
                      ) : (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800">
                          COMPLETED
                        </span>
                      )}
                      <span className="text-[10px] text-slate-400">
                        {new Date(inv.scheduled_at).toLocaleDateString()}
                      </span>
                    </div>

                    <h4 className="font-semibold text-white text-sm">{inv.title}</h4>
                    {inv.task_description && (
                      <p className="text-xs text-slate-400 line-clamp-2">{inv.task_description}</p>
                    )}
                  </div>

                  <div className="pt-2 border-t border-slate-800/80">
                    {isPending ? (
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleRespondInterview(inv.id, 'accept')}
                          disabled={isRespondingId === inv.id}
                          className="flex-1 py-1.5 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold transition text-center shadow-sm"
                        >
                          {isRespondingId === inv.id ? 'Updating…' : 'Accept Invitation'}
                        </button>
                        <button
                          onClick={() => handleRespondInterview(inv.id, 'decline')}
                          disabled={isRespondingId === inv.id}
                          className="py-1.5 px-3 rounded-lg bg-slate-800 hover:bg-rose-950/80 hover:text-rose-400 hover:border-rose-800 border border-slate-700 disabled:opacity-50 text-slate-400 text-xs font-semibold transition"
                        >
                          Decline
                        </button>
                      </div>
                    ) : isAccepted ? (
                      <Link
                        to={`/interview/${inv.id}`}
                        className="inline-flex items-center justify-center space-x-1.5 w-full py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition"
                      >
                        <Video className="w-3.5 h-3.5" />
                        <span>Join Live Coding Room</span>
                      </Link>
                    ) : isCompleted ? (
                      <span className="text-xs text-slate-500 italic block text-center py-1">
                        Session Concluded & Evaluated
                      </span>
                    ) : (
                      <span className="text-xs text-slate-500 italic block text-center py-1">
                        Invitation was declined
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* College Tasks Section (Module 11) */}
      {tasks.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
            <Building2 className="w-4 h-4 text-indigo-400" />
            <span>Assigned College Coding Tasks ({tasks.length})</span>
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {tasks.map(t => (
              <div
                key={t.id}
                className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 space-y-3 flex flex-col justify-between"
              >
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {t.domain}
                    </span>
                    <span className="text-[10px] font-medium text-slate-400 capitalize">{t.difficulty}</span>
                  </div>
                  <h4 className="font-semibold text-white text-sm mt-1">{t.title}</h4>
                  <p className="text-xs text-slate-400 line-clamp-2">{t.description}</p>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-xs">
                  <span className="text-slate-500 flex items-center space-x-1">
                    <Clock className="w-3 h-3" />
                    <span>{t.duration_minutes}m</span>
                  </span>
                  <Link
                    to="/dashboard/student/assessments"
                    className="text-xs font-semibold text-indigo-400 hover:text-indigo-300"
                  >
                    Solve in Workspace →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Portfolio Quick Status Banner */}
      <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <h2 className="text-sm font-semibold text-white">Portfolio Status:</h2>
            {portfolio ? (
              portfolio.confirmed ? (
                <span className="inline-flex items-center space-x-1 text-xs font-medium text-emerald-400 bg-emerald-950/80 border border-emerald-800/80 px-2.5 py-0.5 rounded-full">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>Confirmed ({portfolio.data.skills.programming_languages.length + portfolio.data.skills.frameworks_and_tools.length} skills unverified)</span>
                </span>
              ) : (
                <span className="inline-flex items-center space-x-1 text-xs font-medium text-amber-400 bg-amber-950/80 border border-amber-800/80 px-2.5 py-0.5 rounded-full">
                  <span>Draft Uploaded (Awaiting Confirmation)</span>
                </span>
              )
            ) : (
              <span className="text-xs text-slate-500">Not Uploaded Yet</span>
            )}
          </div>
          <p className="text-xs text-slate-400">
            {portfolio
              ? 'Your confirmed skills define the boundary for adaptive assessments.'
              : 'Upload your resume (JSON/PDF) to populate your verified skill profile.'}
          </p>
        </div>

        <Link
          to="/dashboard/student/portfolio"
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold transition self-start md:self-auto"
        >
          <span>{portfolio ? 'Manage Portfolio' : 'Upload Portfolio'}</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </section>

      {/* Main Feature Cards */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        <Link
          to="/dashboard/student/portfolio"
          className="rounded-xl border border-slate-800 bg-slate-900/50 hover:border-slate-700 p-5 space-y-3 transition group flex flex-col justify-between"
        >
          <div className="space-y-3">
            <FileUp className="w-6 h-6 text-sky-400 group-hover:scale-105 transition" />
            <h3 className="font-semibold text-white text-sm group-hover:text-sky-300 transition">
              Portfolio Upload & Extraction
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Upload your resume or projects to automatically extract your skills, technical domains, and DSA topics.
            </p>
          </div>
          <div className="flex items-center justify-between pt-2">
            <span className="text-[10px] font-mono text-slate-500 bg-slate-800 px-2 py-0.5 rounded">
              Module 3 · Active
            </span>
            <span className="text-xs font-semibold text-sky-400 inline-flex items-center space-x-1">
              <span>Open</span>
              <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition" />
            </span>
          </div>
        </Link>

        <Link
          to="/dashboard/student/assessments"
          className="rounded-xl border border-indigo-800/60 bg-indigo-950/20 hover:border-indigo-700/80 p-5 space-y-3 transition group flex flex-col justify-between"
        >
          <div className="space-y-3">
            <Code2 className="w-6 h-6 text-indigo-400 group-hover:scale-105 transition" />
            <h3 className="font-semibold text-white text-sm group-hover:text-indigo-300 transition">
              Adaptive Assessments
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Take tiered coding challenges (Novice, Adept, Master) matched to your confirmed portfolio skills.
            </p>
          </div>
          <div className="flex items-center justify-between pt-2">
            <span className="text-[10px] font-mono text-indigo-400 bg-indigo-950 px-2 py-0.5 rounded border border-indigo-800/60">
              Modules 5 & 6 · Active
            </span>
            <span className="text-xs font-semibold text-indigo-400 inline-flex items-center space-x-1">
              <span>Launch</span>
              <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition" />
            </span>
          </div>
        </Link>

        <Link
          to="/dashboard/student/analytics"
          className="rounded-xl border border-emerald-800/60 bg-emerald-950/20 hover:border-emerald-700/80 p-5 space-y-3 transition group flex flex-col justify-between"
        >
          <div className="space-y-3">
            <BarChart3 className="w-6 h-6 text-emerald-400 group-hover:scale-105 transition" />
            <h3 className="font-semibold text-white text-sm group-hover:text-emerald-300 transition">Performance Analytics</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Track your progress with transparent deterministic scoring, domain mastery, and skill breakdowns.
            </p>
          </div>
          <div className="flex items-center justify-between pt-2">
            <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60">
              Module 10 · Active
            </span>
            <span className="text-xs font-semibold text-emerald-400 inline-flex items-center space-x-1">
              <span>View</span>
              <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition" />
            </span>
          </div>
        </Link>
      </section>
    </div>
  );
};

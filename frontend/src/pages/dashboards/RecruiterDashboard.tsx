/**
 * RecruiterDashboard — Module 12: Recruiter Portal & Candidate Discovery
 * Allows active approved recruiters to discover verified candidates, review dossiers, and schedule live interviews.
 */

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Briefcase,
  Search,
  Video,
  Calendar,
  AlertCircle,
  X,
  Loader2,
  FileText,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import {
  searchCandidates,
  getCandidateDossier,
  createInterview,
  listRecruiterInterviews,
} from '../../services/recruiter';
import {
  CandidateDiscoveryItem,
  CandidateDetailProfileResponse,
  InterviewSessionResponse,
} from '../../types/recruiter';
import {
  DEMO_RECRUITER_CANDIDATES,
  DEMO_CANDIDATE_DOSSIER,
  DEMO_RECRUITER_INTERVIEWS,
} from '../../services/demoData';

export const RecruiterDashboard: React.FC = () => {
  const { profile, session, isGuest } = useAuth();
  const token = session?.access_token || 'dev-recruiter-token';

  const [candidates, setCandidates] = useState<CandidateDiscoveryItem[]>([]);
  const [interviews, setInterviews] = useState<InterviewSessionResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [domainFilter, setDomainFilter] = useState('');
  const [skillFilter, setSkillFilter] = useState('');

  // Modals
  const [selectedCandidateDossier, setSelectedCandidateDossier] = useState<CandidateDetailProfileResponse | null>(null);
  const [scheduleCandidate, setScheduleCandidate] = useState<CandidateDiscoveryItem | null>(null);
  const [interviewTitle, setInterviewTitle] = useState('');
  const [taskDesc, setTaskDesc] = useState('');
  const [isScheduling, setIsScheduling] = useState(false);

  useEffect(() => {
    loadData();
  }, [token, isGuest]);

  const loadData = () => {
    if (isGuest) {
      let filtered = [...DEMO_RECRUITER_CANDIDATES];
      if (skillFilter.trim()) {
        const query = skillFilter.toLowerCase();
        filtered = filtered.filter(c =>
          c.verified_skills.some(s => s.toLowerCase().includes(query))
        );
      }
      setCandidates(filtered);
      setInterviews(DEMO_RECRUITER_INTERVIEWS);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    Promise.all([
      searchCandidates(token, { domain: domainFilter || undefined, skill: skillFilter || undefined }),
      listRecruiterInterviews(token).catch(() => []),
    ])
      .then(([cands, ints]) => {
        setCandidates(cands);
        setInterviews(ints);
        setIsLoading(false);
      })
      .catch(err => {
        setError(err.message || 'Failed to load recruiter data.');
        setIsLoading(false);
      });
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadData();
  };

  const handleViewDossier = async (candidateId: string) => {
    if (isGuest) {
      setSelectedCandidateDossier(DEMO_CANDIDATE_DOSSIER);
      return;
    }

    try {
      const data = await getCandidateDossier(token, candidateId);
      setSelectedCandidateDossier(data);
    } catch (err: any) {
      setError(err.message || 'Could not load candidate dossier.');
    }
  };

  const handleScheduleInterview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scheduleCandidate || !interviewTitle.trim()) return;

    if (isGuest) {
      const demoInterview: InterviewSessionResponse = {
        id: `demo-interview-${Date.now()}`,
        recruiter_id: 'guest-recruiter-session',
        candidate_id: scheduleCandidate.candidate_id,
        title: `${interviewTitle.trim()} (Sample Demo Session)`,
        task_description: taskDesc.trim() || 'Pair-coding problem-solving interview',
        scheduled_at: new Date(Date.now() + 2 * 3600000).toISOString(),
        status: 'scheduled',
        current_code: '# Live Pair-Coding Workspace\ndef solution():\n    pass\n',
        language: 'python',
        version: 1,
        requested_changes: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setInterviews(prev => [demoInterview, ...prev]);
      setScheduleCandidate(null);
      setInterviewTitle('');
      setTaskDesc('');
      return;
    }

    setIsScheduling(true);
    try {
      await createInterview(token, {
        candidate_id: scheduleCandidate.candidate_id,
        title: interviewTitle.trim(),
        task_description: taskDesc.trim(),
      });
      setScheduleCandidate(null);
      setInterviewTitle('');
      setTaskDesc('');
      loadData();
    } catch (err: any) {
      setError(err.message || 'Could not schedule interview.');
    } finally {
      setIsScheduling(false);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <section className="space-y-2">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium bg-purple-950/80 border border-purple-800/60 text-purple-300">
          <Briefcase className="w-3.5 h-3.5" />
          <span>Verified Recruiter Portal</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
          Verified Talent Discovery
        </h1>
        <p className="text-sm text-slate-400">
          Welcome, {profile?.full_name || 'Recruiter'} · Discover verified candidates, review dossiers with student consent, and conduct live coding sessions.
        </p>
      </section>

      {/* Error alert */}
      {error && (
        <div className="p-4 rounded-xl border border-rose-900/60 bg-rose-950/20 flex items-center justify-between text-xs text-rose-300">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-400" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Scheduled Interviews Carousel / Strip */}
      {interviews.length > 0 && (
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
              <Video className="w-4 h-4 text-emerald-400" />
              <span>Live Interviews ({interviews.length})</span>
            </h2>
            <button
              onClick={loadData}
              className="text-xs text-slate-400 hover:text-white inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700/80 transition"
              title="Refresh interviews list"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Refresh</span>
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {interviews.map(inv => {
              const isPending = inv.status === 'scheduled' && !inv.candidate_accepted;
              const isAccepted = inv.status === 'scheduled' && inv.candidate_accepted;
              const isLive = inv.status === 'in_progress';
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
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800">
                          PENDING ACCEPTANCE
                        </span>
                      ) : isAccepted ? (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                          INVITATION ACCEPTED
                        </span>
                      ) : isLive ? (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800 animate-pulse">
                          IN PROGRESS (LIVE)
                        </span>
                      ) : isCancelled ? (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                          DECLINED
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
                    <Link
                      to={`/interview/${inv.id}`}
                      className="inline-flex items-center justify-center space-x-1.5 w-full py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition"
                    >
                      <Video className="w-3.5 h-3.5" />
                      <span>{isCompleted ? 'View Recording / Outcome' : 'Join Live Coding Room'}</span>
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Candidate Search Bar */}
      <section className="bg-slate-900/40 border border-slate-800 rounded-2xl p-5 space-y-4">
        <form onSubmit={handleSearch} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300">Technical Domain</label>
            <input
              type="text"
              placeholder="e.g. Algorithms, Backend"
              value={domainFilter}
              onChange={e => setDomainFilter(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300">Verified Skill</label>
            <input
              type="text"
              placeholder="e.g. Python, Trees"
              value={skillFilter}
              onChange={e => setSkillFilter(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
            />
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              className="inline-flex items-center justify-center space-x-2 w-full px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold transition"
            >
              <Search className="w-3.5 h-3.5" />
              <span>Filter Verified Candidates</span>
            </button>
          </div>
        </form>
      </section>

      {/* Candidate Discovery Grid */}
      <section className="space-y-4">
        <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
          Consenting Verified Candidates ({candidates.length})
        </h2>

        {isLoading ? (
          <div className="p-12 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
            <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
            <p className="text-sm">Querying verified candidate dossiers…</p>
          </div>
        ) : candidates.length === 0 ? (
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center space-y-3">
            <Search className="w-12 h-12 text-slate-600 mx-auto" />
            <p className="font-semibold text-white">No Consenting Candidates Found</p>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Students must explicitly grant recruiter discoverability consent in their settings before appearing in recruiter talent searches.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {candidates.map(c => (
              <div
                key={c.candidate_id}
                className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4 hover:border-slate-700 transition"
              >
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <h3 className="font-bold text-white text-base">{c.full_name}</h3>
                    <p className="text-xs text-slate-400">{c.college_name || 'Engineering Institute'}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-lg font-black text-emerald-400">{c.verified_avg_score}%</span>
                    <p className="text-[10px] text-slate-500">Verified Avg</p>
                  </div>
                </div>

                {/* Verified Skills */}
                <div className="space-y-1.5">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Verified Skills:</p>
                  <div className="flex flex-wrap gap-1.5">
                    {c.verified_skills.length > 0 ? (
                      c.verified_skills.map((vs, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-800/60 text-emerald-300 text-[11px] font-medium"
                        >
                          <ShieldCheck className="w-3 h-3 text-emerald-400" />
                          <span>{vs}</span>
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500 italic">Assessment in progress</span>
                    )}
                  </div>
                </div>

                {/* Unverified Portfolio Claims */}
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Portfolio Claims (Unverified):</p>
                  <div className="flex flex-wrap gap-1.5">
                    {c.portfolio_claims.map((claim, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded bg-slate-800/80 text-slate-400 text-[10px]">
                        {claim}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between">
                  <button
                    onClick={() => handleViewDossier(c.candidate_id)}
                    className="inline-flex items-center space-x-1 text-xs font-semibold text-purple-400 hover:text-purple-300"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>Inspect Dossier</span>
                  </button>

                  {(() => {
                    const existingInv = interviews.find(
                      i => i.candidate_id === c.candidate_id && i.status !== 'completed' && i.status !== 'cancelled'
                    );

                    if (existingInv) {
                      const isPending = existingInv.status === 'scheduled' && !existingInv.candidate_accepted;
                      return (
                        <div className="flex items-center space-x-2">
                          <span
                            className={`text-[10px] font-bold px-2 py-1 rounded border ${
                              isPending
                                ? 'bg-amber-950/80 text-amber-300 border-amber-800/80'
                                : 'bg-emerald-950/80 text-emerald-300 border-emerald-800/80'
                            }`}
                          >
                            {isPending ? 'Invitation Sent (Pending)' : 'Interview Scheduled'}
                          </span>
                          <Link
                            to={`/interview/${existingInv.id}`}
                            className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition"
                          >
                            <Video className="w-3 h-3 text-emerald-400" />
                            <span>View</span>
                          </Link>
                        </div>
                      );
                    }

                    return (
                      <button
                        onClick={() => setScheduleCandidate(c)}
                        className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold transition shadow-sm"
                      >
                        <Calendar className="w-3.5 h-3.5" />
                        <span>Invite to Interview</span>
                      </button>
                    );
                  })()}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Candidate Dossier Inspection Modal */}
      {selectedCandidateDossier && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <p className="text-[10px] uppercase font-bold text-purple-400">Consent-Governed Candidate Dossier</p>
                <h3 className="font-bold text-white text-base">{selectedCandidateDossier.full_name}</h3>
              </div>
              <button onClick={() => setSelectedCandidateDossier(null)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                <p className="text-xs text-slate-400">Verified Avg</p>
                <p className="text-xl font-bold text-emerald-400 mt-1">{selectedCandidateDossier.verified_avg_composite}%</p>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                <p className="text-xs text-slate-400">Test Pass Rate</p>
                <p className="text-xl font-bold text-sky-400 mt-1">{selectedCandidateDossier.verified_test_pass_rate}%</p>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                <p className="text-xs text-slate-400">Verified Sessions</p>
                <p className="text-xl font-bold text-purple-400 mt-1">{selectedCandidateDossier.verified_sessions_count}</p>
              </div>
            </div>

            {/* Assessment History */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Verified Assessment History</h4>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {selectedCandidateDossier.verified_history.map((vh, idx) => (
                  <div key={idx} className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between text-xs">
                    <div>
                      <p className="font-semibold text-white">{vh.domain} ({vh.tier})</p>
                      <p className="text-[10px] text-slate-500">{vh.date}</p>
                    </div>
                    <span className="font-bold text-emerald-400">{vh.composite_score}%</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedCandidateDossier(null)}
                className="px-4 py-2 text-xs rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold"
              >
                Close Dossier
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Schedule Interview Modal */}
      {scheduleCandidate && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <p className="text-[10px] uppercase font-bold text-emerald-400">Schedule Live Pair-Coding Interview</p>
                <h3 className="font-bold text-white text-base">Candidate: {scheduleCandidate.full_name}</h3>
              </div>
              <button onClick={() => setScheduleCandidate(null)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleScheduleInterview} className="space-y-3">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Interview Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Distributed Architecture & OOP Coding"
                  value={interviewTitle}
                  onChange={e => setInterviewTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Task Objective & Instructions</label>
                <textarea
                  rows={3}
                  placeholder="Describe the problem to be solved together..."
                  value={taskDesc}
                  onChange={e => setTaskDesc(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setScheduleCandidate(null)}
                  className="px-4 py-2 text-xs rounded-xl border border-slate-800 text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isScheduling}
                  className="px-4 py-2 text-xs rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold transition"
                >
                  {isScheduling ? 'Scheduling…' : 'Confirm Invitation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

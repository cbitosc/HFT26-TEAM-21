/**
 * LiveInterviewRoom — Module 12: Live Collaborative Coding Interview
 * Split workspace: instructions & prompt refactors on left, Monaco editor in middle, sandbox execution below.
 */

import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Play,
  CheckCircle2,
  AlertCircle,
  MessageSquarePlus,
  ArrowLeft,
  Loader2,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import {
  getInterview,
  syncInterview,
  requestInterviewChange,
  executeInterviewSandbox,
  finishInterview,
} from '../../services/recruiter';
import { InterviewSessionResponse } from '../../types/recruiter';
import { CodeEditor } from '../../components/CodeEditor';

export const LiveInterviewRoom: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { profile, session, isGuest } = useAuth();
  const token =
    session?.access_token ||
    (profile?.role === 'recruiter' ? 'dev-recruiter-token' : 'dev-student-token');

  const [interview, setInterview] = useState<InterviewSessionResponse | null>(null);
  const [code, setCode] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);

  // Recruiter prompt refactor
  const [newChangePrompt, setNewChangePrompt] = useState('');
  const [isSubmittingChange, setIsSubmittingChange] = useState(false);

  // Sandbox execution
  const [sandboxResult, setSandboxResult] = useState<any | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);

  // Finish interview modal
  const [showFinishModal, setShowFinishModal] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [outcome, setOutcome] = useState<'passed' | 'needs_review' | 'rejected'>('passed');

  const isRecruiter = profile?.role === 'recruiter';

  useEffect(() => {
    if (!id) return;
    loadInterview(true);

    if (isGuest || id?.startsWith('demo')) return;

    // Polling sync interval (every 4 seconds for seamless functional synchronization)
    const interval = setInterval(() => {
      loadInterview(false);
    }, 4000);

    return () => clearInterval(interval);
  }, [id, token, isGuest]);

  const loadInterview = (initial: boolean = false) => {
    if (!id) return;

    if (isGuest || id?.startsWith('demo')) {
      const demoSession: InterviewSessionResponse = {
        id: id || 'demo-interview-001',
        recruiter_id: 'recruiter-demo-001',
        candidate_id: profile?.id || 'demo-student-guest',
        title: 'Frontend & Systems Engineering Screening (Sample Interview)',
        task_description:
          'Live collaborative session: Design and refactor a debounce search pipeline with cache memoization and unit tests.',
        scheduled_at: new Date(Date.now() + 86400000).toISOString(),
        status: 'in_progress',
        current_code:
          '# Welcome to your live coding interview!\n# Task: Refactor debounce search\n\ndef search_query(query: str):\n    return []\n',
        language: 'python',
        version: 1,
        requested_changes: [
          {
            id: 'demo-req-1',
            requested_change: 'Optimize the memory footprint by pruning query cache entries older than 60 seconds.',
            instructions: 'Ensure thread-safety or async locks when clearing cache.',
            requested_at: new Date(Date.now() - 300000).toISOString(),
            code_snapshot_at_request: '# Snapshot\ndef search_query(): pass',
          },
        ],
        candidate_accepted: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setInterview(demoSession);
      if (initial) {
        setCode(demoSession.current_code);
        setIsLoading(false);
      }
      return;
    }

    getInterview(token, id)
      .then(res => {
        setInterview(res);
        if (initial) {
          setCode(res.current_code);
          setIsLoading(false);
        } else if (res.last_edited_by && profile?.id && res.last_edited_by !== profile.id) {
          // Collaborative sync: remote participant edited the code
          setCode(res.current_code);
        }
      })
      .catch(err => {
        if (initial) {
          setError(err.message || 'Could not load interview session.');
          setIsLoading(false);
        }
      });
  };

  const handleSyncCode = async (newCode: string) => {
    setCode(newCode);
    if (!id) return;

    if (isGuest || id?.startsWith('demo')) {
      setInterview(prev => prev ? { ...prev, current_code: newCode } : null);
      return;
    }

    setIsSyncing(true);
    try {
      const res = await syncInterview(token, id, newCode, undefined, interview?.version);
      setInterview(res);
      if (res.current_code !== newCode) {
        // If a remote newer revision was preserved, reflect it
        setCode(res.current_code);
      }
    } catch {
      // Background sync fail silent
    } finally {
      setIsSyncing(false);
    }
  };

  const handleRequestChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !newChangePrompt.trim()) return;

    if (isGuest || id?.startsWith('demo')) {
      setInterview(prev => prev ? {
        ...prev,
        requested_changes: [
          ...(prev.requested_changes || []),
          {
            id: `demo-req-${Date.now()}`,
            requested_change: newChangePrompt.trim(),
            instructions: 'Follow standard algorithmic design patterns.',
            requested_at: new Date().toISOString(),
            code_snapshot_at_request: code,
          }
        ]
      } : null);
      setNewChangePrompt('');
      return;
    }

    setIsSubmittingChange(true);
    try {
      const res = await requestInterviewChange(token, id, newChangePrompt.trim());
      setInterview(res);
      setNewChangePrompt('');
    } catch (err: any) {
      setError(err.message || 'Failed to submit prompt refactor.');
    } finally {
      setIsSubmittingChange(false);
    }
  };

  const handleRunSandbox = async () => {
    if (!id) return;
    setIsExecuting(true);
    setSandboxResult(null);

    if (isGuest || id?.startsWith('demo')) {
      setTimeout(() => {
        setSandboxResult({
          status: 'accepted',
          stdout: 'Executing solution in isolated container...\nTest Case 1: passed\nTest Case 2: passed\nExecution Time: 42ms | Memory: 15.2MB',
          passed: true,
        });
        setIsExecuting(false);
      }, 400);
      return;
    }

    try {
      const res = await executeInterviewSandbox(token, id);
      setSandboxResult(res);
    } catch (err: any) {
      setSandboxResult({ status: 'runtime_error', stderr: err.message });
    } finally {
      setIsExecuting(false);
    }
  };

  const handleFinishInterview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !feedback.trim()) return;

    if (isGuest || id?.startsWith('demo')) {
      setInterview(prev => prev ? { ...prev, status: 'completed', outcome, feedback } : null);
      setShowFinishModal(false);
      return;
    }

    try {
      const res = await finishInterview(token, id, feedback.trim(), outcome);
      setInterview(res);
      setShowFinishModal(false);
    } catch (err: any) {
      setError(err.message || 'Failed to complete interview.');
    }
  };

  if (isLoading) {
    return (
      <div className="p-16 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
        <p className="text-sm">Connecting to live interview room…</p>
      </div>
    );
  }

  if (error || !interview) {
    return (
      <div className="p-8 max-w-lg mx-auto text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-500 mx-auto" />
        <h2 className="text-base font-bold text-white">Interview Access Denied</h2>
        <p className="text-xs text-slate-400">{error || 'Session could not be located.'}</p>
        <Link
          to="/dashboard"
          className="inline-flex items-center space-x-1 text-xs text-emerald-400 hover:text-white"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Dashboard</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4 max-w-7xl mx-auto h-[calc(100vh-6rem)] flex flex-col">
      {/* Top Bar */}
      <div className="flex items-center justify-between p-3 bg-slate-900 border border-slate-800 rounded-xl">
        <div className="flex items-center space-x-3">
          <Link
            to={isRecruiter ? '/dashboard/recruiter' : '/dashboard/student'}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <h2 className="text-sm font-bold text-white">{interview.title}</h2>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                {interview.status}
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Role: <span className="font-semibold text-emerald-400 capitalize">{profile?.role}</span> · Functional live sync active
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs text-slate-400">
            {isSyncing ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-emerald-400" />
            ) : (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            )}
            <span className="hidden sm:inline">Workspace Synced</span>
          </div>

          <button
            onClick={handleRunSandbox}
            disabled={isExecuting}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow transition"
          >
            {isExecuting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            <span>Run Sandbox</span>
          </button>

          {isRecruiter && interview.status !== 'completed' && (
            <button
              onClick={() => setShowFinishModal(true)}
              className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold transition"
            >
              Finish Interview
            </button>
          )}
        </div>
      </div>

      {/* Main Split Body */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 min-h-0">
        {/* Left Column: Instructions & Refactoring Stream */}
        <div className="lg:col-span-4 bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col space-y-4 overflow-y-auto">
          {/* Instructions */}
          <div className="space-y-1.5">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Task Instructions</h3>
            <div className="p-3 bg-slate-950 rounded-lg text-xs text-slate-300 leading-relaxed border border-slate-800/80">
              {interview.task_description || 'Implement the solution collaboratively in the code workspace.'}
            </div>
          </div>

          {/* Prompt Refactoring Panel */}
          <div className="space-y-2 flex-1 flex flex-col">
            <h3 className="text-xs font-bold text-purple-300 uppercase tracking-wider flex items-center space-x-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Prompt Refactor Stream</span>
            </h3>

            {isRecruiter && interview.status !== 'completed' && (
              <form onSubmit={handleRequestChange} className="space-y-2">
                <textarea
                  rows={2}
                  required
                  value={newChangePrompt}
                  onChange={e => setNewChangePrompt(e.target.value)}
                  placeholder="Request code modification (e.g. 'Handle concurrency', 'Refactor to O(1) space')..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-purple-500"
                />
                <button
                  type="submit"
                  disabled={isSubmittingChange}
                  className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold"
                >
                  <MessageSquarePlus className="w-3.5 h-3.5" />
                  <span>Send Refactor Prompt</span>
                </button>
              </form>
            )}

            {/* List of past requested changes */}
            <div className="space-y-2 flex-1 overflow-y-auto">
              {interview.requested_changes.length === 0 ? (
                <p className="text-xs text-slate-500 italic p-3 text-center">
                  No prompt refactors introduced yet.
                </p>
              ) : (
                interview.requested_changes.map(rc => (
                  <div key={rc.id} className="p-2.5 rounded-lg bg-purple-950/30 border border-purple-900/40 space-y-1">
                    <p className="text-xs text-purple-200 font-medium">{rc.requested_change}</p>
                    <span className="text-[10px] text-slate-500">
                      {new Date(rc.requested_at).toLocaleTimeString()}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Code Editor & Sandbox Output */}
        <div className="lg:col-span-8 flex flex-col space-y-3 min-h-0">
          <div className="flex-1 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden min-h-[300px]">
            <CodeEditor
              value={code}
              onChange={handleSyncCode}
              language="python"
            />
          </div>

          {/* Sandbox Output Pane */}
          {sandboxResult && (
            <div className="h-44 bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col text-xs font-mono overflow-y-auto">
              <div className="flex items-center justify-between pb-1.5 border-b border-slate-800 text-[11px]">
                <span className="text-slate-400">Sandbox Execution Output</span>
                <span className={sandboxResult.passed ? 'text-emerald-400' : 'text-rose-400'}>
                  {sandboxResult.status.toUpperCase()}
                </span>
              </div>
              <div className="pt-2 text-slate-200 space-y-1">
                {sandboxResult.stdout && <pre>{sandboxResult.stdout}</pre>}
                {sandboxResult.stderr && <pre className="text-rose-400">{sandboxResult.stderr}</pre>}
                {sandboxResult.compile_output && <pre className="text-amber-400">{sandboxResult.compile_output}</pre>}
                {!sandboxResult.stdout && !sandboxResult.stderr && (
                  <p className="text-slate-500">Program executed with empty standard output.</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Recruiter Finish Modal */}
      {showFinishModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4">
            <h3 className="font-bold text-white text-base">Complete Live Interview</h3>
            <form onSubmit={handleFinishInterview} className="space-y-3">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Recruiter Evaluation & Feedback</label>
                <textarea
                  required
                  rows={4}
                  value={feedback}
                  onChange={e => setFeedback(e.target.value)}
                  placeholder="Record assessment of problem-solving, code quality, and response to prompt changes..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-white"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Interview Outcome</label>
                <select
                  value={outcome}
                  onChange={e => setOutcome(e.target.value as any)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
                >
                  <option value="passed">Passed</option>
                  <option value="needs_review">Needs Further Review</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>

              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowFinishModal(false)}
                  className="px-4 py-2 text-xs rounded-xl border border-slate-800 text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold"
                >
                  Finalize Interview
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

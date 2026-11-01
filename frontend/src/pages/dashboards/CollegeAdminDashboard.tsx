/**
 * CollegeAdminDashboard — Module 11: College Task Management
 * Allows College Administrators to create, publish, manage tasks, and inspect analytics.
 */

import React, { useEffect, useState } from 'react';
import {
  Building2,
  Plus,
  Clock,
  Archive,
  BarChart2,
  AlertCircle,
  FileCode,
  X,
  Loader2,
  Users,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import {
  listCollegeTasks,
  createCollegeTask,
  updateCollegeTaskStatus,
  getTaskAnalytics,
} from '../../services/college';
import {
  CollegeTaskResponse,
  CollegeTaskCreate,
  CollegeTaskAnalyticsResponse,
} from '../../types/college';
import {
  DEMO_COLLEGE_TASKS,
  DEMO_COLLEGE_ANALYTICS,
} from '../../services/demoData';

export const CollegeAdminDashboard: React.FC = () => {
  const { profile, session, isGuest } = useAuth();
  const token = session?.access_token || 'dev-college-admin-token';

  const [tasks, setTasks] = useState<CollegeTaskResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedAnalytics, setSelectedAnalytics] = useState<CollegeTaskAnalyticsResponse | null>(null);

  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [domain, setDomain] = useState('Algorithms & DSA');
  const [difficulty, setDifficulty] = useState('medium');
  const [duration, setDuration] = useState(60);
  const [instructions, setInstructions] = useState('');
  const [starterCode, setStarterCode] = useState('# Write solution here\ndef solve():\n    pass\n');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    loadTasks();
  }, [token, isGuest]);

  const loadTasks = () => {
    if (isGuest) {
      setTasks(DEMO_COLLEGE_TASKS);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    listCollegeTasks(token)
      .then(res => {
        setTasks(res);
        setIsLoading(false);
      })
      .catch(err => {
        setError(err.message || 'Failed to load college tasks.');
        setIsLoading(false);
      });
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) return;

    if (isGuest) {
      const demoTask: CollegeTaskResponse = {
        id: `demo-task-${Date.now()}`,
        college_id: 'demo-college-001',
        creator_id: 'admin-demo-001',
        title: `${title.trim()} (Sample Demo Task)`,
        description: description.trim(),
        domain,
        difficulty,
        allowed_languages: ['python'],
        duration_minutes: duration,
        instructions,
        starter_code: starterCode,
        test_cases: [{ input: 'sample', expected_output: 'sample' }],
        status: 'published',
        assigned_student_ids: [],
        allow_late_submissions: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setTasks(prev => [demoTask, ...prev]);
      setShowCreateModal(false);
      resetForm();
      return;
    }

    setIsSubmitting(true);
    const payload: CollegeTaskCreate = {
      title: title.trim(),
      description: description.trim(),
      domain,
      difficulty,
      duration_minutes: duration,
      instructions,
      starter_code: starterCode,
      test_cases: [
        { input: 'test_input', expected_output: 'test_output' },
      ],
      status: 'published',
    };

    try {
      await createCollegeTask(token, payload);
      setShowCreateModal(false);
      resetForm();
      loadTasks();
    } catch (err: any) {
      setError(err.message || 'Could not create task.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setTitle('');
    setDescription('');
    setInstructions('');
  };

  const handleStatusChange = async (taskId: string, newStatus: string) => {
    if (isGuest) {
      setTasks(prev =>
        prev.map(t => (t.id === taskId ? { ...t, status: newStatus as any } : t))
      );
      return;
    }

    try {
      await updateCollegeTaskStatus(token, taskId, newStatus);
      loadTasks();
    } catch (err: any) {
      setError(err.message || 'Status transition failed.');
    }
  };

  const handleViewAnalytics = async (taskId: string) => {
    if (isGuest) {
      setSelectedAnalytics(DEMO_COLLEGE_ANALYTICS);
      return;
    }

    try {
      const data = await getTaskAnalytics(token, taskId);
      setSelectedAnalytics(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch analytics.');
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <section className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium bg-indigo-950/80 border border-indigo-800/60 text-indigo-300">
            <Building2 className="w-3.5 h-3.5" />
            <span>College Administration</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            College Assessment Portal
          </h1>
          <p className="text-sm text-slate-400">
            Welcome, {profile?.full_name || 'Administrator'} · Manage department coding assessments and cohort submissions.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Create New Assessment</span>
        </button>
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

      {/* Task List Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
            Department Coding Tasks ({tasks.length})
          </h2>
        </div>

        {isLoading ? (
          <div className="p-12 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
            <p className="text-sm">Loading college tasks…</p>
          </div>
        ) : tasks.length === 0 ? (
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center space-y-4">
            <FileCode className="w-12 h-12 text-slate-600 mx-auto" />
            <div>
              <p className="font-semibold text-white">No College Tasks Created Yet</p>
              <p className="text-xs text-slate-400 mt-1">
                Create your first departmental coding assessment to deploy to your students.
              </p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create Task</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {tasks.map(task => (
              <div
                key={task.id}
                className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4 hover:border-slate-700 transition"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {task.domain}
                    </span>
                    <h3 className="font-bold text-white text-base">{task.title}</h3>
                  </div>
                  <span
                    className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                      task.status === 'published'
                        ? 'bg-emerald-950/80 border border-emerald-800 text-emerald-300'
                        : task.status === 'closed'
                        ? 'bg-rose-950/80 border border-rose-800 text-rose-300'
                        : task.status === 'draft'
                        ? 'bg-amber-950/80 border border-amber-800 text-amber-300'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {task.status.toUpperCase()}
                  </span>
                </div>

                <p className="text-xs text-slate-400 line-clamp-2">{task.description}</p>

                <div className="flex items-center gap-4 text-xs text-slate-500 pt-2 border-t border-slate-800/80">
                  <span className="flex items-center space-x-1">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{task.duration_minutes}m</span>
                  </span>
                  <span className="capitalize">{task.difficulty}</span>
                  <span className="flex items-center space-x-1">
                    <Users className="w-3.5 h-3.5" />
                    <span>{task.assigned_student_ids.length ? `${task.assigned_student_ids.length} Assigned` : 'All Dept'}</span>
                  </span>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between pt-2">
                  <button
                    onClick={() => handleViewAnalytics(task.id)}
                    className="inline-flex items-center space-x-1 text-xs font-semibold text-indigo-400 hover:text-indigo-300"
                  >
                    <BarChart2 className="w-3.5 h-3.5" />
                    <span>Analytics</span>
                  </button>

                  <div className="flex items-center space-x-2">
                    {task.status === 'published' ? (
                      <button
                        onClick={() => handleStatusChange(task.id, 'closed')}
                        className="px-2.5 py-1 text-xs rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800"
                      >
                        Close Submissions
                      </button>
                    ) : task.status === 'closed' || task.status === 'draft' ? (
                      <button
                        onClick={() => handleStatusChange(task.id, 'published')}
                        className="px-2.5 py-1 text-xs rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold"
                      >
                        Publish
                      </button>
                    ) : null}

                    {task.status !== 'archived' && (
                      <button
                        onClick={() => handleStatusChange(task.id, 'archived')}
                        className="p-1.5 text-slate-400 hover:text-rose-400"
                        title="Archive Task"
                      >
                        <Archive className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Create Task Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base">Create Department Coding Task</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateTask} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Task Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  placeholder="e.g. Distributed Task Queue Mechanism"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Problem Description</label>
                <textarea
                  required
                  rows={3}
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder="Detail the technical requirements and constraints..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Technical Domain</label>
                  <select
                    value={domain}
                    onChange={e => setDomain(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
                  >
                    <option>Algorithms & DSA</option>
                    <option>Web Development</option>
                    <option>Backend Development</option>
                    <option>Cloud Computing</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Difficulty Tier</label>
                  <select
                    value={difficulty}
                    onChange={e => setDifficulty(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
                  >
                    <option value="easy">Easy (Novice)</option>
                    <option value="medium">Medium (Adept)</option>
                    <option value="hard">Hard (Master)</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Duration (mins)</label>
                  <input
                    type="number"
                    min={15}
                    max={240}
                    value={duration}
                    onChange={e => setDuration(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Starter Code</label>
                <textarea
                  rows={3}
                  value={starterCode}
                  onChange={e => setStarterCode(e.target.value)}
                  className="w-full font-mono bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-emerald-400"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-xs rounded-xl border border-slate-800 text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 text-xs rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition"
                >
                  {isSubmitting ? 'Creating…' : 'Publish Task'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Analytics Modal */}
      {selectedAnalytics && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <p className="text-[10px] uppercase font-bold text-indigo-400">Task Performance Analytics</p>
                <h3 className="font-bold text-white text-base">{selectedAnalytics.title}</h3>
              </div>
              <button onClick={() => setSelectedAnalytics(null)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-center">
                <p className="text-xs text-slate-400">Assigned Cohort</p>
                <p className="text-xl font-bold text-white mt-1">{selectedAnalytics.total_assigned}</p>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-center">
                <p className="text-xs text-slate-400">Completed Submissions</p>
                <p className="text-xl font-bold text-emerald-400 mt-1">{selectedAnalytics.total_completed}</p>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-center">
                <p className="text-xs text-slate-400">Average Score</p>
                <p className="text-xl font-bold text-sky-400 mt-1">{selectedAnalytics.avg_score}%</p>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-center">
                <p className="text-xs text-slate-400">Cohort Pass Rate</p>
                <p className="text-xl font-bold text-indigo-400 mt-1">{selectedAnalytics.pass_rate}%</p>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedAnalytics(null)}
                className="px-4 py-2 text-xs rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

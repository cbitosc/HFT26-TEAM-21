/**
 * StudentPortfolioPage — Module 3: Portfolio Upload, Extraction Review & Confirmation.
 * Allows students to upload PDF/JSON portfolios, review & edit extracted details,
 * and confirm their eligible technical boundary for adaptive assessments.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  FileUp,
  FileText,
  FileCode,
  CheckCircle2,
  Clock,
  Plus,
  Trash2,
  X,
  ArrowLeft,
  ShieldAlert,
  Loader2,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import {
  PortfolioResponse,
  PortfolioStructure,
  ProjectItem,
} from '../../types/portfolio';
import {
  fetchStudentPortfolio,
  uploadStudentPortfolio,
  confirmStudentPortfolio,
} from '../../services/portfolio';
import { Alert } from '../../components/Alert';
import { Button } from '../../components/Button';
import { DEMO_STUDENT_PORTFOLIO } from '../../services/demoData';

export const StudentPortfolioPage: React.FC = () => {
  const { session, isGuest } = useAuth();
  const token = session?.access_token || '';

  // Data states
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [formData, setFormData] = useState<PortfolioStructure>({
    projects: [],
    skills: { programming_languages: [], frameworks_and_tools: [] },
    domains: [],
    dsa_topics: [],
  });

  // UI state
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // New tag input local state
  const [newLang, setNewLang] = useState<string>('');
  const [newTool, setNewTool] = useState<string>('');
  const [newDomain, setNewDomain] = useState<string>('');
  const [newDsa, setNewDsa] = useState<string>('');

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch initial portfolio
  const loadPortfolio = useCallback(async () => {
    if (isGuest) {
      setIsLoading(false);
      setPortfolio(DEMO_STUDENT_PORTFOLIO);
      setFormData({
        projects: DEMO_STUDENT_PORTFOLIO.data.projects.map(p => ({
          name: p.name,
          description: p.description,
          technologies: p.technologies,
        })),
        skills: {
          programming_languages: ['Python', 'TypeScript'],
          frameworks_and_tools: ['React', 'FastAPI', 'Docker', 'PostgreSQL'],
        },
        domains: ['Algorithms & Problem Solving', 'Full-Stack Web Architecture'],
        dsa_topics: ['Dynamic Programming', 'Graph Theory', 'Trees & BSTs'],
      });
      return;
    }

    if (!token) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchStudentPortfolio(token);
      if (data) {
        setPortfolio(data);
        setFormData(data.data);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Could not load existing portfolio.');
    } finally {
      setIsLoading(false);
    }
  }, [token, isGuest]);

  useEffect(() => {
    loadPortfolio();
  }, [loadPortfolio]);

  // File selection handling
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      validateAndSetFile(file);
    }
  };

  const validateAndSetFile = (file: File) => {
    setError(null);
    const validExtensions = ['.pdf', '.json'];
    const isSupported = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    if (!isSupported) {
      setError('Unsupported file type. Please upload a .pdf or .json portfolio file.');
      setSelectedFile(null);
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError('File size exceeds the 5 MB limit.');
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
  };

  // Drag and drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  // Upload handler
  const handleUpload = async () => {
    if (!selectedFile || !token) return;
    setIsUploading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const res = await uploadStudentPortfolio(selectedFile, token);
      setPortfolio(res);
      setFormData(res.data);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setSuccessMessage('Portfolio parsed successfully. Please review and edit the extracted details below.');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Upload processing failed.');
    } finally {
      setIsUploading(false);
    }
  };

  // Confirm / Save handler
  const handleConfirm = async () => {
    if (!token) return;
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const res = await confirmStudentPortfolio(formData, token);
      setPortfolio(res);
      setFormData(res.data);
      setSuccessMessage('Portfolio successfully confirmed! Your eligible assessment boundaries are set.');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Could not confirm portfolio.');
    } finally {
      setIsSaving(false);
    }
  };

  // Tag manipulation helpers
  const addTag = (category: 'languages' | 'tools' | 'domains' | 'dsa', value: string) => {
    const trimmed = value.trim();
    if (!trimmed) return;

    if (category === 'languages') {
      if (!formData.skills.programming_languages.includes(trimmed)) {
        setFormData({
          ...formData,
          skills: {
            ...formData.skills,
            programming_languages: [...formData.skills.programming_languages, trimmed],
          },
        });
      }
      setNewLang('');
    } else if (category === 'tools') {
      if (!formData.skills.frameworks_and_tools.includes(trimmed)) {
        setFormData({
          ...formData,
          skills: {
            ...formData.skills,
            frameworks_and_tools: [...formData.skills.frameworks_and_tools, trimmed],
          },
        });
      }
      setNewTool('');
    } else if (category === 'domains') {
      if (!formData.domains.includes(trimmed)) {
        setFormData({
          ...formData,
          domains: [...formData.domains, trimmed],
        });
      }
      setNewDomain('');
    } else if (category === 'dsa') {
      if (!formData.dsa_topics.includes(trimmed)) {
        setFormData({
          ...formData,
          dsa_topics: [...formData.dsa_topics, trimmed],
        });
      }
      setNewDsa('');
    }
  };

  const removeTag = (category: 'languages' | 'tools' | 'domains' | 'dsa', index: number) => {
    if (category === 'languages') {
      const copy = [...formData.skills.programming_languages];
      copy.splice(index, 1);
      setFormData({
        ...formData,
        skills: { ...formData.skills, programming_languages: copy },
      });
    } else if (category === 'tools') {
      const copy = [...formData.skills.frameworks_and_tools];
      copy.splice(index, 1);
      setFormData({
        ...formData,
        skills: { ...formData.skills, frameworks_and_tools: copy },
      });
    } else if (category === 'domains') {
      const copy = [...formData.domains];
      copy.splice(index, 1);
      setFormData({ ...formData, domains: copy });
    } else if (category === 'dsa') {
      const copy = [...formData.dsa_topics];
      copy.splice(index, 1);
      setFormData({ ...formData, dsa_topics: copy });
    }
  };

  // Project manipulation
  const addProject = () => {
    setFormData({
      ...formData,
      projects: [
        ...formData.projects,
        { name: '', description: '', technologies: [] },
      ],
    });
  };

  const updateProject = (index: number, field: keyof ProjectItem, value: any) => {
    const copy = [...formData.projects];
    copy[index] = { ...copy[index], [field]: value };
    setFormData({ ...formData, projects: copy });
  };

  const removeProject = (index: number) => {
    const copy = [...formData.projects];
    copy.splice(index, 1);
    setFormData({ ...formData, projects: copy });
  };

  const addProjectTech = (projIndex: number, tech: string) => {
    const trimmed = tech.trim();
    if (!trimmed) return;
    const proj = formData.projects[projIndex];
    if (!proj.technologies.includes(trimmed)) {
      updateProject(projIndex, 'technologies', [...proj.technologies, trimmed]);
    }
  };

  const removeProjectTech = (projIndex: number, techIndex: number) => {
    const proj = formData.projects[projIndex];
    const copy = [...proj.technologies];
    copy.splice(techIndex, 1);
    updateProject(projIndex, 'technologies', copy);
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Navigation & Header */}
      <div className="space-y-3">
        <Link
          to="/dashboard/student"
          className="inline-flex items-center space-x-2 text-xs font-medium text-slate-400 hover:text-sky-400 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Dashboard</span>
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white flex items-center space-x-2">
              <span>Student Portfolio</span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-sky-950 border border-sky-800 text-sky-400">
                Module 3
              </span>
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Upload your projects and resume in PDF or JSON format to define your verified assessment scope.
            </p>
          </div>

          {portfolio && (
            <div className="flex items-center space-x-2 text-xs">
              <span
                className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full font-medium ${
                  portfolio.confirmed
                    ? 'bg-emerald-950/80 border border-emerald-800/80 text-emerald-300'
                    : 'bg-amber-950/80 border border-amber-800/80 text-amber-300'
                }`}
              >
                {portfolio.confirmed ? (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Confirmed Profile</span>
                  </>
                ) : (
                  <>
                    <Clock className="w-3.5 h-3.5" />
                    <span>Draft (Unconfirmed)</span>
                  </>
                )}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Alerts */}
      {error && <Alert variant="error" message={error} />}
      {successMessage && <Alert variant="success" message={successMessage} />}

      {/* Upload Zone */}
      <section className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="text-base font-semibold text-white flex items-center space-x-2">
          <FileUp className="w-4 h-4 text-sky-400" />
          <span>Upload Portfolio File</span>
        </h2>

        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition flex flex-col items-center justify-center space-y-3 ${
            dragActive
              ? 'border-sky-500 bg-sky-950/30'
              : selectedFile
              ? 'border-emerald-600 bg-slate-800/40'
              : 'border-slate-700 hover:border-slate-600 bg-slate-950/40'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.json"
            onChange={handleFileChange}
            className="hidden"
          />

          <div className="w-12 h-12 rounded-full bg-slate-800/80 flex items-center justify-center text-slate-300">
            {selectedFile?.name.endsWith('.pdf') ? (
              <FileText className="w-6 h-6 text-red-400" />
            ) : selectedFile?.name.endsWith('.json') ? (
              <FileCode className="w-6 h-6 text-amber-400" />
            ) : (
              <FileUp className="w-6 h-6 text-sky-400" />
            )}
          </div>

          <div>
            {selectedFile ? (
              <div className="space-y-1">
                <p className="text-sm font-semibold text-white">{selectedFile.name}</p>
                <p className="text-xs text-slate-400">
                  {(selectedFile.size / 1024).toFixed(1)} KB — Ready to extract
                </p>
              </div>
            ) : (
              <div className="space-y-1">
                <p className="text-sm font-medium text-slate-200">
                  Drag and drop your <span className="text-sky-400">.pdf</span> or{' '}
                  <span className="text-sky-400">.json</span> file here
                </p>
                <p className="text-xs text-slate-500">Supports PDF resumes or JSON project export (Max 5 MB)</p>
              </div>
            )}
          </div>
        </div>

        {selectedFile && (
          <div className="flex items-center justify-end space-x-3 pt-2">
            <Button
              variant="secondary"
              className="py-1.5 px-3 text-xs"
              onClick={() => {
                setSelectedFile(null);
                if (fileInputRef.current) fileInputRef.current.value = '';
              }}
              disabled={isUploading}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              className="py-1.5 px-4 text-xs"
              onClick={handleUpload}
              isLoading={isUploading}
            >
              <Sparkles className="w-4 h-4 mr-1.5" />
              Process & Extract Portfolio
            </Button>
          </div>
        )}
      </section>

      {/* Mandatory Disclaimer Alert */}
      <div className="rounded-xl border border-sky-900/60 bg-sky-950/20 p-4 flex items-start space-x-3">
        <ShieldAlert className="w-5 h-5 text-sky-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-slate-300 space-y-1">
          <p className="font-semibold text-sky-300">Important Evaluation Policy:</p>
          <p className="text-slate-400 leading-relaxed">
            Confirming your portfolio verifies your submitted information and defines your eligible assessment boundary.
            Claimed skills are marked <span className="text-amber-400 font-semibold">unverified</span> and do not establish
            technical proficiency until validated through deterministic coding assessments.
          </p>
        </div>
      </div>

      {/* Extracted Details & Review Section */}
      {isLoading ? (
        <div className="p-12 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-6 h-6 animate-spin text-sky-400" />
          <p className="text-sm">Loading portfolio details…</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Projects */}
          <section className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-semibold text-white">Projects</h2>
                <p className="text-xs text-slate-400">Your key software engineering projects and repositories</p>
              </div>
              <Button variant="secondary" className="py-1 px-3 text-xs" onClick={addProject}>
                <Plus className="w-3.5 h-3.5 mr-1" />
                Add Project
              </Button>
            </div>

            {formData.projects.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-4 text-center">
                No projects extracted yet. Upload a portfolio file or add projects manually above.
              </p>
            ) : (
              <div className="space-y-4">
                {formData.projects.map((proj, pIdx) => (
                  <div
                    key={pIdx}
                    className="p-4 rounded-lg border border-slate-800 bg-slate-950/50 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <input
                        type="text"
                        placeholder="Project Name (e.g. Distributed Task Queue)"
                        value={proj.name}
                        onChange={e => updateProject(pIdx, 'name', e.target.value)}
                        className="bg-transparent text-sm font-semibold text-white focus:outline-none focus:ring-1 focus:ring-sky-500 rounded px-2 py-1 w-full max-w-md border border-transparent hover:border-slate-700"
                      />
                      <button
                        type="button"
                        onClick={() => removeProject(pIdx)}
                        className="text-slate-500 hover:text-red-400 p-1 transition"
                        title="Remove project"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>

                    <textarea
                      placeholder="Project description and key technical contributions…"
                      value={proj.description}
                      onChange={e => updateProject(pIdx, 'description', e.target.value)}
                      rows={2}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-300 focus:outline-none focus:border-sky-500 transition"
                    />

                    {/* Technologies */}
                    <div className="space-y-1.5">
                      <label className="text-[11px] font-medium text-slate-400">Technologies Used:</label>
                      <div className="flex flex-wrap items-center gap-1.5">
                        {proj.technologies.map((tech, tIdx) => (
                          <span
                            key={tIdx}
                            className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-200 border border-slate-700"
                          >
                            <span>{tech}</span>
                            <button
                              type="button"
                              onClick={() => removeProjectTech(pIdx, tIdx)}
                              className="text-slate-400 hover:text-white"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </span>
                        ))}
                        <input
                          type="text"
                          placeholder="+ Add tech and press Enter"
                          onKeyDown={e => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              addProjectTech(pIdx, (e.target as HTMLInputElement).value);
                              (e.target as HTMLInputElement).value = '';
                            }
                          }}
                          className="bg-slate-900 border border-slate-800 rounded px-2 py-0.5 text-xs text-slate-300 focus:outline-none focus:border-sky-500"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Skills Breakdown */}
          <section className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-semibold text-white flex items-center space-x-2">
                  <span>Skills</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/80 border border-amber-800/80 text-amber-300 uppercase tracking-wide">
                    Status: Unverified
                  </span>
                </h2>
                <p className="text-xs text-slate-400">Languages and tools detected from your portfolio</p>
              </div>
            </div>

            {/* Programming Languages */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300">Programming Languages</label>
              <div className="flex flex-wrap items-center gap-2">
                {formData.skills.programming_languages.map((lang, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-sky-950/70 border border-sky-800/60 text-sky-300"
                  >
                    <span>{lang}</span>
                    <button
                      type="button"
                      onClick={() => removeTag('languages', idx)}
                      className="text-sky-400 hover:text-white"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
                <div className="inline-flex items-center">
                  <input
                    type="text"
                    placeholder="Add language…"
                    value={newLang}
                    onChange={e => setNewLang(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addTag('languages', newLang);
                      }
                    }}
                    className="bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1 text-xs text-slate-300 focus:outline-none focus:border-sky-500 w-32"
                  />
                  <button
                    type="button"
                    onClick={() => addTag('languages', newLang)}
                    className="ml-1 text-slate-400 hover:text-sky-400 p-1"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>

            {/* Frameworks & Tools */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300">Frameworks, Libraries & Developer Tools</label>
              <div className="flex flex-wrap items-center gap-2">
                {formData.skills.frameworks_and_tools.map((tool, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-slate-800 border border-slate-700 text-slate-200"
                  >
                    <span>{tool}</span>
                    <button
                      type="button"
                      onClick={() => removeTag('tools', idx)}
                      className="text-slate-400 hover:text-white"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
                <div className="inline-flex items-center">
                  <input
                    type="text"
                    placeholder="Add tool/framework…"
                    value={newTool}
                    onChange={e => setNewTool(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addTag('tools', newTool);
                      }
                    }}
                    className="bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1 text-xs text-slate-300 focus:outline-none focus:border-sky-500 w-36"
                  />
                  <button
                    type="button"
                    onClick={() => addTag('tools', newTool)}
                    className="ml-1 text-slate-400 hover:text-sky-400 p-1"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </section>

          {/* Technical Domains */}
          <section className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
            <div>
              <h2 className="text-base font-semibold text-white">Relevant Technical Domains</h2>
              <p className="text-xs text-slate-400">High-level domains matching your software focus</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {formData.domains.map((dom, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-indigo-950/70 border border-indigo-800/60 text-indigo-300"
                >
                  <span>{dom}</span>
                  <button
                    type="button"
                    onClick={() => removeTag('domains', idx)}
                    className="text-indigo-400 hover:text-white"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
              <div className="inline-flex items-center">
                <input
                  type="text"
                  placeholder="Add domain…"
                  value={newDomain}
                  onChange={e => setNewDomain(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      addTag('domains', newDomain);
                    }
                  }}
                  className="bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1 text-xs text-slate-300 focus:outline-none focus:border-indigo-500 w-32"
                />
                <button
                  type="button"
                  onClick={() => addTag('domains', newDomain)}
                  className="ml-1 text-slate-400 hover:text-indigo-400 p-1"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </section>

          {/* DSA Topics */}
          <section className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
            <div>
              <h2 className="text-base font-semibold text-white">Claimed Data Structures & Algorithms Topics</h2>
              <p className="text-xs text-slate-400">
                Topics you have studied or applied. SkillProof AI strictly respects these boundaries during assessments.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {formData.dsa_topics.map((topic, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-950/70 border border-emerald-800/60 text-emerald-300"
                >
                  <span>{topic}</span>
                  <button
                    type="button"
                    onClick={() => removeTag('dsa', idx)}
                    className="text-emerald-400 hover:text-white"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
              <div className="inline-flex items-center">
                <input
                  type="text"
                  placeholder="Add DSA topic…"
                  value={newDsa}
                  onChange={e => setNewDsa(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      addTag('dsa', newDsa);
                    }
                  }}
                  className="bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1 text-xs text-slate-300 focus:outline-none focus:border-emerald-500 w-36"
                />
                <button
                  type="button"
                  onClick={() => addTag('dsa', newDsa)}
                  className="ml-1 text-slate-400 hover:text-emerald-400 p-1"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </section>

          {/* Confirmation Action Footer */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <p className="text-xs font-semibold text-white">Ready to lock in your assessment scope?</p>
              <p className="text-xs text-slate-400">
                Confirming updates your profile and enables adaptive question generation tailored to these boundaries.
              </p>
            </div>
            <Button
              variant="primary"
              className="py-2.5 px-5 text-xs font-semibold"
              onClick={handleConfirm}
              isLoading={isSaving}
            >
              <CheckCircle2 className="w-4 h-4 mr-1.5" />
              Confirm Portfolio
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

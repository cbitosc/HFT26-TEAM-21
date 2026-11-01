/**
 * AiAssistantDrawer — Module 9: Guarded AI Coding Assistant
 *
 * Security contract (enforced on the backend; respected here):
 *  - Novice + Verified track: assistant is disabled (403 from server, also guarded in UI).
 *  - Adept/Master + Verified track: guarded mode (hints only, no free-form solve-it-for-me).
 *  - Practice track: open educational mode.
 *  - Advisory notice is always displayed.
 *  - No reference solutions, no grading data, no hidden test cases are ever sent or displayed.
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles,
  ShieldOff,
  ChevronRight,
  MessageSquare,
  Lightbulb,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Send,
  Bot,
  User,
  Info,
} from 'lucide-react';
import {
  AssistantChatMessage,
  AssistantHintRequest,
  AssistantExplainErrorRequest,
  AssistantChatRequest,
  AssistantResponse,
  QuestionPublic,
  SampleRunResponse,
} from '../types/assessment';
import {
  requestAssistantHint,
  requestErrorExplanation,
  requestAssistantChat,
} from '../services/assessment';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AiAssistantDrawerProps {
  sessionId: string;
  question: QuestionPublic;
  assessmentTier: string;
  assessmentTrack: string;
  currentCode: string;
  token: string;
  lastErrorMessage?: string | null;
  latestExecutionResult?: SampleRunResponse | null;
  isGuest?: boolean;
}

type ActiveTab = 'hint' | 'error' | 'chat';
type HintLevel = 1 | 2 | 3;

// ---------------------------------------------------------------------------
// Helper: Source badge
// ---------------------------------------------------------------------------

const SourceBadge: React.FC<{ source: 'featherless' | 'fallback' }> = ({ source }) => (
  <span
    className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono border ${
      source === 'featherless'
        ? 'bg-indigo-950 text-indigo-300 border-indigo-800'
        : 'bg-slate-800 text-slate-400 border-slate-700'
    }`}
  >
    {source === 'featherless' ? '✦ AI Generated' : '⊙ Deterministic Fallback'}
  </span>
);

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export const AiAssistantDrawer: React.FC<AiAssistantDrawerProps> = ({
  sessionId,
  question,
  assessmentTier,
  assessmentTrack,
  currentCode,
  token,
  lastErrorMessage,
  latestExecutionResult,
  isGuest = false,
}) => {
  // Derive capability from track + tier (matches backend Mode Matrix)
  const isDisabled =
    (assessmentTrack || '').toLowerCase() === 'verified' &&
    (assessmentTier || '').toLowerCase() === 'novice';

  // Compute active error / execution diagnostics
  const hasExecuted = Boolean(latestExecutionResult);
  const effectiveError =
    lastErrorMessage ||
    (latestExecutionResult
      ? latestExecutionResult.error_message ||
        latestExecutionResult.compile_output ||
        latestExecutionResult.stderr ||
        (latestExecutionResult.passed === false && latestExecutionResult.expected_output
          ? `Output mismatch: Expected '${latestExecutionResult.expected_output}', got '${latestExecutionResult.actual_output || '(no output)'}'`
          : null)
      : null);

  // UI state
  const [activeTab, setActiveTab] = useState<ActiveTab>('hint');
  const [hintLevel, setHintLevel] = useState<HintLevel>(1);
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<AssistantResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [rateLimited, setRateLimited] = useState(false);

  // Chat state
  const [chatHistory, setChatHistory] = useState<AssistantChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  // Reset response on question / tab change
  useEffect(() => {
    setResponse(null);
    setErrorMsg(null);
    setRateLimited(false);
  }, [question.id, activeTab]);

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const handleError = (err: unknown) => {
    const message = err instanceof Error ? err.message : 'Unexpected error occurred.';
    if (message.includes('HTTP 429')) {
      setRateLimited(true);
      setErrorMsg('Rate limit reached. Please wait a moment before requesting another hint.');
    } else if (message.includes('HTTP 403')) {
      setErrorMsg('The AI assistant is not available for this assessment tier and track combination.');
    } else {
      setErrorMsg(message);
    }
  };

  const handleRequestHint = async () => {
    if (isLoading) return;
    setIsLoading(true);
    setResponse(null);
    setErrorMsg(null);
    setRateLimited(false);

    if (isGuest || sessionId?.startsWith('demo') || !token) {
      setTimeout(() => {
        const demoHints: Record<number, string> = {
          1: `Level 1 Conceptual Nudge for ${question.title}: Break down the problem invariant. For each element you examine, what counterpart or condition must exist to satisfy the target?`,
          2: `Level 2 Algorithmic Strategy: Avoid O(N^2) pairwise comparisons. Can you store elements you have already inspected in a Hash Map (lookup dictionary) or use Two Pointers to achieve O(N) linear time?`,
          3: `Level 3 Structured Pseudocode: 1. Initialize lookup = {}. 2. Loop through elements checking complement condition. 3. If complement in lookup, return indices; otherwise record current element.`,
        };
        setResponse({
          reply: demoHints[hintLevel] || demoHints[1],
          hint_level: hintLevel,
          mode: 'practice',
          is_guarded: false,
          source: 'fallback',
          advisory_notice: 'AI assistance is advisory and designed to guide your problem-solving.',
        });
        setIsLoading(false);
      }, 350);
      return;
    }

    const params: AssistantHintRequest = {
      question_id: question.id,
      current_code: currentCode,
      hint_level: hintLevel,
    };

    try {
      const res = await requestAssistantHint(sessionId, params, token);
      setResponse(res);
    } catch (err) {
      handleError(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExplainError = async (overrideError?: string) => {
    const targetError = overrideError || effectiveError || 'Execution check';
    if (isLoading) return;
    setIsLoading(true);
    setResponse(null);
    setErrorMsg(null);
    setRateLimited(false);

    if (isGuest || sessionId?.startsWith('demo') || !token) {
      setTimeout(() => {
        setResponse({
          reply: `Conceptual Analysis: The sandbox reported: "${targetError}". In ${question.title}, verify that your return value structure matches the sample output format, and check boundary index conditions.`,
          hint_level: undefined,
          mode: 'practice',
          is_guarded: false,
          source: 'fallback',
          advisory_notice: 'AI assistance is advisory and designed to guide your problem-solving.',
        });
        setIsLoading(false);
      }, 350);
      return;
    }

    const params: AssistantExplainErrorRequest = {
      question_id: question.id,
      current_code: currentCode,
      error_message: targetError,
    };

    try {
      const res = await requestErrorExplanation(sessionId, params, token);
      setResponse(res);
    } catch (err) {
      handleError(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendChat = async () => {
    if (!chatInput.trim() || isLoading) return;
    const message = chatInput.trim();
    setChatInput('');
    setErrorMsg(null);
    setRateLimited(false);

    // Optimistically append user message
    const newHistory: AssistantChatMessage[] = [
      ...chatHistory,
      { role: 'user', content: message },
    ];
    setChatHistory(newHistory);
    setIsLoading(true);

    if (isGuest || sessionId?.startsWith('demo') || !token) {
      setTimeout(() => {
        const demoReply = `Regarding "${message}": For ${question.title}, think about how the state evolves on each step. What data structure gives you fast lookup without re-scanning the array? Try stepping through with a small input case.`;
        setChatHistory([
          ...newHistory,
          { role: 'assistant', content: demoReply },
        ]);
        setResponse({
          reply: demoReply,
          mode: 'practice',
          is_guarded: false,
          source: 'fallback',
          advisory_notice: 'AI assistance is advisory and designed to guide your problem-solving.',
        });
        setIsLoading(false);
      }, 350);
      return;
    }

    const params: AssistantChatRequest = {
      question_id: question.id,
      message,
      current_code: currentCode,
      history: chatHistory.slice(-8), // send last 8 turns to stay within backend's 10-message limit
    };

    try {
      const res = await requestAssistantChat(sessionId, params, token);
      setChatHistory([
        ...newHistory,
        { role: 'assistant', content: res.reply },
      ]);
      setResponse(res); // capture source + advisory for display
    } catch (err) {
      handleError(err);
      const errMsg = err instanceof Error ? err.message : 'Assistant failed to respond.';
      setChatHistory([
        ...newHistory,
        { role: 'assistant', content: `[Guidance Notice]: ${errMsg}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChatKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendChat();
    }
  };

  // ---------------------------------------------------------------------------
  // Disabled state — Novice Verified
  // ---------------------------------------------------------------------------

  if (isDisabled) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 flex flex-col items-center justify-center space-y-3 text-center min-h-[180px]">
        <ShieldOff className="w-8 h-8 text-slate-600" />
        <div>
          <p className="text-sm font-semibold text-slate-300">AI Assistant Disabled</p>
          <p className="text-xs text-slate-500 mt-1 max-w-xs leading-relaxed">
            The AI assistant is not available on the <span className="text-sky-400 font-mono">Novice Verified</span> track.
            Independent problem solving is required to establish verified assessment credibility.
          </p>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Mode badge
  // ---------------------------------------------------------------------------

  const modeBadge =
    assessmentTrack === 'practice' ? (
      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded border bg-indigo-950 text-indigo-300 border-indigo-800">
        Practice Mode
      </span>
    ) : (
      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded border bg-amber-950 text-amber-400 border-amber-800">
        Guarded Mode
      </span>
    );

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-slate-950 px-4 py-2.5 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <span className="text-xs font-semibold text-slate-300">AI Coding Assistant</span>
          {modeBadge}
        </div>
      </div>

      {/* Advisory Notice */}
      <div className="px-4 py-2 border-b border-slate-800/60 bg-slate-950/40 flex items-start space-x-2">
        <Info className="w-3 h-3 text-slate-500 mt-0.5 flex-shrink-0" />
        <p className="text-[10px] text-slate-500 italic leading-relaxed">
          This assistant provides directional guidance only. It does not provide direct solutions, reference
          implementations, or grading evaluations. All code is evaluated deterministically.
        </p>
      </div>

      {/* Tab Selector */}
      <div className="flex border-b border-slate-800">
        {(['hint', 'error', 'chat'] as ActiveTab[]).map((tab) => {
          const labels: Record<ActiveTab, string> = {
            hint: 'Hints',
            error: 'Explain Error',
            chat: 'Chat',
          };
          const icons: Record<ActiveTab, React.ReactNode> = {
            hint: <Lightbulb className="w-3 h-3" />,
            error: <AlertCircle className="w-3 h-3" />,
            chat: <MessageSquare className="w-3 h-3" />,
          };
          const isErrorTab = tab === 'error';
          const isErrorDisabled = isErrorTab && !hasExecuted;

          return (
            <button
              key={tab}
              onClick={() => !isErrorDisabled && setActiveTab(tab)}
              disabled={isErrorDisabled}
              className={`flex-1 flex items-center justify-center space-x-1.5 px-3 py-2 text-xs font-semibold transition ${
                activeTab === tab
                  ? 'bg-slate-800 text-indigo-300 border-b-2 border-indigo-500'
                  : isErrorDisabled
                  ? 'text-slate-700 cursor-not-allowed'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              {icons[tab]}
              <span>{labels[tab]}</span>
              {isErrorTab && !hasExecuted && (
                <span className="text-[9px] text-slate-600">(run code first)</span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="p-4 flex-1 space-y-4 overflow-y-auto max-h-[420px]">

        {/* ── Hint Tab ── */}
        {activeTab === 'hint' && (
          <div className="space-y-4">
            <div className="space-y-2">
              <p className="text-xs text-slate-400 font-medium">Select hint depth:</p>
              <div className="grid grid-cols-3 gap-2">
                {([1, 2, 3] as HintLevel[]).map((level) => {
                  const labels = ['Level 1: Nudge', 'Level 2: Strategy', 'Level 3: Pseudocode'];
                  const desc = [
                    'A directional observation about your approach.',
                    'A higher-level algorithmic strategy suggestion.',
                    'A structured pseudocode outline (no working code).',
                  ];
                  return (
                    <button
                      key={level}
                      onClick={() => setHintLevel(level)}
                      title={desc[level - 1]}
                      className={`px-3 py-2 rounded-lg text-xs font-semibold border transition ${
                        hintLevel === level
                          ? 'bg-indigo-900 border-indigo-600 text-indigo-200'
                          : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-indigo-700 hover:text-slate-200'
                      }`}
                    >
                      {labels[level - 1]}
                    </button>
                  );
                })}
              </div>
              <p className="text-[10px] text-slate-600 italic">
                {['A directional observation about your approach.',
                  'A higher-level algorithmic strategy suggestion.',
                  'A structured pseudocode outline — no working implementation.'][hintLevel - 1]}
              </p>
            </div>

            <button
              onClick={handleRequestHint}
              disabled={isLoading}
              className="w-full inline-flex items-center justify-center space-x-2 px-4 py-2.5 rounded-lg bg-indigo-700 hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-bold transition"
            >
              {isLoading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Lightbulb className="w-3.5 h-3.5" />
              )}
              <span>{isLoading ? 'Generating hint…' : `Get Level ${hintLevel} Hint`}</span>
            </button>

            {/* Response */}
            {response && (
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <SourceBadge source={response.source} />
                  {response.hint_level !== null && response.hint_level !== undefined && (
                    <span className="text-[10px] text-slate-500 font-mono">
                      Level {response.hint_level} hint
                    </span>
                  )}
                </div>
                <div className="bg-slate-950 rounded-lg p-3 border border-slate-800 text-xs text-slate-200 leading-relaxed whitespace-pre-wrap">
                  {response.reply}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Explain Error Tab ── */}
        {activeTab === 'error' && (
          <div className="space-y-4">
            {hasExecuted ? (
              <>
                {effectiveError ? (
                  <div className="bg-rose-950/30 border border-rose-900/50 rounded-lg p-3 space-y-1">
                    <p className="text-[10px] font-bold text-rose-400 uppercase">Sandbox Diagnostic</p>
                    <p className="text-xs font-mono text-rose-300 whitespace-pre-wrap">{effectiveError}</p>
                  </div>
                ) : (
                  <div className="bg-emerald-950/30 border border-emerald-900/50 rounded-lg p-3 space-y-1">
                    <div className="flex items-center space-x-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <p className="text-xs font-semibold text-emerald-300">Sample Execution Passed</p>
                    </div>
                    <p className="text-[11px] text-slate-400">
                      Your solution passed the sample test case. You can request an algorithmic efficiency or optimization review.
                    </p>
                  </div>
                )}

                <button
                  onClick={() => handleExplainError(effectiveError || 'Code passed sample tests. Analyze time and space complexity.')}
                  disabled={isLoading}
                  className={`w-full inline-flex items-center justify-center space-x-2 px-4 py-2.5 rounded-lg text-white text-xs font-bold transition disabled:opacity-50 disabled:cursor-not-allowed ${
                    effectiveError
                      ? 'bg-rose-800 hover:bg-rose-700'
                      : 'bg-emerald-800 hover:bg-emerald-700'
                  }`}
                >
                  {isLoading ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : effectiveError ? (
                    <AlertCircle className="w-3.5 h-3.5" />
                  ) : (
                    <Sparkles className="w-3.5 h-3.5" />
                  )}
                  <span>
                    {isLoading
                      ? 'Analyzing…'
                      : effectiveError
                      ? 'Explain This Issue'
                      : 'Review Complexity & Optimization'}
                  </span>
                </button>

                {response && (
                  <div className="space-y-2">
                    <SourceBadge source={response.source} />
                    <div className="bg-slate-950 rounded-lg p-3 border border-slate-800 text-xs text-slate-200 leading-relaxed whitespace-pre-wrap">
                      {response.reply}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center space-y-2 py-6">
                <AlertCircle className="w-7 h-7 text-slate-600 mx-auto" />
                <p className="text-xs text-slate-500">
                  Run your code using the <span className="font-semibold text-slate-400">Run Sample</span> button first.
                  Once executed, any compiler errors, runtime exceptions, or output discrepancies will be analyzed here.
                </p>
              </div>
            )}
          </div>
        )}

        {/* ── Chat Tab ── */}
        {activeTab === 'chat' && (
          <div className="space-y-3 flex flex-col">
            {/* Chat history */}
            <div className="space-y-2 min-h-[120px] max-h-[260px] overflow-y-auto">
              {chatHistory.length === 0 ? (
                <div className="text-center py-6 space-y-2">
                  <Bot className="w-7 h-7 text-slate-600 mx-auto" />
                  <p className="text-xs text-slate-500">
                    Ask a conceptual question about this problem. The assistant will guide your thinking
                    — it will not solve the problem directly.
                  </p>
                </div>
              ) : (
                chatHistory.slice(-12).map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex items-start space-x-2 ${
                      msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                    }`}
                  >
                    <div
                      className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                        msg.role === 'user'
                          ? 'bg-sky-800'
                          : 'bg-indigo-800'
                      }`}
                    >
                      {msg.role === 'user' ? (
                        <User className="w-3 h-3 text-sky-200" />
                      ) : (
                        <Bot className="w-3 h-3 text-indigo-200" />
                      )}
                    </div>
                    <div
                      className={`max-w-[85%] rounded-lg px-3 py-2 text-xs leading-relaxed whitespace-pre-wrap ${
                        msg.role === 'user'
                          ? 'bg-sky-900/60 border border-sky-800/50 text-sky-100'
                          : 'bg-slate-800 border border-slate-700 text-slate-200'
                      }`}
                    >
                      {msg.content}
                    </div>
                  </div>
                ))
              )}
              {isLoading && (
                <div className="flex items-center space-x-2">
                  <div className="w-6 h-6 rounded-full bg-indigo-800 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-3 h-3 text-indigo-200" />
                  </div>
                  <div className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2">
                    <Loader2 className="w-3 h-3 animate-spin text-indigo-400" />
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Source + turn count */}
            {response && chatHistory.length > 0 && (
              <div className="flex items-center space-x-2">
                <SourceBadge source={response.source} />
                <span className="text-[10px] text-slate-600 font-mono">
                  {Math.floor(chatHistory.length / 2)}/6 turns
                </span>
              </div>
            )}

            {/* Input row */}
            <div className="flex items-end space-x-2">
              <textarea
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={handleChatKeyDown}
                placeholder="Ask a conceptual question… (Enter to send)"
                maxLength={2000}
                rows={2}
                className="flex-1 bg-slate-950 text-slate-200 text-xs rounded-lg border border-slate-700 p-2.5 resize-none focus:outline-none focus:border-indigo-600 font-sans placeholder-slate-600"
              />
              <button
                onClick={handleSendChat}
                disabled={isLoading || !chatInput.trim()}
                className="p-2.5 rounded-lg bg-indigo-700 hover:bg-indigo-600 disabled:opacity-40 disabled:cursor-not-allowed text-white transition"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </div>
            <p className="text-[10px] text-slate-600 text-right">
              {chatInput.length}/2000 · Shift+Enter for newline
            </p>
          </div>
        )}

        {/* ── Shared error / rate-limit states ── */}
        {errorMsg && (
          <div
            className={`rounded-lg p-3 border text-xs flex items-start space-x-2 ${
              rateLimited
                ? 'bg-amber-950/40 border-amber-800/60 text-amber-300'
                : 'bg-rose-950/40 border-rose-800/60 text-rose-300'
            }`}
          >
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* ── Advisory notice (always shown at bottom) ── */}
        {response?.advisory_notice && (
          <div className="mt-1 pt-3 border-t border-slate-800/60">
            <p className="text-[10px] text-slate-600 italic leading-relaxed">
              <ChevronRight className="w-2.5 h-2.5 inline mr-0.5 text-slate-700" />
              {response.advisory_notice}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

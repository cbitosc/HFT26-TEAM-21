/**
 * TypeScript types for Assessment Agent, Question Bank & Student Workspace (Modules 4, 5, 6).
 */

export interface TestCase {
  input_data: string;
  expected_output: string;
  is_hidden: boolean;
  explanation?: string;
}

export interface QuestionPublic {
  id: string;
  title: string;
  difficulty: 'easy' | 'medium' | 'hard';
  domain: string;
  topic: string;
  language: string;
  problem_statement: string;
  constraints?: string;
  starter_code: string;
  sample_input: string;
  sample_output: string;
  public_test_cases: TestCase[];
}

export interface CandidateSubmission {
  question_id: string;
  submitted_code: string;
}

export interface QuestionResult {
  question_id: string;
  title: string;
  difficulty: string;
  domain: string;
  passed_tests: number;
  total_tests: number;
  all_passed: boolean;
  feedback: string;
}

export interface AssessmentSessionResponse {
  session_id: string;
  user_id: string;
  tier: 'novice' | 'adept' | 'master';
  track: 'verified' | 'practice';
  status: 'active' | 'completed' | 'expired';
  domain: string;
  matched_skills: string[];
  questions: QuestionPublic[];
  ai_guidance?: string;
  created_at: string;
  completed_at?: string;
}

export interface AssessmentSummaryResponse {
  session_id: string;
  user_id: string;
  tier: 'novice' | 'adept' | 'master';
  track: 'verified' | 'practice';
  status: 'completed';
  score_percentage: number;
  total_questions: number;
  questions_passed: number;
  results: QuestionResult[];
  matched_skills: string[];
  demonstrated_skills?: string[];
  skill_gaps?: string[];
  created_at: string;
  completed_at?: string;
  verification_notice: string;
}

export interface AssessmentGenerateParams {
  tier: 'novice' | 'adept' | 'master';
  track: 'verified' | 'practice';
  domain_filter?: string;
  preferred_language?: string;
}

// ---------------------------------------------------------------------------
// Module 7: Code Execution Sandbox Types
// ---------------------------------------------------------------------------

export interface SampleRunRequest {
  question_id: string;
  submitted_code: string;
  custom_input?: string;
}

export interface SampleRunResponse {
  question_id: string;
  status: string; // 'accepted', 'wrong_answer', 'compilation_error', 'runtime_error', 'time_limit_exceeded', 'memory_limit_exceeded', 'sandbox_error', 'sandbox_unavailable'
  passed: boolean;
  stdout?: string | null;
  stderr?: string | null;
  compile_output?: string | null;
  execution_time_ms?: number | null;
  memory_kb?: number | null;
  exit_code?: number | null;
  expected_output?: string | null;
  actual_output?: string | null;
  error_message?: string | null;
  sandbox_provider: string;
}

// ---------------------------------------------------------------------------
// Module 8: CodeTrace Telemetry Types
// ---------------------------------------------------------------------------

export interface CodeTraceEventCreate {
  question_id: string;
  event_type: 'snapshot' | 'sample_run' | 'submission' | 'paste_cadence' | 'switch';
  code_snapshot: string;
  diff_summary?: Record<string, any>;
  metrics?: Record<string, any>;
}

export interface CodeTraceEvent {
  id: string;
  session_id: string;
  user_id: string;
  question_id: string;
  event_type: string;
  code_snapshot: string;
  diff_summary: {
    added_lines?: number;
    deleted_lines?: number;
    char_delta?: number;
    total_chars?: number;
    total_lines?: number;
    [key: string]: any;
  };
  metrics: {
    execution_time_ms?: number;
    sample_passed?: boolean;
    paste_length?: number;
    [key: string]: any;
  };
  created_at: string;
}

export interface CodeTraceTimelineResponse {
  session_id: string;
  total_events: number;
  total_revisions: number;
  sample_runs_count: number;
  events: CodeTraceEvent[];
  summary: {
    total_events: number;
    total_revisions: number;
    sample_runs_count: number;
    first_event_at?: string;
    last_event_at?: string;
  };
}

// ---------------------------------------------------------------------------
// Module 9: Guarded AI Coding Assistant Types
// ---------------------------------------------------------------------------

export interface AssistantChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AssistantHintRequest {
  question_id: string;
  current_code: string;
  hint_level: number; // 1, 2, or 3
}

export interface AssistantExplainErrorRequest {
  question_id: string;
  current_code: string;
  error_message: string;
}

export interface AssistantChatRequest {
  question_id: string;
  message: string;
  current_code: string;
  history?: AssistantChatMessage[];
}

export interface AssistantResponse {
  reply: string;
  hint_level?: number | null;
  mode: 'guarded' | 'practice';
  is_guarded: boolean;
  source: 'featherless' | 'fallback';
  advisory_notice: string;
}

// ---------------------------------------------------------------------------
// Module 10: Performance Analytics and Scoring Types
// ---------------------------------------------------------------------------

export interface TrendPoint {
  session_id: string;
  date: string;
  composite_score: number;
  test_score: number;
  raw_correctness_pct?: number;
  ai_efficiency_score: number;
  telemetry_status?: 'self_sufficient' | 'assisted' | 'unknown';
  tier: string;
  track: string;
  domain: string;
  questions_passed: number;
  total_questions: number;
}

export interface DomainPerformance {
  domain: string;
  sessions: number;
  questions_attempted: number;
  questions_passed: number;
  pass_rate: number;
}

export interface SkillMasteryItem {
  tier: string;
  difficulty: string;
  sessions: number;
  avg_composite_score: number;
  best_composite_score: number;
  total_questions: number;
  total_passed: number;
}

export interface HintUtilizationSummary {
  total_hint_requests: number;
  level_1_hints: number;
  level_2_hints: number;
  level_3_hints: number;
  sessions_with_hints: number;
  avg_hints_per_session: number;
  ai_efficiency_avg: number;
}

export interface AnalyticsResponse {
  user_id: string;
  generated_at: string;
  total_sessions: number;
  verified_sessions: number;
  practice_sessions: number;
  overall_avg_composite: number;
  best_composite_score: number;
  overall_test_pass_rate: number;
  practice_avg_composite?: number | null;
  trend: TrendPoint[];
  domain_performance: DomainPerformance[];
  skill_mastery: SkillMasteryItem[];
  hint_utilization: HintUtilizationSummary;
  scoring_formula_note: string;
}


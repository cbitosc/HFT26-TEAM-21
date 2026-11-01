/**
 * TypeScript types for Module 12: Recruiter Portal & Live Interviews
 */

export interface CandidateDiscoveryItem {
  candidate_id: string;
  full_name: string;
  college_name?: string | null;
  verified_skills: string[];
  verified_domains: string[];
  verified_avg_score: number;
  verified_sessions_count: number;
  portfolio_claims: string[];
  recruiter_discoverable: boolean;
}

export interface CandidateDetailProfileResponse {
  candidate_id: string;
  full_name: string;
  college_name?: string | null;
  verified_avg_composite: number;
  verified_test_pass_rate: number;
  verified_sessions_count: number;
  verified_skills: string[];
  domain_mastery: Array<{
    domain: string;
    sessions: number;
    questions_attempted: number;
    questions_passed: number;
    pass_rate: number;
  }>;
  tier_mastery: Array<{
    tier: string;
    difficulty: string;
    sessions: number;
    avg_composite_score: number;
    best_composite_score: number;
    total_questions: number;
    total_passed: number;
  }>;
  verified_history: Array<{
    session_id: string;
    date: string;
    domain: string;
    tier: string;
    composite_score: number;
    test_score: number;
    raw_correctness_pct: number;
  }>;
  portfolio_claims: Array<{
    claim: string;
    is_verified: boolean;
    source: string;
  }>;
  consent_status: boolean;
}

export interface InterviewSessionCreate {
  candidate_id: string;
  title: string;
  scheduled_at?: string;
  task_description?: string;
  initial_code?: string;
  language?: string;
}

export interface InterviewRespondRequest {
  action: 'accept' | 'decline';
}

export interface InterviewSessionResponse {
  id: string;
  recruiter_id: string;
  candidate_id: string;
  title: string;
  scheduled_at: string;
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
  candidate_accepted?: boolean | null;
  task_description: string;
  current_code: string;
  language: string;
  version: number;
  last_edited_by?: string | null;
  requested_changes: Array<{
    id: string;
    requested_change: string;
    instructions?: string;
    requested_at: string;
    code_snapshot_at_request: string;
  }>;
  feedback?: string | null;
  outcome?: 'passed' | 'needs_review' | 'rejected' | null;
  created_at: string;
  updated_at: string;
}

/**
 * TypeScript types for Module 11: College Task Management
 */

export interface CollegeTaskTestCase {
  input: string;
  expected_output: string;
  is_hidden?: boolean;
}

export interface CollegeTaskCreate {
  title: string;
  description: string;
  domain: string;
  difficulty: string;
  allowed_languages?: string[];
  deadline?: string;
  duration_minutes?: number;
  instructions?: string;
  starter_code?: string;
  test_cases?: CollegeTaskTestCase[];
  status?: 'draft' | 'published' | 'closed' | 'archived';
  assigned_student_ids?: string[];
  allow_late_submissions?: boolean;
}

export interface CollegeTaskResponse {
  id: string;
  college_id: string;
  creator_id: string;
  title: string;
  description: string;
  domain: string;
  difficulty: string;
  allowed_languages: string[];
  deadline?: string;
  duration_minutes: number;
  instructions?: string;
  starter_code: string;
  test_cases: CollegeTaskTestCase[];
  status: 'draft' | 'published' | 'closed' | 'archived';
  assigned_student_ids: string[];
  allow_late_submissions: boolean;
  created_at: string;
  updated_at: string;
}

export interface CollegeTaskSubmissionCreate {
  submitted_code: string;
  language?: string;
}

export interface CollegeTaskSubmissionResponse {
  id: string;
  task_id: string;
  student_id: string;
  college_id: string;
  submitted_code: string;
  language: string;
  status: string;
  score_percentage: number;
  tests_passed: number;
  total_tests: number;
  results: Array<{
    test_case_index: number;
    passed: boolean;
    status: string;
    execution_time_ms?: number | null;
    expected_output?: string;
    actual_output?: string;
  }>;
  submitted_at: string;
}

export interface CollegeTaskAnalyticsResponse {
  task_id: string;
  title: string;
  status: string;
  deadline?: string;
  total_assigned: number;
  total_started: number;
  total_completed: number;
  total_pending: number;
  avg_score: number;
  pass_rate: number;
}

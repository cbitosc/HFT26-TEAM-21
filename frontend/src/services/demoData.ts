/**
 * Demo Data Provider — Isolated, synthetic data for SkillProof AI Guest Mode.
 *
 * Requirements:
 * - All demo data must be clearly labeled as sample/demo data.
 * - Role-specific mock data for Student, College Administrator, and Recruiter.
 * - Completely isolated from production database records.
 * - Safe for interactive experimentation without triggering real mutations.
 */

import { PortfolioResponse } from '../types/portfolio';
import { CollegeTaskResponse, CollegeTaskAnalyticsResponse } from '../types/college';
import { CandidateDiscoveryItem, CandidateDetailProfileResponse, InterviewSessionResponse } from '../types/recruiter';
import { AnalyticsResponse } from '../types/assessment';

// ---------------------------------------------------------------------------
// Student Demo Data
// ---------------------------------------------------------------------------

export const DEMO_STUDENT_PORTFOLIO: PortfolioResponse = {
  id: 'demo-portfolio-guest-001',
  user_id: 'demo-student-guest',
  confirmed: true,
  confirmed_at: new Date().toISOString(),
  skills_status: 'verified',
  data: {
    projects: [
      {
        name: 'Algorithmic Order Matcher (Sample Project)',
        description:
          'High-throughput matching engine implementing price-time priority order book queuing, cancellation handling, and audit trails.',
        technologies: ['Python', 'FastAPI', 'Data Structures'],
      },
      {
        name: 'Distributed Log Aggregator (Sample Project)',
        description:
          'Lightweight distributed log streaming pipeline with cluster worker heartbeat monitoring and backpressure buffering.',
        technologies: ['TypeScript', 'Node.js', 'Docker'],
      },
    ],
    skills: {
      programming_languages: ['Python', 'TypeScript', 'SQL'],
      frameworks_and_tools: ['React', 'FastAPI', 'Docker', 'PostgreSQL'],
    },
    domains: ['Algorithms & Problem Solving', 'Full-Stack Web Architecture'],
    dsa_topics: ['Dynamic Programming', 'Graph Theory', 'Trees & BSTs'],
  },
  created_at: new Date(Date.now() - 7 * 86400000).toISOString(),
  updated_at: new Date().toISOString(),
};

export const DEMO_STUDENT_TASKS: CollegeTaskResponse[] = [
  {
    id: 'demo-task-001',
    college_id: 'demo-college-001',
    creator_id: 'admin-001',
    title: 'CS-301: Balanced Binary Tree Validation (Sample Task)',
    description:
      'Implement a validation function to verify whether an arbitrary binary search tree satisfies strict height-balancing invariants (AVL condition).',
    domain: 'Algorithms & DSA',
    difficulty: 'medium',
    allowed_languages: ['python'],
    duration_minutes: 60,
    instructions:
      '1. Read the BST root node.\n2. Calculate subtree heights recursively.\n3. Return true if height difference <= 1 and subtrees are balanced.',
    starter_code:
      '# Sample Student Task\ndef is_balanced_bst(root):\n    # Write your solution here\n    pass\n',
    test_cases: [
      { input: '[3, 9, 20, null, null, 15, 7]', expected_output: 'true' },
      { input: '[1, 2, 2, 3, 3, null, null, 4, 4]', expected_output: 'false' },
    ],
    status: 'published',
    assigned_student_ids: ['demo-student-guest'],
    allow_late_submissions: false,
    created_at: new Date(Date.now() - 2 * 86400000).toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'demo-task-002',
    college_id: 'demo-college-001',
    creator_id: 'admin-001',
    title: 'CS-402: Dijkstra Shortest Path Router (Sample Task)',
    description:
      'Build an optimal graph router utilizing a min-heap priority queue to determine shortest distance vectors in weighted transit networks.',
    domain: 'Algorithms & DSA',
    difficulty: 'hard',
    allowed_languages: ['python'],
    duration_minutes: 90,
    instructions: 'Implement dijkstra(graph, start_node) returning shortest distance map.',
    starter_code: '# Sample Task\ndef dijkstra(graph, start):\n    pass\n',
    test_cases: [
      {
        input: '{"A": [["B", 1], ["C", 4]], "B": [["C", 2]]}, start="A"',
        expected_output: '{"A": 0, "B": 1, "C": 3}',
      },
    ],
    status: 'published',
    assigned_student_ids: ['demo-student-guest'],
    allow_late_submissions: true,
    created_at: new Date(Date.now() - 5 * 86400000).toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export const DEMO_STUDENT_INTERVIEWS: InterviewSessionResponse[] = [
  {
    id: 'demo-interview-001',
    recruiter_id: 'recruiter-demo-001',
    candidate_id: 'demo-student-guest',
    title: 'Frontend & Systems Engineering Screening (Sample Interview)',
    task_description:
      'Live collaborative session: Design and refactor a debounce search pipeline with cache memoization and unit tests.',
    scheduled_at: new Date(Date.now() + 86400000).toISOString(),
    status: 'scheduled',
    current_code:
      '# Welcome to your live coding interview!\n# Task: Refactor debounce search\n\ndef search_query(query: str):\n    return []\n',
    language: 'python',
    version: 1,
    requested_changes: [],
    candidate_accepted: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export const DEMO_STUDENT_ANALYTICS: AnalyticsResponse = {
  user_id: 'demo-student-guest',
  generated_at: new Date().toISOString(),
  total_sessions: 4,
  verified_sessions: 3,
  practice_sessions: 1,
  overall_avg_composite: 86.8,
  best_composite_score: 94.0,
  overall_test_pass_rate: 88.9,
  practice_avg_composite: 82.5,
  trend: [
    {
      session_id: 'session-demo-1',
      date: new Date(Date.now() - 6 * 86400000).toISOString().split('T')[0],
      composite_score: 82.0,
      test_score: 80.0,
      raw_correctness_pct: 80.0,
      ai_efficiency_score: 85.0,
      telemetry_status: 'assisted',
      tier: 'novice',
      track: 'verified',
      domain: 'Algorithms & Problem Solving',
      questions_passed: 3,
      total_questions: 3,
    },
    {
      session_id: 'session-demo-2',
      date: new Date(Date.now() - 4 * 86400000).toISOString().split('T')[0],
      composite_score: 86.5,
      test_score: 85.0,
      raw_correctness_pct: 85.0,
      ai_efficiency_score: 90.0,
      telemetry_status: 'self_sufficient',
      tier: 'adept',
      track: 'verified',
      domain: 'Data Structures & Algorithms',
      questions_passed: 3,
      total_questions: 3,
    },
    {
      session_id: 'session-demo-3',
      date: new Date(Date.now() - 2 * 86400000).toISOString().split('T')[0],
      composite_score: 92.0,
      test_score: 90.0,
      raw_correctness_pct: 90.0,
      ai_efficiency_score: 95.0,
      telemetry_status: 'self_sufficient',
      tier: 'master',
      track: 'verified',
      domain: 'Systems & Distributed Computing',
      questions_passed: 3,
      total_questions: 3,
    },
  ],
  domain_performance: [
    {
      domain: 'Data Structures & Algorithms',
      sessions: 2,
      questions_attempted: 6,
      questions_passed: 6,
      pass_rate: 100.0,
    },
    {
      domain: 'Systems & Distributed Computing',
      sessions: 1,
      questions_attempted: 3,
      questions_passed: 3,
      pass_rate: 100.0,
    },
    {
      domain: 'Algorithms & Problem Solving',
      sessions: 1,
      questions_attempted: 3,
      questions_passed: 2,
      pass_rate: 66.7,
    },
  ],
  skill_mastery: [
    {
      tier: 'novice',
      difficulty: 'easy',
      sessions: 1,
      avg_composite_score: 82.0,
      best_composite_score: 82.0,
      total_questions: 3,
      total_passed: 3,
    },
    {
      tier: 'adept',
      difficulty: 'medium',
      sessions: 2,
      avg_composite_score: 86.5,
      best_composite_score: 89.0,
      total_questions: 6,
      total_passed: 5,
    },
    {
      tier: 'master',
      difficulty: 'hard',
      sessions: 1,
      avg_composite_score: 92.0,
      best_composite_score: 92.0,
      total_questions: 3,
      total_passed: 3,
    },
  ],
  hint_utilization: {
    total_hint_requests: 2,
    level_1_hints: 2,
    level_2_hints: 0,
    level_3_hints: 0,
    sessions_with_hints: 1,
    avg_hints_per_session: 0.5,
    ai_efficiency_avg: 90.0,
  },
  scoring_formula_note:
    'Sample Guest Analytics — Composite score reflects deterministic test correctness, problem-solving speed, and CodeTrace hint telemetry.',
};

// ---------------------------------------------------------------------------
// College Administrator Demo Data
// ---------------------------------------------------------------------------

export const DEMO_COLLEGE_TASKS: CollegeTaskResponse[] = [
  {
    id: 'college-task-demo-1',
    college_id: 'demo-college-001',
    creator_id: 'admin-001',
    title: 'Midterm Lab: LRU Cache Implementation (Sample Task)',
    description:
      'Construct a Least Recently Used (LRU) Cache data structure with O(1) get and put time complexity utilizing doubly-linked nodes and a hash table.',
    domain: 'Data Structures & Algorithms',
    difficulty: 'medium',
    allowed_languages: ['python'],
    duration_minutes: 60,
    instructions: 'Implement LRUCache with capacity, get(key), and put(key, value).',
    starter_code:
      'class LRUCache:\n    def __init__(self, capacity: int):\n        pass\n    def get(self, key: int) -> int:\n        return -1\n    def put(self, key: int, value: int) -> None:\n        pass\n',
    test_cases: [
      { input: 'capacity=2, put(1,1), put(2,2), get(1)', expected_output: '1' },
      { input: 'put(3,3), get(2)', expected_output: '-1' },
    ],
    status: 'published',
    assigned_student_ids: ['demo-student-guest'],
    allow_late_submissions: false,
    created_at: new Date(Date.now() - 3 * 86400000).toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'college-task-demo-2',
    college_id: 'demo-college-001',
    creator_id: 'admin-001',
    title: 'Assignment 4: Asynchronous Task Rate Limiter (Sample Task)',
    description:
      'Implement a Token Bucket algorithm in Python for rate limiting inbound API requests within a sliding execution window.',
    domain: 'Software Engineering',
    difficulty: 'hard',
    allowed_languages: ['python'],
    duration_minutes: 90,
    instructions: 'Implement acquire() and refill() logic with lock safety.',
    starter_code:
      'class TokenBucket:\n    def __init__(self, capacity: int, rate: float):\n        pass\n    def allow_request(self) -> bool:\n        return True\n',
    test_cases: [
      { input: 'capacity=5, rate=1, 5 consecutive requests', expected_output: 'all true' },
      { input: '6th request without delay', expected_output: 'false' },
    ],
    status: 'published',
    assigned_student_ids: ['demo-student-guest'],
    allow_late_submissions: true,
    created_at: new Date(Date.now() - 6 * 86400000).toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'college-task-demo-3',
    college_id: 'demo-college-001',
    creator_id: 'admin-001',
    title: 'Practice Challenge: Subarray Sum Equals K (Sample Task)',
    description:
      'Find the total number of continuous subarrays whose sum equals a specified integer k using prefix-sum hash indexing.',
    domain: 'Data Structures & Algorithms',
    difficulty: 'medium',
    allowed_languages: ['python'],
    duration_minutes: 45,
    instructions: 'Implement subarray_sum(nums, k) in O(n) time.',
    starter_code: 'def subarray_sum(nums: list[int], k: int) -> int:\n    pass\n',
    test_cases: [
      { input: 'nums=[1,1,1], k=2', expected_output: '2' },
      { input: 'nums=[1,2,3], k=3', expected_output: '2' },
    ],
    status: 'draft',
    assigned_student_ids: [],
    allow_late_submissions: false,
    created_at: new Date(Date.now() - 1 * 86400000).toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export const DEMO_COLLEGE_ANALYTICS: CollegeTaskAnalyticsResponse = {
  task_id: 'college-task-demo-1',
  title: 'Midterm Lab: LRU Cache Implementation (Sample Task)',
  status: 'published',
  total_assigned: 45,
  total_started: 42,
  total_completed: 40,
  total_pending: 3,
  avg_score: 83.4,
  pass_rate: 90.5,
};

// ---------------------------------------------------------------------------
// Recruiter Demo Data
// ---------------------------------------------------------------------------

export const DEMO_RECRUITER_CANDIDATES: CandidateDiscoveryItem[] = [
  {
    candidate_id: 'sample-cand-001',
    full_name: 'Alex Chen (Sample Candidate)',
    college_name: 'Institute of Technology - CS Dept',
    verified_skills: ['Python', 'FastAPI', 'React', 'Docker', 'PostgreSQL'],
    verified_domains: ['Algorithms & Problem Solving', 'Full-Stack Architecture'],
    verified_avg_score: 94.5,
    verified_sessions_count: 4,
    portfolio_claims: ['Algorithmic Order Matcher', 'Distributed Log Aggregator'],
    recruiter_discoverable: true,
  },
  {
    candidate_id: 'sample-cand-002',
    full_name: 'Priya Sharma (Sample Candidate)',
    college_name: 'National University of Engineering',
    verified_skills: ['C++', 'Python', 'Dynamic Programming', 'Graph Theory'],
    verified_domains: ['Data Structures & Algorithms'],
    verified_avg_score: 91.0,
    verified_sessions_count: 5,
    portfolio_claims: ['Graph Transit Optimizer', 'Memory Safe Allocator'],
    recruiter_discoverable: true,
  },
  {
    candidate_id: 'sample-cand-003',
    full_name: 'Marcus Vance (Sample Candidate)',
    college_name: 'Metropolitan Polytechnic Institute',
    verified_skills: ['Go', 'Kubernetes', 'Redis', 'Message Queues'],
    verified_domains: ['Systems & Distributed Computing'],
    verified_avg_score: 88.0,
    verified_sessions_count: 3,
    portfolio_claims: ['Microservices Orchestrator'],
    recruiter_discoverable: true,
  },
];

export const DEMO_CANDIDATE_DOSSIER: CandidateDetailProfileResponse = {
  candidate_id: 'sample-cand-001',
  full_name: 'Alex Chen (Sample Candidate)',
  college_name: 'Institute of Technology - CS Dept',
  verified_avg_composite: 94.5,
  verified_test_pass_rate: 96.0,
  verified_sessions_count: 4,
  verified_skills: ['Python', 'FastAPI', 'React', 'Docker', 'PostgreSQL'],
  domain_mastery: [
    {
      domain: 'Systems & Distributed Computing',
      sessions: 2,
      questions_attempted: 6,
      questions_passed: 6,
      pass_rate: 100.0,
    },
    {
      domain: 'Data Structures & Algorithms',
      sessions: 2,
      questions_attempted: 6,
      questions_passed: 5,
      pass_rate: 83.3,
    },
  ],
  tier_mastery: [
    {
      tier: 'master',
      difficulty: 'hard',
      sessions: 2,
      avg_composite_score: 95.0,
      best_composite_score: 96.0,
      total_questions: 6,
      total_passed: 6,
    },
  ],
  verified_history: [
    {
      session_id: 'sample-session-101',
      date: new Date(Date.now() - 3 * 86400000).toISOString().split('T')[0],
      domain: 'Systems & Distributed Computing',
      tier: 'master',
      composite_score: 95.0,
      test_score: 95.0,
      raw_correctness_pct: 100.0,
    },
  ],
  portfolio_claims: [
    {
      claim: 'Algorithmic Order Matcher (Sample Project)',
      is_verified: true,
      source: 'GitHub Repository',
    },
    {
      claim: 'Distributed Log Aggregator (Sample Project)',
      is_verified: true,
      source: 'GitHub Repository',
    },
  ],
  consent_status: true,
};

export const DEMO_RECRUITER_INTERVIEWS: InterviewSessionResponse[] = [
  {
    id: 'demo-interview-rec-1',
    recruiter_id: 'guest-recruiter-session',
    candidate_id: 'sample-cand-001',
    title: 'Pair-Coding Session: System Debounce & Memory Cache (Sample Interview)',
    task_description:
      'Evaluate candidate code architecture, dynamic requirement changes, and modular testing.',
    scheduled_at: new Date(Date.now() + 4 * 3600000).toISOString(),
    status: 'scheduled',
    current_code:
      '# Live Pair-Coding Workspace (Sample Interview)\n# Candidate: Alex Chen\n\ndef cache_decorator(ttl_seconds: int):\n    def decorator(func):\n        # Refactor with TTL expiry\n        return func\n    return decorator\n',
    language: 'python',
    version: 1,
    requested_changes: [],
    candidate_accepted: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

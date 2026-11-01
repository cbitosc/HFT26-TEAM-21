-- ==============================================================================
-- SkillProof AI — Migration 005: College Task Management (Module 11)
-- ==============================================================================

-- 1. College Tasks table
create table if not exists public.college_tasks (
    id uuid primary key default gen_random_uuid(),
    college_id uuid not null,
    creator_id uuid not null references public.profiles(id) on delete cascade,
    title text not null check (char_length(trim(title)) >= 3 and char_length(title) <= 200),
    description text not null,
    domain text not null,
    difficulty text not null check (difficulty in ('easy', 'medium', 'hard', 'novice', 'adept', 'master')),
    allowed_languages text[] not null default array['python'],
    deadline timestamptz,
    duration_minutes integer not null default 60 check (duration_minutes > 0 and duration_minutes <= 1440),
    instructions text,
    starter_code text not null default '# Write your solution here\n',
    test_cases jsonb not null default '[]'::jsonb,
    status text not null default 'draft' check (status in ('draft', 'published', 'closed', 'archived')),
    assigned_student_ids uuid[] default array[]::uuid[],
    allow_late_submissions boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- 2. College Task Submissions table
create table if not exists public.college_task_submissions (
    id uuid primary key default gen_random_uuid(),
    task_id uuid not null references public.college_tasks(id) on delete cascade,
    student_id uuid not null references public.profiles(id) on delete cascade,
    college_id uuid not null,
    submitted_code text not null,
    language text not null default 'python',
    status text not null default 'submitted' check (status in ('draft', 'submitted', 'graded')),
    score_percentage float not null default 0.0 check (score_percentage >= 0.0 and score_percentage <= 100.0),
    tests_passed integer not null default 0,
    total_tests integer not null default 0,
    results jsonb not null default '[]'::jsonb,
    submitted_at timestamptz not null default now()
);

-- 3. Indexes for high performance queries
create index if not exists idx_college_tasks_college_status on public.college_tasks (college_id, status);
create index if not exists idx_college_tasks_deadline on public.college_tasks (deadline);
create index if not exists idx_task_submissions_task_student on public.college_task_submissions (task_id, student_id);
create index if not exists idx_task_submissions_college on public.college_task_submissions (college_id);

-- 4. Enable Row Level Security (RLS)
alter table public.college_tasks enable row level security;
alter table public.college_task_submissions enable row level security;

-- 5. RLS Policies: college_tasks
-- College Admins can view and manage tasks for their own college
create policy "College admins manage their college tasks"
    on public.college_tasks
    for all
    to authenticated
    using (
        exists (
            select 1 from public.profiles
            where id = auth.uid()
              and role = 'college_admin'
              and account_status = 'active'
              and college_id = public.college_tasks.college_id
        )
    )
    with check (
        exists (
            select 1 from public.profiles
            where id = auth.uid()
              and role = 'college_admin'
              and account_status = 'active'
              and college_id = public.college_tasks.college_id
        )
    );

-- Students can read published/closed tasks assigned to them or their college
create policy "Students view assigned college tasks"
    on public.college_tasks
    for select
    to authenticated
    using (
        exists (
            select 1 from public.profiles
            where id = auth.uid()
              and role = 'student'
              and account_status = 'active'
              and college_id = public.college_tasks.college_id
              and public.college_tasks.status in ('published', 'closed')
              and (
                  public.college_tasks.assigned_student_ids is null
                  or cardinality(public.college_tasks.assigned_student_ids) = 0
                  or auth.uid() = any(public.college_tasks.assigned_student_ids)
              )
        )
    );

-- 6. RLS Policies: college_task_submissions
-- Note: Submissions use separate SELECT and INSERT policies for students.
-- Direct UPDATE and DELETE by students are strictly denied by RLS to preserve deterministic grading.

-- Students can view ONLY their own submissions
create policy "Students view own task submissions"
    on public.college_task_submissions
    for select
    to authenticated
    using (
        student_id = auth.uid()
        and exists (
            select 1 from public.profiles
            where id = auth.uid()
              and role = 'student'
              and account_status = 'active'
        )
    );

-- Students can insert submissions ONLY for eligible published tasks with untampered grading fields
create policy "Students insert own task submissions"
    on public.college_task_submissions
    for insert
    to authenticated
    with check (
        -- Identity validation: submission belongs to authenticated student
        student_id = auth.uid()
        -- Profile validation: active student whose profile college matches submission college
        and exists (
            select 1 from public.profiles
            where id = auth.uid()
              and role = 'student'
              and account_status = 'active'
              and college_id = public.college_task_submissions.college_id
        )
        -- Anti-tampering check: students cannot self-assign scores or mark submission as graded
        and status in ('draft', 'submitted')
        and score_percentage = 0.0
        and tests_passed = 0
        and total_tests = 0
        and (results is null or results = '[]'::jsonb)
        -- Task eligibility and relationship check
        and exists (
            select 1 from public.college_tasks
            where id = public.college_task_submissions.task_id
              and college_id = public.college_task_submissions.college_id
              and status = 'published'
              -- Deadline check: deadline not passed or late submissions explicitly allowed
              and (
                  deadline is null
                  or deadline > now()
                  or allow_late_submissions = true
              )
              -- Assignment check: task open to whole college or explicitly assigned to this student
              and (
                  assigned_student_ids is null
                  or cardinality(assigned_student_ids) = 0
                  or auth.uid() = any(assigned_student_ids)
              )
        )
    );

-- College Admins can view submissions for their college tasks
create policy "College admins view college submissions"
    on public.college_task_submissions
    for select
    to authenticated
    using (
        exists (
            select 1 from public.profiles
            where id = auth.uid()
              and role = 'college_admin'
              and account_status = 'active'
              and college_id = public.college_task_submissions.college_id
        )
    );

-- College Admins can update submissions for their college tasks (for grading / status notes)
create policy "College admins update college submissions"
    on public.college_task_submissions
    for update
    to authenticated
    using (
        exists (
            select 1 from public.profiles
            where id = auth.uid()
              and role = 'college_admin'
              and account_status = 'active'
              and college_id = public.college_task_submissions.college_id
        )
    )
    with check (
        exists (
            select 1 from public.profiles
            where id = auth.uid()
              and role = 'college_admin'
              and account_status = 'active'
              and college_id = public.college_task_submissions.college_id
        )
    );

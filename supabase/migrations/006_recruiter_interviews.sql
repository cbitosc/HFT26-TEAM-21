-- ==============================================================================
-- SkillProof AI — Migration 006: Recruiter Portal & Live Interviews (Module 12)
-- ==============================================================================

-- 1. Add recruiter discoverability consent column to profiles
alter table public.profiles
    add column if not exists recruiter_discoverable boolean not null default false;

-- 2. Interview Sessions table
create table if not exists public.interview_sessions (
    id uuid primary key default gen_random_uuid(),
    recruiter_id uuid not null references public.profiles(id) on delete cascade,
    candidate_id uuid not null references public.profiles(id) on delete cascade,
    title text not null check (char_length(trim(title)) >= 3 and char_length(title) <= 200),
    scheduled_at timestamptz not null default now(),
    status text not null default 'scheduled' check (status in ('scheduled', 'in_progress', 'completed', 'cancelled')),
    task_description text not null default '',
    current_code text not null default '# Live Interview Coding Workspace\n',
    language text not null default 'python',
    requested_changes jsonb not null default '[]'::jsonb,
    feedback text,
    outcome text check (outcome is null or outcome in ('passed', 'needs_review', 'rejected')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- 3. Indexes for high-performance queries and discovery filtering
create index if not exists idx_interviews_recruiter on public.interview_sessions (recruiter_id, status);
create index if not exists idx_interviews_candidate on public.interview_sessions (candidate_id, status);
create index if not exists idx_profiles_discoverable on public.profiles (recruiter_discoverable, role, account_status);

-- 4. Enable Row Level Security (RLS)
alter table public.interview_sessions enable row level security;

-- 5. RLS Policies: interview_sessions

-- (A) Recruiter SELECT: Approved recruiters can view only interviews they scheduled
create policy "Recruiters view own interview sessions"
    on public.interview_sessions
    for select
    to authenticated
    using (
        recruiter_id = auth.uid()
        and exists (
            select 1 from public.profiles
            where id = auth.uid()
              and role = 'recruiter'
              and account_status = 'active'
        )
    );

-- (B) Recruiter INSERT: Only approved, active recruiters can schedule interviews,
-- and ONLY with candidates who have granted discoverability/interview consent
create policy "Approved recruiters create interview sessions"
    on public.interview_sessions
    for insert
    to authenticated
    with check (
        recruiter_id = auth.uid()
        and exists (
            select 1 from public.profiles
            where id = auth.uid()
              and role = 'recruiter'
              and account_status = 'active'
        )
        and exists (
            select 1 from public.profiles candidate_profile
            where candidate_profile.id = public.interview_sessions.candidate_id
              and candidate_profile.role = 'student'
              and candidate_profile.account_status = 'active'
              and candidate_profile.recruiter_discoverable = true
        )
    );

-- (C) Recruiter UPDATE: Approved recruiters can update administrative and evaluation fields
create policy "Approved recruiters update own interview sessions"
    on public.interview_sessions
    for update
    to authenticated
    using (
        recruiter_id = auth.uid()
        and exists (
            select 1 from public.profiles
            where id = auth.uid()
              and role = 'recruiter'
              and account_status = 'active'
        )
    )
    with check (
        recruiter_id = auth.uid()
        and exists (
            select 1 from public.profiles
            where id = auth.uid()
              and role = 'recruiter'
              and account_status = 'active'
        )
    );

-- (D) Recruiter DELETE: Approved recruiters can remove sessions they own
create policy "Approved recruiters delete own interview sessions"
    on public.interview_sessions
    for delete
    to authenticated
    using (
        recruiter_id = auth.uid()
        and exists (
            select 1 from public.profiles
            where id = auth.uid()
              and role = 'recruiter'
              and account_status = 'active'
        )
    );

-- (E) Candidate SELECT: Invited candidates can only view their own interview sessions
create policy "Candidates view invited interview sessions"
    on public.interview_sessions
    for select
    to authenticated
    using (
        candidate_id = auth.uid()
        and exists (
            select 1 from public.profiles
            where id = auth.uid()
              and role = 'student'
              and account_status = 'active'
        )
    );

-- (F) Candidate UPDATE: Invited candidates may update active interview sessions,
-- restricted at row level to active states (trigger enforces column restrictions)
create policy "Candidates update code in invited interview sessions"
    on public.interview_sessions
    for update
    to authenticated
    using (
        candidate_id = auth.uid()
        and status in ('scheduled', 'in_progress')
        and exists (
            select 1 from public.profiles
            where id = auth.uid()
              and role = 'student'
              and account_status = 'active'
        )
    )
    with check (
        candidate_id = auth.uid()
        and status in ('scheduled', 'in_progress')
        and exists (
            select 1 from public.profiles
            where id = auth.uid()
              and role = 'student'
              and account_status = 'active'
        )
    );

-- 6. Trigger: Candidate Column Protection
-- RLS restricts rows; this trigger strictly prevents candidates from modifying
-- administrative, scheduling, or evaluation fields (outcome, feedback, status, recruiter_id, candidate_id, title, scheduled_at).
create or replace function public.enforce_candidate_interview_update_restrictions()
returns trigger
language plpgsql
security definer
as $$
declare
    current_auth_uid uuid;
begin
    begin
        current_auth_uid := auth.uid();
    exception when others then
        current_auth_uid := null;
    end;

    -- If the updating user is the invited candidate
    if current_auth_uid is not null and current_auth_uid = old.candidate_id then
        if new.id <> old.id
           or new.recruiter_id <> old.recruiter_id
           or new.candidate_id <> old.candidate_id
           or new.title <> old.title
           or new.scheduled_at <> old.scheduled_at
           or new.status <> old.status
           or new.requested_changes is distinct from old.requested_changes
           or new.feedback is distinct from old.feedback
           or new.outcome is distinct from old.outcome
           or new.created_at <> old.created_at then
            raise exception 'Candidate update forbidden: candidates may only update live coding workspace fields (current_code, language, updated_at).';
        end if;
    end if;
    return new;
end;
$$;

drop trigger if exists trg_candidate_interview_update on public.interview_sessions;
create trigger trg_candidate_interview_update
    before update on public.interview_sessions
    for each row
    execute function public.enforce_candidate_interview_update_restrictions();

-- 7. Secure Candidate Code Synchronization RPC
-- Provides a clean, column-restricted procedure for candidates to sync workspace code.
create or replace function public.sync_candidate_interview_code(
    p_session_id uuid,
    p_code text,
    p_language text default 'python'
)
returns public.interview_sessions
language plpgsql
security definer
as $$
declare
    v_session public.interview_sessions;
    v_caller_id uuid;
begin
    begin
        v_caller_id := auth.uid();
    exception when others then
        v_caller_id := null;
    end;

    if v_caller_id is null then
        raise exception 'Authentication required.';
    end if;

    select * into v_session
    from public.interview_sessions
    where id = p_session_id
      and candidate_id = v_caller_id
      and status in ('scheduled', 'in_progress');

    if not found then
        raise exception 'Interview session not found or candidate unauthorized.';
    end if;

    update public.interview_sessions
    set current_code = p_code,
        language = coalesce(p_language, 'python'),
        status = 'in_progress',
        updated_at = now()
    where id = p_session_id
    returning * into v_session;

    return v_session;
end;
$$;

grant execute on function public.sync_candidate_interview_code(uuid, text, text) to authenticated;

-- 8. Recruiter Discovery Policy on public.profiles
-- Allows approved, active recruiters to discover active students who granted explicit consent.
drop policy if exists "Recruiters view discoverable candidates" on public.profiles;
create policy "Recruiters view discoverable candidates"
    on public.profiles
    for select
    to authenticated
    using (
        recruiter_discoverable = true
        and role = 'student'
        and account_status = 'active'
        and exists (
            select 1 from public.profiles recruiter_profile
            where recruiter_profile.id = auth.uid()
              and recruiter_profile.role = 'recruiter'
              and recruiter_profile.account_status = 'active'
        )
    );

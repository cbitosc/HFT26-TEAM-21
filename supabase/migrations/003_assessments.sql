-- =============================================================================
-- SkillProof AI — Database Schema: Question Bank & Assessments (Modules 4, 5, 6)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Verified Question Bank Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.questions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    difficulty TEXT NOT NULL CHECK (difficulty IN ('easy', 'medium', 'hard')),
    domain TEXT NOT NULL,
    topic TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'python',
    problem_statement TEXT NOT NULL,
    constraints TEXT,
    starter_code TEXT NOT NULL,
    sample_input TEXT NOT NULL,
    sample_output TEXT NOT NULL,
    reference_solution TEXT NOT NULL,
    test_cases JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_verified BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON public.questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_questions_domain ON public.questions(domain);
CREATE INDEX IF NOT EXISTS idx_questions_topic ON public.questions(topic);

-- -----------------------------------------------------------------------------
-- 2. Assessment Sessions Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.assessment_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    tier TEXT NOT NULL CHECK (tier IN ('novice', 'adept', 'master')),
    track TEXT NOT NULL CHECK (track IN ('verified', 'practice')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'expired')),
    domain TEXT NOT NULL,
    matched_skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    question_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    score_percentage NUMERIC(5, 2),
    results JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_assessment_sessions_user ON public.assessment_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_assessment_sessions_track ON public.assessment_sessions(track);
CREATE INDEX IF NOT EXISTS idx_assessment_sessions_status ON public.assessment_sessions(status);

-- -----------------------------------------------------------------------------
-- Least-Privilege Grants and RLS Policies
-- -----------------------------------------------------------------------------
REVOKE ALL ON public.questions FROM PUBLIC, anon, authenticated;
REVOKE ALL ON public.assessment_sessions FROM PUBLIC, anon, authenticated;

-- Candidates can read public question statements (reference solutions shielded via view/API)
GRANT SELECT (id, title, difficulty, domain, topic, language, problem_statement, constraints, starter_code, sample_input, sample_output, is_verified)
    ON public.questions TO authenticated;

-- Candidates manage their own assessment sessions
GRANT SELECT, INSERT, UPDATE ON public.assessment_sessions TO authenticated;

-- Service role has full administrative access
GRANT ALL ON public.questions TO service_role;
GRANT ALL ON public.assessment_sessions TO service_role;

ALTER TABLE public.questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assessment_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "questions_select_all" ON public.questions
    FOR SELECT USING (true);

CREATE POLICY "assessment_sessions_select_own" ON public.assessment_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "assessment_sessions_insert_own" ON public.assessment_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "assessment_sessions_update_own" ON public.assessment_sessions
    FOR UPDATE USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

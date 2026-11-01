-- =============================================================================
-- SkillProof AI — Database Schema: Student Portfolios (Module 3)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.profiles(id) ON DELETE CASCADE,
    portfolio_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    confirmed BOOLEAN NOT NULL DEFAULT false,
    confirmed_at TIMESTAMPTZ,
    skills_status TEXT NOT NULL DEFAULT 'unverified' CHECK (skills_status IN ('unverified', 'partially_verified', 'verified')),
    raw_filename TEXT,
    file_type TEXT CHECK (file_type IN ('pdf', 'json', 'manual')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON public.portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolios_confirmed ON public.portfolios(confirmed);

-- -----------------------------------------------------------------------------
-- Least-Privilege Grants and Revocations
-- -----------------------------------------------------------------------------
REVOKE ALL ON public.portfolios FROM PUBLIC, anon, authenticated;

-- Authenticated students can view and manage their own portfolio
GRANT SELECT, INSERT, UPDATE ON public.portfolios TO authenticated;

-- service_role has administrative access
GRANT ALL ON public.portfolios TO service_role;

-- -----------------------------------------------------------------------------
-- Row Level Security (RLS) Policies
-- -----------------------------------------------------------------------------
ALTER TABLE public.portfolios ENABLE ROW LEVEL SECURITY;

-- Students can only access their own portfolio
CREATE POLICY "portfolios_select_own"
    ON public.portfolios FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "portfolios_insert_own"
    ON public.portfolios FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "portfolios_update_own"
    ON public.portfolios FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

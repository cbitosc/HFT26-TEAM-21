-- ============================================================================
-- Migration 004: CodeTrace Coding Journey and Version History (Module 8)
--
-- Tracks student problem-solving evolution, incremental milestone edits,
-- sample execution tests, and editing cadences.
-- Telemetry is used purely as constructive evidence of problem solving
-- and version history, with strict student ownership and RLS security.
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.codetrace_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    question_id TEXT NOT NULL,
    event_type TEXT NOT NULL, -- 'snapshot', 'sample_run', 'submission', 'paste_cadence'
    code_snapshot TEXT NOT NULL,
    diff_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for fast timeline queries
CREATE INDEX IF NOT EXISTS idx_codetrace_session_created
    ON public.codetrace_events (session_id, created_at ASC);

CREATE INDEX IF NOT EXISTS idx_codetrace_user_id
    ON public.codetrace_events (user_id);

-- Enable Row Level Security (RLS)
ALTER TABLE public.codetrace_events ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Candidates own and can view their own telemetry
DROP POLICY IF EXISTS "Users can view own codetrace events" ON public.codetrace_events;
CREATE POLICY "Users can view own codetrace events"
    ON public.codetrace_events
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own codetrace events" ON public.codetrace_events;
CREATE POLICY "Users can insert own codetrace events"
    ON public.codetrace_events
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

-- Service role has full administrative access
DROP POLICY IF EXISTS "Service role can manage all codetrace events" ON public.codetrace_events;
CREATE POLICY "Service role can manage all codetrace events"
    ON public.codetrace_events
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

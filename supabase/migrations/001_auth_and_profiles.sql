-- =============================================================================
-- SkillProof AI — Migration 001: Authentication, Profiles & Hardened RBAC
-- =============================================================================
-- Run this entire file in the Supabase SQL Editor ONCE on a fresh project.
-- Do NOT run twice: all CREATE statements use IF NOT EXISTS guards.
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- 1. Colleges Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.colleges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    code TEXT UNIQUE,
    domain TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_colleges_name ON public.colleges(name);

-- -----------------------------------------------------------------------------
-- 2. Platform Administrators Registry Table
-- Authoritative whitelist of users who may approve/reject verification requests.
-- Never readable by client-side connections; accessed only by service_role.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.platform_admins (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    granted_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    is_active BOOLEAN NOT NULL DEFAULT true
);

CREATE INDEX IF NOT EXISTS idx_platform_admins_active ON public.platform_admins(is_active);

-- -----------------------------------------------------------------------------
-- 3. User Profiles Table
-- Mirrors auth.users 1:1. Role and account_status are NEVER self-assignable.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT NOT NULL,
    requested_role TEXT NOT NULL DEFAULT 'student'
        CHECK (requested_role IN ('student', 'college_admin', 'recruiter')),
    role TEXT NOT NULL DEFAULT 'student'
        CHECK (role IN ('student', 'college_admin', 'recruiter')),
    account_status TEXT NOT NULL DEFAULT 'active'
        CHECK (account_status IN ('active', 'pending_approval', 'rejected', 'suspended')),
    college_id UUID REFERENCES public.colleges(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_profiles_role ON public.profiles(role);
CREATE INDEX IF NOT EXISTS idx_profiles_account_status ON public.profiles(account_status);
CREATE INDEX IF NOT EXISTS idx_profiles_college_id ON public.profiles(college_id);

-- -----------------------------------------------------------------------------
-- 4. College Administrator Verification Requests Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.college_admin_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.profiles(id) ON DELETE CASCADE,
    college_id UUID NOT NULL REFERENCES public.colleges(id) ON DELETE CASCADE,
    department TEXT NOT NULL,
    designation TEXT NOT NULL,
    verification_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (verification_status IN ('pending', 'approved', 'rejected')),
    rejection_reason TEXT,
    reviewed_at TIMESTAMPTZ,
    reviewed_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_college_admin_requests_status
    ON public.college_admin_requests(verification_status);

-- -----------------------------------------------------------------------------
-- 5. Recruiter Profiles & Verification Requests Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.recruiter_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.profiles(id) ON DELETE CASCADE,
    company_name TEXT NOT NULL,
    work_email TEXT NOT NULL,
    designation TEXT NOT NULL,
    company_website TEXT,
    linkedin_url TEXT,
    verification_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (verification_status IN ('pending', 'approved', 'rejected')),
    rejection_reason TEXT,
    reviewed_at TIMESTAMPTZ,
    reviewed_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_recruiter_profiles_status
    ON public.recruiter_profiles(verification_status);

-- -----------------------------------------------------------------------------
-- 6. Administrative Audit Log Table
-- Append-only record of all verification approvals and rejections.
-- Retention-safe design: Deleting an applicant or reviewer preserves audit history.
-- Never modifiable or deletable by client connections.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.admin_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id UUID NOT NULL,
    request_type TEXT NOT NULL CHECK (request_type IN ('college_admin', 'recruiter')),
    applicant_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    applicant_email TEXT,
    reviewer_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action TEXT NOT NULL CHECK (action IN ('approved', 'rejected')),
    rejection_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_request ON public.admin_audit_logs(request_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_applicant ON public.admin_audit_logs(applicant_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_reviewer ON public.admin_audit_logs(reviewer_id);

-- =============================================================================
-- LEAST-PRIVILEGE GRANTS AND REVOCATIONS
-- =============================================================================

REVOKE ALL ON public.colleges FROM PUBLIC, anon, authenticated;
REVOKE ALL ON public.platform_admins FROM PUBLIC, anon, authenticated;
REVOKE ALL ON public.profiles FROM PUBLIC, anon, authenticated;
REVOKE ALL ON public.college_admin_requests FROM PUBLIC, anon, authenticated;
REVOKE ALL ON public.recruiter_profiles FROM PUBLIC, anon, authenticated;
REVOKE ALL ON public.admin_audit_logs FROM PUBLIC, anon, authenticated;

-- Colleges: Read-only for registration forms
GRANT SELECT ON public.colleges TO anon, authenticated;

-- Platform Admins: service_role only; no client-facing grants
GRANT SELECT ON public.platform_admins TO service_role;

-- Profiles: read own row; write only full_name
GRANT SELECT ON public.profiles TO authenticated;
GRANT UPDATE (full_name) ON public.profiles TO authenticated;

-- Verification requests: submit and view own records
GRANT SELECT, INSERT ON public.college_admin_requests TO authenticated;
GRANT SELECT, INSERT ON public.recruiter_profiles TO authenticated;

-- Audit Logs: service_role can select and insert; no client access
GRANT SELECT, INSERT ON public.admin_audit_logs TO service_role;

-- service_role: full operational access
GRANT ALL ON public.colleges TO service_role;
GRANT ALL ON public.platform_admins TO service_role;
GRANT ALL ON public.profiles TO service_role;
GRANT ALL ON public.college_admin_requests TO service_role;
GRANT ALL ON public.recruiter_profiles TO service_role;
GRANT ALL ON public.admin_audit_logs TO service_role;

-- =============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================================================

ALTER TABLE public.colleges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.platform_admins ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.college_admin_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recruiter_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admin_audit_logs ENABLE ROW LEVEL SECURITY;

-- Colleges: public read
CREATE POLICY "colleges_select_all"
    ON public.colleges FOR SELECT USING (true);

-- Platform Admins: deny all client connections (service_role bypasses RLS)
CREATE POLICY "platform_admins_deny_all"
    ON public.platform_admins FOR ALL USING (false);

-- Audit Logs: deny all client connections (service_role reads/writes)
CREATE POLICY "admin_audit_logs_deny_all"
    ON public.admin_audit_logs FOR ALL USING (false);

-- Profiles: own-row isolation only
CREATE POLICY "profiles_select_own"
    ON public.profiles FOR SELECT USING (auth.uid() = id);

CREATE POLICY "profiles_update_own"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- College Admin Requests: view own; insert only a pending own-row request
CREATE POLICY "college_admin_requests_select_own"
    ON public.college_admin_requests FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "college_admin_requests_insert_own_pending"
    ON public.college_admin_requests FOR INSERT
    WITH CHECK (
        auth.uid() = user_id
        AND verification_status = 'pending'
        AND reviewed_by IS NULL
        AND reviewed_at IS NULL
        AND rejection_reason IS NULL
        AND EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid()
              AND requested_role = 'college_admin'
              AND account_status = 'pending_approval'
        )
    );

-- Recruiter Profiles: view own; insert only a pending own-row record matching requested_role
CREATE POLICY "recruiter_profiles_select_own"
    ON public.recruiter_profiles FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "recruiter_profiles_insert_own_pending"
    ON public.recruiter_profiles FOR INSERT
    WITH CHECK (
        auth.uid() = user_id
        AND verification_status = 'pending'
        AND reviewed_by IS NULL
        AND reviewed_at IS NULL
        AND rejection_reason IS NULL
        AND EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid()
              AND requested_role = 'recruiter'
              AND account_status = 'pending_approval'
        )
    );

-- =============================================================================
-- DATABASE FUNCTIONS AND HARDENED TRIGGERS
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Trigger: Invariant guard on profiles UPDATE.
-- Item 1 Correction:
--   - Executed in INVOKER context (NOT SECURITY DEFINER).
--   - Uses standard SQL CURRENT_USER to inspect the actual invoker's identity.
--   - When an authenticated user calls UPDATE, CURRENT_USER is 'authenticated'.
--   - When a SECURITY DEFINER approval function calls UPDATE, CURRENT_USER is
--     the function owner ('postgres' or 'supabase_admin').
--   - Disallows modification of role, account_status, college_id, or email
--     unless invoked by postgres or supabase_admin.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.protect_profile_privileges()
RETURNS TRIGGER
SET search_path = ''
LANGUAGE plpgsql AS $$
BEGIN
    -- Check executing user context
    IF CURRENT_USER NOT IN ('postgres', 'supabase_admin') THEN
        IF NEW.role IS DISTINCT FROM OLD.role THEN
            RAISE EXCEPTION 'Unauthorized: role modification is restricted to administrative workflows.';
        END IF;
        IF NEW.account_status IS DISTINCT FROM OLD.account_status THEN
            RAISE EXCEPTION 'Unauthorized: account_status modification is restricted to administrative workflows.';
        END IF;
        IF NEW.college_id IS DISTINCT FROM OLD.college_id THEN
            RAISE EXCEPTION 'Unauthorized: college_id assignment is restricted to administrative workflows.';
        END IF;
        IF NEW.email IS DISTINCT FROM OLD.email THEN
            RAISE EXCEPTION 'Unauthorized: email must be changed through Supabase Auth.';
        END IF;
    END IF;

    NEW.updated_at := pg_catalog.timezone('utc'::pg_catalog.text, pg_catalog.now());
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_protect_profile_privileges ON public.profiles;
CREATE TRIGGER trg_protect_profile_privileges
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.protect_profile_privileges();

-- -----------------------------------------------------------------------------
-- Trigger: Handle new user signup.
-- Removed broad WHEN OTHERS fallback — real DB errors must abort cleanly.
-- college_id is ALWAYS NULL at signup (never from metadata).
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = ''
LANGUAGE plpgsql AS $$
DECLARE
    v_role pg_catalog.text;
    v_name pg_catalog.text;
BEGIN
    -- 1. Sanitize requested_role
    v_role := COALESCE(pg_catalog.btrim(NEW.raw_user_meta_data->>'requested_role'), 'student');
    IF v_role NOT IN ('student', 'college_admin', 'recruiter') THEN
        v_role := 'student';
    END IF;

    -- 2. Sanitize full_name
    v_name := pg_catalog.btrim(COALESCE(NEW.raw_user_meta_data->>'full_name', ''));
    IF v_name = '' THEN
        v_name := 'SkillProof User';
    END IF;

    -- 3. Insert profile (college_id ALWAYS NULL at signup)
    IF v_role = 'student' THEN
        INSERT INTO public.profiles (id, email, full_name, requested_role, role, account_status, college_id)
        VALUES (NEW.id, NEW.email, v_name, 'student', 'student', 'active', NULL);
    ELSE
        -- college_admin or recruiter: starts as student role, pending_approval
        INSERT INTO public.profiles (id, email, full_name, requested_role, role, account_status, college_id)
        VALUES (NEW.id, NEW.email, v_name, v_role, 'student', 'pending_approval', NULL);
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- =============================================================================
-- HARDENED APPROVAL AND REJECTION FUNCTIONS (service_role only)
-- All functions run as SECURITY DEFINER with SET search_path = ''
-- =============================================================================

-- Approve a College Administrator verification request
CREATE OR REPLACE FUNCTION public.approve_college_admin_request(
    p_request_id UUID,
    p_reviewer_id UUID
)
RETURNS JSONB
SECURITY DEFINER
SET search_path = ''
LANGUAGE plpgsql AS $$
DECLARE
    v_req   public.college_admin_requests%ROWTYPE;
    v_prof  public.profiles%ROWTYPE;
BEGIN
    -- 1. Verify reviewer is an active platform admin
    IF NOT EXISTS (
        SELECT 1 FROM public.platform_admins
        WHERE id = p_reviewer_id AND is_active = true
    ) THEN
        RAISE EXCEPTION 'Reviewer % is not an authorized active platform administrator.', p_reviewer_id;
    END IF;

    -- 2. Lock and fetch request
    SELECT * INTO v_req
    FROM public.college_admin_requests
    WHERE id = p_request_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'College admin request % not found.', p_request_id;
    END IF;
    IF v_req.verification_status <> 'pending' THEN
        RAISE EXCEPTION 'Request % is not pending (status: %).', p_request_id, v_req.verification_status;
    END IF;

    -- 3. Lock and validate profile
    SELECT * INTO v_prof
    FROM public.profiles
    WHERE id = v_req.user_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Profile % not found.', v_req.user_id;
    END IF;
    IF v_prof.account_status <> 'pending_approval' THEN
        RAISE EXCEPTION 'Profile % has unexpected account_status: %.', v_prof.id, v_prof.account_status;
    END IF;
    IF v_prof.requested_role <> 'college_admin' THEN
        RAISE EXCEPTION 'Profile % requested_role mismatch: expected college_admin, got %.', v_prof.id, v_prof.requested_role;
    END IF;

    -- 4. Atomically approve request and update profile
    UPDATE public.college_admin_requests
    SET verification_status = 'approved',
        reviewed_by         = p_reviewer_id,
        reviewed_at         = pg_catalog.timezone('utc'::pg_catalog.text, pg_catalog.now())
    WHERE id = p_request_id;

    UPDATE public.profiles
    SET role           = 'college_admin',
        account_status = 'active',
        college_id     = v_req.college_id,
        updated_at     = pg_catalog.timezone('utc'::pg_catalog.text, pg_catalog.now())
    WHERE id = v_req.user_id;

    -- 5. Record in administrative audit log (Retention-safe with snapshot email)
    INSERT INTO public.admin_audit_logs (
        request_id, request_type, applicant_id, applicant_email, reviewer_id, action, rejection_reason, created_at
    ) VALUES (
        p_request_id, 'college_admin', v_req.user_id, v_prof.email, p_reviewer_id, 'approved', NULL,
        pg_catalog.timezone('utc'::pg_catalog.text, pg_catalog.now())
    );

    RETURN pg_catalog.jsonb_build_object(
        'status',       'success',
        'action',       'approved',
        'request_id',   p_request_id,
        'user_id',      v_req.user_id,
        'college_id',   v_req.college_id,
        'assigned_role','college_admin',
        'reviewed_by',  p_reviewer_id
    );
END;
$$;

-- Approve a Recruiter verification request
CREATE OR REPLACE FUNCTION public.approve_recruiter_request(
    p_request_id UUID,
    p_reviewer_id UUID
)
RETURNS JSONB
SECURITY DEFINER
SET search_path = ''
LANGUAGE plpgsql AS $$
DECLARE
    v_rec   public.recruiter_profiles%ROWTYPE;
    v_prof  public.profiles%ROWTYPE;
BEGIN
    -- 1. Verify reviewer is an active platform admin
    IF NOT EXISTS (
        SELECT 1 FROM public.platform_admins
        WHERE id = p_reviewer_id AND is_active = true
    ) THEN
        RAISE EXCEPTION 'Reviewer % is not an authorized active platform administrator.', p_reviewer_id;
    END IF;

    -- 2. Lock and fetch request
    SELECT * INTO v_rec
    FROM public.recruiter_profiles
    WHERE id = p_request_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Recruiter request % not found.', p_request_id;
    END IF;
    IF v_rec.verification_status <> 'pending' THEN
        RAISE EXCEPTION 'Request % is not pending (status: %).', p_request_id, v_rec.verification_status;
    END IF;

    -- 3. Lock and validate profile
    SELECT * INTO v_prof
    FROM public.profiles
    WHERE id = v_rec.user_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Profile % not found.', v_rec.user_id;
    END IF;
    IF v_prof.account_status <> 'pending_approval' THEN
        RAISE EXCEPTION 'Profile % has unexpected account_status: %.', v_prof.id, v_prof.account_status;
    END IF;
    IF v_prof.requested_role <> 'recruiter' THEN
        RAISE EXCEPTION 'Profile % requested_role mismatch: expected recruiter, got %.', v_prof.id, v_prof.requested_role;
    END IF;

    -- 4. Atomically approve request and update profile
    UPDATE public.recruiter_profiles
    SET verification_status = 'approved',
        reviewed_by         = p_reviewer_id,
        reviewed_at         = pg_catalog.timezone('utc'::pg_catalog.text, pg_catalog.now())
    WHERE id = p_request_id;

    UPDATE public.profiles
    SET role           = 'recruiter',
        account_status = 'active',
        updated_at     = pg_catalog.timezone('utc'::pg_catalog.text, pg_catalog.now())
    WHERE id = v_rec.user_id;

    -- 5. Record in administrative audit log (Retention-safe with snapshot email)
    INSERT INTO public.admin_audit_logs (
        request_id, request_type, applicant_id, applicant_email, reviewer_id, action, rejection_reason, created_at
    ) VALUES (
        p_request_id, 'recruiter', v_rec.user_id, v_prof.email, p_reviewer_id, 'approved', NULL,
        pg_catalog.timezone('utc'::pg_catalog.text, pg_catalog.now())
    );

    RETURN pg_catalog.jsonb_build_object(
        'status',       'success',
        'action',       'approved',
        'request_id',   p_request_id,
        'user_id',      v_rec.user_id,
        'assigned_role','recruiter',
        'reviewed_by',  p_reviewer_id
    );
END;
$$;

-- Reject any verification request (Item 2 Correction)
CREATE OR REPLACE FUNCTION public.reject_verification_request(
    p_request_type TEXT,   -- 'college_admin' or 'recruiter'
    p_request_id   UUID,
    p_reviewer_id  UUID,
    p_reason       TEXT
)
RETURNS JSONB
SECURITY DEFINER
SET search_path = ''
LANGUAGE plpgsql AS $$
DECLARE
    v_user_id   UUID;
    v_prof      public.profiles%ROWTYPE;
    v_status    TEXT;
    v_clean_reason TEXT;
BEGIN
    -- 1. Verify reviewer is an active platform admin
    IF NOT EXISTS (
        SELECT 1 FROM public.platform_admins
        WHERE id = p_reviewer_id AND is_active = true
    ) THEN
        RAISE EXCEPTION 'Reviewer % is not an authorized active platform administrator.', p_reviewer_id;
    END IF;

    -- 2. Validate rejection reason
    v_clean_reason := pg_catalog.btrim(COALESCE(p_reason, ''));
    IF v_clean_reason = '' OR pg_catalog.length(v_clean_reason) < 5 THEN
        RAISE EXCEPTION 'A non-empty rejection reason of at least 5 characters is required.';
    END IF;

    -- 3. Lock and verify the request
    IF p_request_type = 'college_admin' THEN
        SELECT user_id, verification_status INTO v_user_id, v_status
        FROM public.college_admin_requests
        WHERE id = p_request_id
        FOR UPDATE;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'College admin request % not found.', p_request_id;
        END IF;
        IF v_status <> 'pending' THEN
            RAISE EXCEPTION 'Request % is not pending (status: %).', p_request_id, v_status;
        END IF;

    ELSIF p_request_type = 'recruiter' THEN
        SELECT user_id, verification_status INTO v_user_id, v_status
        FROM public.recruiter_profiles
        WHERE id = p_request_id
        FOR UPDATE;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Recruiter request % not found.', p_request_id;
        END IF;
        IF v_status <> 'pending' THEN
            RAISE EXCEPTION 'Request % is not pending (status: %).', p_request_id, v_status;
        END IF;

    ELSE
        RAISE EXCEPTION 'Invalid request_type: %. Expected college_admin or recruiter.', p_request_type;
    END IF;

    -- 4. Lock and verify the associated profile
    SELECT * INTO v_prof
    FROM public.profiles
    WHERE id = v_user_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Profile % not found for request %.', v_user_id, p_request_id;
    END IF;

    IF v_prof.account_status <> 'pending_approval' THEN
        RAISE EXCEPTION 'Profile % has unexpected account_status: % (expected pending_approval).',
            v_prof.id, v_prof.account_status;
    END IF;

    IF v_prof.requested_role <> p_request_type THEN
        RAISE EXCEPTION 'Profile % requested_role mismatch: expected %, got %.',
            v_prof.id, p_request_type, v_prof.requested_role;
    END IF;

    -- 5. Atomically update request to rejected
    IF p_request_type = 'college_admin' THEN
        UPDATE public.college_admin_requests
        SET verification_status = 'rejected',
            rejection_reason    = v_clean_reason,
            reviewed_by         = p_reviewer_id,
            reviewed_at         = pg_catalog.timezone('utc'::pg_catalog.text, pg_catalog.now())
        WHERE id = p_request_id;
    ELSE
        UPDATE public.recruiter_profiles
        SET verification_status = 'rejected',
            rejection_reason    = v_clean_reason,
            reviewed_by         = p_reviewer_id,
            reviewed_at         = pg_catalog.timezone('utc'::pg_catalog.text, pg_catalog.now())
        WHERE id = p_request_id;
    END IF;

    -- 6. Atomically update profile to rejected
    UPDATE public.profiles
    SET account_status = 'rejected',
        updated_at     = pg_catalog.timezone('utc'::pg_catalog.text, pg_catalog.now())
    WHERE id = v_user_id;

    -- 7. Record in administrative audit log (Retention-safe with snapshot email)
    INSERT INTO public.admin_audit_logs (
        request_id, request_type, applicant_id, applicant_email, reviewer_id, action, rejection_reason, created_at
    ) VALUES (
        p_request_id, p_request_type, v_user_id, v_prof.email, p_reviewer_id, 'rejected', v_clean_reason,
        pg_catalog.timezone('utc'::pg_catalog.text, pg_catalog.now())
    );

    RETURN pg_catalog.jsonb_build_object(
        'status',           'success',
        'action',           'rejected',
        'request_type',     p_request_type,
        'request_id',       p_request_id,
        'user_id',          v_user_id,
        'rejection_reason', v_clean_reason,
        'reviewed_by',      p_reviewer_id
    );
END;
$$;

-- =============================================================================
-- FUNCTION EXECUTION GRANTS (exact argument signatures required)
-- =============================================================================

REVOKE ALL ON FUNCTION public.approve_college_admin_request(UUID, UUID)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.approve_college_admin_request(UUID, UUID)
    TO service_role;

REVOKE ALL ON FUNCTION public.approve_recruiter_request(UUID, UUID)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.approve_recruiter_request(UUID, UUID)
    TO service_role;

REVOKE ALL ON FUNCTION public.reject_verification_request(TEXT, UUID, UUID, TEXT)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.reject_verification_request(TEXT, UUID, UUID, TEXT)
    TO service_role;

-- =============================================================================
-- SEED DATA: Initial Colleges
-- Populate with representative institutions; extend as needed.
-- =============================================================================

INSERT INTO public.colleges (name, code, domain) VALUES
    ('Indian Institute of Technology, Bombay', 'IITB', 'iitb.ac.in'),
    ('Indian Institute of Technology, Delhi', 'IITD', 'iitd.ac.in'),
    ('Indian Institute of Technology, Madras', 'IITM', 'iitm.ac.in'),
    ('National Institute of Technology, Trichy', 'NITT', 'nitt.edu'),
    ('National Institute of Technology, Warangal', 'NITW', 'nitw.ac.in'),
    ('Vellore Institute of Technology', 'VIT', 'vit.ac.in'),
    ('Anna University', 'AU', 'annauniv.edu'),
    ('Osmania University', 'OU', 'osmania.ac.in'),
    ('Delhi University', 'DU', 'du.ac.in'),
    ('University of Hyderabad', 'UOH', 'uohyd.ac.in'),
    ('Other / Not Listed', 'OTHER', NULL)
ON CONFLICT (name) DO NOTHING;

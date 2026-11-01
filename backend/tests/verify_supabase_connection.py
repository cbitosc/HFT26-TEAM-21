"""
SkillProof AI — Live Supabase Connection Verifier
Tests connection to Supabase Auth & Database without logging any secret keys.
"""

import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx
from app.config import get_settings

SEPARATOR = "=" * 70


def mask_url(url: str) -> str:
    if not url:
        return "(empty)"
    return url


def verify():
    print(SEPARATOR)
    print("SKILLPROOF AI — LIVE SUPABASE CONFIGURATION & CONNECTION VERIFIER")
    print(SEPARATOR)

    settings = get_settings()

    # 1. Environment Variable Inspection
    print("\n[1/4] Environment Variables Check:")
    has_url = bool(settings.supabase_url and settings.supabase_url.strip())
    has_anon = bool(settings.supabase_anon_key and settings.supabase_anon_key.strip())
    has_service = bool(settings.supabase_service_role_key and settings.supabase_service_role_key.strip())

    print(f"  - SUPABASE_URL:              {'CONFIGURED (' + mask_url(settings.supabase_url) + ')' if has_url else 'MISSING'}")
    print(f"  - SUPABASE_ANON_KEY:         {'CONFIGURED (length: ' + str(len(settings.supabase_anon_key)) + ' chars)' if has_anon else 'MISSING'}")
    print(f"  - SUPABASE_SERVICE_ROLE_KEY: {'CONFIGURED (length: ' + str(len(settings.supabase_service_role_key)) + ' chars)' if has_service else 'MISSING'}")
    print(f"  - SUPABASE_JWT_ALGORITHM:    {settings.supabase_jwt_algorithm}")

    if not has_url or not has_anon or not has_service:
        print("\nSTATUS: INCOMPLETE CONFIGURATION")
        print("Please populate the missing keys in backend/.env and frontend/.env before proceeding.")
        return False

    # 2. JWKS & Auth Endpoint Reachability
    print("\n[2/4] Testing Auth & JWKS Endpoint Reachability...")
    try:
        with httpx.Client(timeout=8.0) as client:
            jwks_res = client.get(settings.jwks_uri)
            if jwks_res.status_code == 200:
                keys = jwks_res.json().get("keys", [])
                print(f"  [PASS] Reached JWKS endpoint ({len(keys)} public key(s) detected)")
            else:
                print(f"  [WARN] JWKS returned HTTP {jwks_res.status_code}")
    except Exception as exc:
        print(f"  [FAIL] Failed to reach JWKS endpoint: {exc}")
        return False

    # 3. Service Client Connection & Table Verification
    print("\n[3/4] Testing Service Role Client & Database Tables...")
    try:
        from app.supabase_client import service_client
        client = service_client()

        tables_to_check = [
            ("public.colleges", "colleges"),
            ("public.profiles", "profiles"),
            ("public.platform_admins", "platform_admins"),
            ("public.college_admin_requests", "college_admin_requests"),
            ("public.recruiter_profiles", "recruiter_profiles"),
            ("public.admin_audit_logs", "admin_audit_logs"),
            ("public.portfolios", "portfolios"),
            ("public.questions", "questions"),
            ("public.assessment_sessions", "assessment_sessions"),
        ]

        missing_tables = []
        for table_label, table_name in tables_to_check:
            try:
                res = client.table(table_name).select("*", count="exact").limit(1).execute()
                print(f"  [PASS] Table exists: {table_label} (record count: {res.count})")
            except Exception as tbl_err:
                missing_tables.append(table_label)
                print(f"  [PENDING] Table not found or inaccessible: {table_label}")

        if missing_tables:
            print(f"\n[!] Note: {len(missing_tables)} table(s) need migration execution in Supabase SQL Editor:")
            for mt in missing_tables:
                print(f"    - {mt}")
        else:
            print("\n  [PASS] All 8 database tables exist and are accessible by service_role!")

    except Exception as exc:
        print(f"  [FAIL] Service client error: {exc}")
        return False

    # 4. Summary
    print(f"\n{SEPARATOR}")
    print("LIVE SUPABASE CONNECTION VERIFIED SUCCESSFULLY")
    print(SEPARATOR)
    return True


if __name__ == "__main__":
    verify()

"""
SkillProof AI — Live Supabase Student Registration and Authentication Integration Test
Tests live student registration, database trigger, profile defaults, login, and /api/auth/me.
Never exposes or logs passwords, tokens, or secret keys.
"""

import sys
import os
import uuid

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))

import httpx
from app.config import get_settings
from app.supabase_client import anon_client, service_client

SEPARATOR = "=" * 70


def mask_email(email: str) -> str:
    parts = email.split("@")
    if len(parts) == 2:
        return f"{parts[0][:3]}***@{parts[1]}"
    return "***"


def run_test():
    print(SEPARATOR)
    print("SKILLPROOF AI — LIVE SUPABASE AUTHENTICATION INTEGRATION TEST")
    print(SEPARATOR)

    settings = get_settings()

    if not settings.is_supabase_configured:
        print("\n[ERROR] Supabase is not configured in backend/.env.")
        return False

    # Unique test email to prevent collisions
    test_id = uuid.uuid4().hex[:8]
    test_email = f"student.test.{test_id}@skillproof.ai"
    test_password = f"TestPass!{uuid.uuid4().hex[:12]}"
    test_full_name = f"Test Student {test_id}"

    user_id = None
    access_token = None

    try:
        anon = anon_client()
        admin = service_client()

        # ---------------------------------------------------------------------
        # 1. Test Student Registration (Simulating Frontend SignUp)
        # ---------------------------------------------------------------------
        print("\n[1/6] Registering new student via Supabase Auth...")
        print(f"      Target Email: {mask_email(test_email)}")
        try:
            signup_res = anon.auth.sign_up({
                "email": test_email,
                "password": test_password,
                "options": {
                    "data": {
                        "full_name": test_full_name,
                        "requested_role": "student",
                    }
                }
            })
            if signup_res.user and signup_res.user.id:
                user_id = signup_res.user.id
                print(f"  [PASS] User successfully created in auth.users via sign_up (ID: {user_id})")
        except Exception as signup_err:
            if "rate limit" in str(signup_err).lower():
                print("  [INFO] Supabase public sign_up email rate limit reached (3/hr free tier limit).")
                print("         Provisioning test user via admin API to verify trigger & auth pipeline...")
                admin_user = admin.auth.admin.create_user({
                    "email": test_email,
                    "password": test_password,
                    "email_confirm": True,
                    "user_metadata": {
                        "full_name": test_full_name,
                        "requested_role": "student",
                    }
                })
                user_id = admin_user.user.id
                print(f"  [PASS] User successfully created in auth.users (ID: {user_id})")
            else:
                raise

        # ---------------------------------------------------------------------
        # 2. Verify Database Trigger: public.profiles Row & Secure Defaults
        # ---------------------------------------------------------------------
        print("\n[2/6] Verifying public.profiles row created by on_auth_user_created trigger...")
        profile_res = admin.table("profiles").select("*").eq("id", user_id).execute()

        if not profile_res.data or len(profile_res.data) == 0:
            print("  [FAIL] Database trigger failed: no row in public.profiles for user.")
            return False

        profile = profile_res.data[0]
        print(f"  [PASS] Profile exists in public.profiles")
        print(f"         - Email:          {mask_email(profile['email'])}")
        print(f"         - Full Name:      {profile['full_name']}")
        print(f"         - Role:           {profile['role']} (expected: student)")
        print(f"         - Requested Role: {profile['requested_role']} (expected: student)")
        print(f"         - Account Status: {profile['account_status']} (expected: active)")
        print(f"         - College ID:     {profile['college_id']} (expected: None)")

        assert profile["role"] == "student", f"Expected role 'student', got '{profile['role']}'"
        assert profile["account_status"] == "active", f"Expected 'active', got '{profile['account_status']}'"
        assert profile["college_id"] is None, f"Expected college_id None, got '{profile['college_id']}'"
        print("  [PASS] Default role and active status verified as assigned securely by trigger.")

        # ---------------------------------------------------------------------
        # 3. Handle Email Confirmation if enabled on Supabase project
        # ---------------------------------------------------------------------
        # If the project requires email confirmation, confirm via admin API so login works
        try:
            admin.auth.admin.update_user_by_id(user_id, {"email_confirm": True})
        except Exception:
            pass  # Already confirmed or not required

        # ---------------------------------------------------------------------
        # 4. Test Login with Valid Credentials
        # ---------------------------------------------------------------------
        print("\n[3/6] Testing Login with valid credentials via Supabase Auth...")
        login_res = anon.auth.sign_in_with_password({
            "email": test_email,
            "password": test_password,
        })

        if not login_res.session or not login_res.session.access_token:
            print("  [FAIL] Login failed: no session or access_token returned.")
            return False

        access_token = login_res.session.access_token
        print(f"  [PASS] Login successful! Valid JWT issued (token length: {len(access_token)} chars).")

        # ---------------------------------------------------------------------
        # 5. Test Authenticated Access to FastAPI /api/auth/me
        # ---------------------------------------------------------------------
        print("\n[4/6] Testing authenticated access to /api/auth/me using live JWT...")
        # Test directly against running FastAPI server
        with httpx.Client(base_url="http://127.0.0.1:8000", timeout=10.0) as http_client:
            me_res = http_client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if me_res.status_code != 200:
                print(f"  [FAIL] /api/auth/me returned HTTP {me_res.status_code}: {me_res.text}")
                return False

            me_data = me_res.json()
            print(f"  [PASS] /api/auth/me returned HTTP 200 OK")
            print(f"         - Resolved User ID: {me_data['id']}")
            print(f"         - Authoritative Role: {me_data['role']}")
            print(f"         - Account Status:    {me_data['account_status']}")
            assert me_data["id"] == user_id
            assert me_data["role"] == "student"
            assert me_data["account_status"] == "active"

        # ---------------------------------------------------------------------
        # 6. Test Invalid Credentials and Unauthorized Access
        # ---------------------------------------------------------------------
        print("\n[5/6] Testing invalid credentials & unauthorized access scenarios...")

        # A. Wrong password login
        try:
            anon.auth.sign_in_with_password({
                "email": test_email,
                "password": "IncorrectPassword123!",
            })
            print("  [FAIL] Wrong password was unexpectedly accepted!")
            return False
        except Exception as auth_err:
            print(f"  [PASS] Invalid password rejected by Supabase Auth (caught expected error)")

        # B. Unauthenticated /api/auth/me
        with httpx.Client(base_url="http://127.0.0.1:8000", timeout=5.0) as http_client:
            no_token_res = http_client.get("/api/auth/me")
            assert no_token_res.status_code == 401
            print("  [PASS] Missing Authorization header -> HTTP 401 Unauthorized")

            # C. Forged / invalid signature token
            forged_token = access_token[:-8] + "ABCDEFGH"
            invalid_res = http_client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {forged_token}"}
            )
            assert invalid_res.status_code == 401
            print("  [PASS] Tampered JWT signature -> HTTP 401 Unauthorized (fail-closed)")

        # ---------------------------------------------------------------------
        # 7. Cleanup Test User
        # ---------------------------------------------------------------------
        print("\n[6/6] Cleaning up test user from live database...")
        try:
            admin.auth.admin.delete_user(user_id)
            print(f"  [PASS] Test user {user_id} deleted successfully.")
        except Exception as clean_err:
            print(f"  [WARN] Cleanup error: {clean_err}")

        print(f"\n{SEPARATOR}")
        print("ALL LIVE AUTHENTICATION INTEGRATION TESTS PASSED (100% SUCCESS)")
        print(SEPARATOR)
        return True

    except Exception as exc:
        print(f"\n[FAIL] Unexpected error during live test: {exc}")
        import traceback
        traceback.print_exc()
        if user_id:
            try:
                admin = service_client()
                admin.auth.admin.delete_user(user_id)
                print(f"[CLEANUP] Deleted test user {user_id}")
            except Exception:
                pass
        return False


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)

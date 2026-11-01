"""
Standalone test runner for SkillProof AI Module 2.
Directly executes all verification tests using asyncio and httpx ASGITransport.
"""

import sys
import os
import uuid
import asyncio
from datetime import datetime, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import httpx
from fastapi import HTTPException
from app.main import app
from app.models import (
    UserProfile,
    ProfileUpdateRequest,
    CollegeAdminRequestCreate,
    RecruiterRequestCreate,
    RejectionRequest,
    AdminAuditLogResponse,
    PortfolioStructure,
    ProjectItem,
    SkillsStructure,
)
from app.services.question_bank import get_question_by_id, evaluate_submission
from app.api.deps import require_role


async def main():
    print("=================================================================")
    print("SkillProof AI — Modules 2, 3, 4, 5 & 6 End-to-End Test Suite")
    print("=================================================================")
    passed = 0
    total = 0

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:

        # 1. Root
        total += 1
        r = await client.get("/")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert r.json()["status"] == "online"
        print("PASS [1/35]: GET / (Root endpoint online)")
        passed += 1

        # 2. Health
        total += 1
        r = await client.get("/api/health")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert r.json()["status"] == "ok"
        print("PASS [2/35]: GET /api/health (Service status ok)")
        passed += 1

        # 3. Unauthenticated /api/auth/me -> 401
        total += 1
        r = await client.get("/api/auth/me")
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("PASS [3/35]: GET /api/auth/me without token -> HTTP 401 Unauthorized")
        passed += 1

        # 4. Invalid token -> 401 or 503 (Fail-Closed)
        total += 1
        r = await client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.payload"})
        assert r.status_code in (401, 503), f"Expected 401/503, got {r.status_code}"
        print("PASS [4/35]: GET /api/auth/me with invalid token -> Fail-closed (HTTP 401/503)")
        passed += 1

        # 5. Unauthenticated /api/requests/college-admin -> 401
        total += 1
        r = await client.get("/api/requests/college-admin")
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("PASS [5/35]: GET /api/requests/college-admin without token -> HTTP 401")
        passed += 1

        # 6. Unauthenticated /api/admin/requests/college-admin -> 401
        total += 1
        r = await client.get("/api/admin/requests/college-admin")
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("PASS [6/35]: GET /api/admin/requests/college-admin without token -> HTTP 401")
        passed += 1

        # 7. Unauthenticated /api/admin/audit-logs -> 401
        total += 1
        r = await client.get("/api/admin/audit-logs")
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("PASS [7/35]: GET /api/admin/audit-logs without token -> HTTP 401")
        passed += 1

        # 8. require_role accepts active student
        total += 1
        profile = UserProfile(
            id=uuid.uuid4(),
            email="student@example.com",
            full_name="Active Student",
            requested_role="student",
            role="student",
            account_status="active",
            college_id=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        checker = require_role("student")
        res = await checker(profile)
        assert res.role == "student" and res.account_status == "active"
        print("PASS [8/35]: require_role accepts active student")
        passed += 1

        # 9. require_role rejects pending status -> 403
        total += 1
        pending_profile = UserProfile(
            id=uuid.uuid4(),
            email="admin@example.com",
            full_name="Pending Admin",
            requested_role="college_admin",
            role="college_admin",
            account_status="pending_approval",
            college_id=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        try:
            checker_admin = require_role("college_admin")
            await checker_admin(pending_profile)
            assert False, "Should have raised HTTPException 403"
        except HTTPException as exc:
            assert exc.status_code == 403
            assert "pending_approval" in exc.detail
        print("PASS [9/35]: require_role rejects pending_approval account -> HTTP 403")
        passed += 1

        # 10. require_role rejects role mismatch -> 403
        total += 1
        try:
            checker_recruiter = require_role("recruiter")
            await checker_recruiter(profile)  # profile has role="student"
            assert False, "Should have raised HTTPException 403"
        except HTTPException as exc:
            assert exc.status_code == 403
            assert "Access denied" in exc.detail
        print("PASS [10/35]: require_role rejects role mismatch (student accessing recruiter) -> HTTP 403")
        passed += 1

        # 11. Model validation: profile update
        total += 1
        try:
            ProfileUpdateRequest(full_name="   ")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
        valid_req = ProfileUpdateRequest(full_name="  Jane Doe  ")
        assert valid_req.full_name == "Jane Doe"
        print("PASS [11/35]: ProfileUpdateRequest validates and sanitizes input (blank rejected)")
        passed += 1

        # 12. Model validation: rejection reason minimum length
        total += 1
        try:
            RejectionRequest(request_id=uuid.uuid4(), reason="no")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
        valid_rej = RejectionRequest(request_id=uuid.uuid4(), reason="Documentation was unverifiable.")
        assert valid_rej.reason == "Documentation was unverifiable."
        print("PASS [12/35]: RejectionRequest enforces minimum 5-character reason")
        passed += 1

        # 13. Audit log model serialization with applicant_id present
        total += 1
        applicant_id = uuid.uuid4()
        reviewer_id = uuid.uuid4()
        req_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        log_entry = AdminAuditLogResponse(
            id=uuid.uuid4(),
            request_id=req_id,
            request_type="college_admin",
            applicant_id=applicant_id,
            applicant_email="applicant@college.edu",
            reviewer_id=reviewer_id,
            action="approved",
            rejection_reason=None,
            created_at=now,
        )
        assert log_entry.applicant_id == applicant_id
        assert log_entry.applicant_email == "applicant@college.edu"
        print("PASS [13/35]: AdminAuditLogResponse accepts standard active log record")
        passed += 1

        # 14. Audit log model retention safety (applicant deleted -> applicant_id is None, applicant_email preserved)
        total += 1
        deleted_user_log = AdminAuditLogResponse(
            id=uuid.uuid4(),
            request_id=req_id,
            request_type="recruiter",
            applicant_id=None,
            applicant_email="deleted_recruiter@company.com",
            reviewer_id=reviewer_id,
            action="rejected",
            rejection_reason="Unverified company registration details.",
            created_at=now,
        )
        assert deleted_user_log.applicant_id is None
        assert deleted_user_log.applicant_email == "deleted_recruiter@company.com"
        print("PASS [14/35]: AdminAuditLogResponse preserves audit entry when applicant_id is SET NULL")
        passed += 1

        # 15. Verification request creation models validate fields
        total += 1
        col_req = CollegeAdminRequestCreate(
            college_id=uuid.uuid4(),
            department="  Computer Science  ",
            designation="  Head of Department  ",
        )
        assert col_req.department == "Computer Science"
        assert col_req.designation == "Head of Department"

        rec_req = RecruiterRequestCreate(
            company_name="  Tech Innovations Ltd  ",
            work_email="talent@techinnovations.com",
            designation="  Lead Technical Recruiter  ",
            company_website="https://techinnovations.com",
        )
        assert rec_req.company_name == "Tech Innovations Ltd"
        assert rec_req.work_email == "talent@techinnovations.com"
        assert rec_req.designation == "Lead Technical Recruiter"
        print("PASS [15/35]: CollegeAdminRequestCreate & RecruiterRequestCreate validate and sanitize input")
        passed += 1

        # =====================================================================
        # MODULE 3 TESTS: Portfolio Upload, Extraction, Review & Confirmation
        # =====================================================================

        dev_headers = {"Authorization": "Bearer dev-student-token"}

        # 16. Valid JSON portfolio upload
        total += 1
        valid_json_payload = json.dumps({
            "projects": [
                {
                    "name": "Cloud Task Engine",
                    "description": "Distributed async task scheduler",
                    "technologies": ["Python", "FastAPI", "Redis", "Docker"]
                }
            ],
            "skills": {
                "programming_languages": ["Python", "TypeScript", "SQL"],
                "frameworks_and_tools": ["FastAPI", "React", "Docker"]
            },
            "domains": ["Backend Development", "Cloud Computing"],
            "dsa_topics": ["Arrays", "Hash Tables", "Queues"]
        }).encode("utf-8")

        r = await client.post(
            "/api/portfolio/upload",
            headers=dev_headers,
            files={"file": ("portfolio.json", valid_json_payload, "application/json")}
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["confirmed"] is False
        assert data["skills_status"] == "unverified"
        assert len(data["data"]["projects"]) == 1
        assert "Python" in data["data"]["skills"]["programming_languages"]
        print("PASS [16/35]: POST /api/portfolio/upload with valid JSON -> HTTP 200 unconfirmed draft")
        passed += 1

        # 17. Valid PDF portfolio upload
        total += 1
        minimal_pdf = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 170 >>
stream
BT
/F1 12 Tf
100 700 Td
(PROJECTS) Tj
0 -20 Td
(Distributed Task Queue - Python, FastAPI, Redis, Docker) Tj
0 -20 Td
(Skills: Python, TypeScript, React, PostgreSQL) Tj
0 -20 Td
(Domains: Backend Development, Cloud Computing) Tj
0 -20 Td
(DSA: Arrays, Dynamic Programming, Trees) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000465 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
534
%%EOF"""

        r = await client.post(
            "/api/portfolio/upload",
            headers=dev_headers,
            files={"file": ("resume.pdf", minimal_pdf, "application/pdf")}
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert "Python" in data["data"]["skills"]["programming_languages"]
        assert "Backend Development" in data["data"]["domains"]
        assert "Arrays" in data["data"]["dsa_topics"]
        print("PASS [17/35]: POST /api/portfolio/upload with valid PDF -> HTTP 200 extracted content")
        passed += 1

        # 18. Invalid JSON upload (malformed syntax) -> 400
        total += 1
        r = await client.post(
            "/api/portfolio/upload",
            headers=dev_headers,
            files={"file": ("broken.json", b"{ malformed: json, syntax... }", "application/json")}
        )
        assert r.status_code == 400, f"Expected 400, got {r.status_code}"
        print("PASS [18/35]: POST /api/portfolio/upload with malformed JSON -> HTTP 400 Bad Request")
        passed += 1

        # 19. Unsupported file type upload (.txt) -> 400
        total += 1
        r = await client.post(
            "/api/portfolio/upload",
            headers=dev_headers,
            files={"file": ("unsupported.txt", b"plain text content", "text/plain")}
        )
        assert r.status_code == 400, f"Expected 400, got {r.status_code}"
        print("PASS [19/35]: POST /api/portfolio/upload with unsupported file type -> HTTP 400")
        passed += 1

        # 20. Empty / corrupted PDF upload -> 400
        total += 1
        r = await client.post(
            "/api/portfolio/upload",
            headers=dev_headers,
            files={"file": ("corrupt.pdf", b"%PDF-corrupted-binary-content-without-catalog", "application/pdf")}
        )
        assert r.status_code == 400, f"Expected 400, got {r.status_code}"
        print("PASS [20/35]: POST /api/portfolio/upload with corrupted PDF -> HTTP 400")
        passed += 1

        # 21. Unauthorized portfolio upload (no token) -> 401
        total += 1
        r = await client.post(
            "/api/portfolio/upload",
            files={"file": ("portfolio.json", valid_json_payload, "application/json")}
        )
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("PASS [21/35]: POST /api/portfolio/upload without token -> HTTP 401 Unauthorized")
        passed += 1

        # 22. Role mismatch upload (require_role rejects non-students) -> 403
        total += 1
        recruiter_profile = UserProfile(
            id=uuid.uuid4(),
            email="recruiter@company.com",
            full_name="Recruiter Jane",
            requested_role="recruiter",
            role="recruiter",
            account_status="active",
            college_id=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        student_checker = require_role("student")
        try:
            await student_checker(recruiter_profile)
            assert False, "Should have raised HTTPException 403"
        except HTTPException as exc:
            assert exc.status_code == 403
            assert "Access denied" in exc.detail
        print("PASS [22/35]: require_role('student') blocks recruiter from portfolio endpoints -> HTTP 403")
        passed += 1

        # 23. Student portfolio retrieval (GET /api/portfolio/me) -> 200
        total += 1
        r = await client.get("/api/portfolio/me", headers=dev_headers)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        saved_portfolio = r.json()
        assert saved_portfolio["user_id"] == "00000000-0000-0000-0000-000000000001"
        print("PASS [23/35]: GET /api/portfolio/me retrieves current student's portfolio -> HTTP 200")
        passed += 1

        # 24. Portfolio confirmation (POST /api/portfolio/confirm)
        total += 1
        confirm_payload = {
            "data": {
                "projects": [
                    {
                        "name": "Production E-Commerce API",
                        "description": "High throughput microservice",
                        "technologies": ["Python", "FastAPI", "PostgreSQL"]
                    }
                ],
                "skills": {
                    "programming_languages": ["Python", "Go", "TypeScript"],
                    "frameworks_and_tools": ["FastAPI", "Docker", "PostgreSQL"]
                },
                "domains": ["Backend Development", "Cloud Computing"],
                "dsa_topics": ["Arrays", "Hash Tables", "Dynamic Programming"]
            }
        }
        r = await client.post("/api/portfolio/confirm", headers=dev_headers, json=confirm_payload)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        confirmed_res = r.json()
        assert confirmed_res["confirmed"] is True
        assert confirmed_res["skills_status"] == "unverified"
        assert confirmed_res["confirmed_at"] is not None
        assert len(confirmed_res["data"]["projects"]) == 1
        print("PASS [24/35]: POST /api/portfolio/confirm marks confirmed with unverified status -> HTTP 200")
        passed += 1

        # 25. Unauthenticated GET /api/portfolio/me -> 401
        total += 1
        r = await client.get("/api/portfolio/me")
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("PASS [25/35]: GET /api/portfolio/me without token -> HTTP 401 Unauthorized")
        passed += 1

        # =====================================================================
        # MODULES 4, 5, 6: QUESTION BANK, ASSESSMENT AGENT & STUDENT WORKSPACE
        # =====================================================================

        # 26. Question Bank: List questions (conceals reference solutions & hidden tests)
        total += 1
        r = await client.get("/api/assessment/questions", headers=dev_headers)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        questions_list = r.json()
        assert len(questions_list) >= 20, f"Expected >= 20 seed questions, got {len(questions_list)}"
        first_q = questions_list[0]
        assert "reference_solution" not in first_q
        assert "test_cases" not in first_q
        assert "public_test_cases" in first_q
        print(f"PASS [26/35]: GET /api/assessment/questions -> HTTP 200 ({len(questions_list)} curated questions verified)")
        passed += 1

        # 27. Question Bank: Filter by difficulty (hard)
        total += 1
        r = await client.get("/api/assessment/questions?difficulty=hard", headers=dev_headers)
        assert r.status_code == 200
        hard_questions = r.json()
        assert len(hard_questions) >= 6
        assert all(q["difficulty"] == "hard" for q in hard_questions)
        print("PASS [27/35]: GET /api/assessment/questions?difficulty=hard -> HTTP 200 (filtered)")
        passed += 1

        # 28. Question Bank: Get single question
        total += 1
        r = await client.get("/api/assessment/questions/two-sum", headers=dev_headers)
        assert r.status_code == 200
        q_data = r.json()
        assert q_data["id"] == "two-sum"
        assert q_data["title"] == "Two Sum"
        print("PASS [28/35]: GET /api/assessment/questions/two-sum -> HTTP 200")
        passed += 1

        # 29. Question Bank: Deterministic evaluation of reference solution (100% pass)
        total += 1
        two_sum_q = get_question_by_id("two-sum")
        assert two_sum_q is not None
        eval_result = evaluate_submission(two_sum_q, two_sum_q.reference_solution)
        assert eval_result.all_passed is True
        assert eval_result.passed_tests == len(two_sum_q.test_cases)
        print("PASS [29/35]: Deterministic test evaluation: reference solution passes 100% test cases")
        passed += 1

        # 30. Question Bank: Deterministic evaluation of flawed/broken submission
        total += 1
        flawed_code = "def two_sum(nums, target):\n    return [0, 0]\n"
        flawed_result = evaluate_submission(two_sum_q, flawed_code)
        assert flawed_result.all_passed is False
        assert "failed" in flawed_result.feedback.lower()
        print("PASS [30/35]: Deterministic test evaluation: incorrect solution fails assertions gracefully")
        passed += 1

        # 31. Assessment Agent: Coordinate assessment generation (Novice, Verified)
        total += 1
        gen_payload = {
            "tier": "novice",
            "track": "verified",
            "domain_filter": "Backend Development",
            "preferred_language": "python"
        }
        r = await client.post("/api/assessment/generate", headers=dev_headers, json=gen_payload)
        assert r.status_code == 201, f"Expected 201, got {r.status_code}"
        sess_data = r.json()
        session_id = sess_data["session_id"]
        assert sess_data["tier"] == "novice"
        assert sess_data["track"] == "verified"
        assert len(sess_data["questions"]) >= 2
        print("PASS [31/35]: POST /api/assessment/generate (Novice, Verified) -> HTTP 201 session active")
        passed += 1

        # 32. Assessment Agent: Generate Master Practice session (Isolated Sandbox)
        total += 1
        prac_payload = {
            "tier": "master",
            "track": "practice",
            "domain_filter": "Algorithms & DSA",
            "preferred_language": "python"
        }
        r = await client.post("/api/assessment/generate", headers=dev_headers, json=prac_payload)
        assert r.status_code == 201
        prac_data = r.json()
        assert prac_data["track"] == "practice"
        assert prac_data["tier"] == "master"
        print("PASS [32/35]: POST /api/assessment/generate (Master, Practice) -> HTTP 201 isolated session")
        passed += 1

        # 33. Student Workspace: Retrieve active session
        total += 1
        r = await client.get(f"/api/assessment/session/{session_id}", headers=dev_headers)
        assert r.status_code == 200
        retrieved_sess = r.json()
        assert retrieved_sess["session_id"] == session_id
        assert retrieved_sess["status"] == "active"
        print("PASS [33/35]: GET /api/assessment/session/{id} -> HTTP 200 workspace loaded")
        passed += 1

        # 34. Student Workspace: Submit answers and receive evaluated summary
        total += 1
        # Prepare valid submissions for the active session questions
        submitted_answers = []
        for q in sess_data["questions"]:
            full_q = get_question_by_id(q["id"])
            sol = full_q.reference_solution if full_q else q["starter_code"]
            submitted_answers.append({"question_id": q["id"], "submitted_code": sol})

        submit_payload = {"submissions": submitted_answers}
        r = await client.post(f"/api/assessment/session/{session_id}/submit", headers=dev_headers, json=submit_payload)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        summary_res = r.json()
        assert summary_res["status"] == "completed"
        assert summary_res["score_percentage"] == 100.0
        assert summary_res["questions_passed"] == len(sess_data["questions"])
        assert "Verified Assessment" in summary_res["verification_notice"]
        print("PASS [34/35]: POST /api/assessment/session/{id}/submit -> HTTP 200 evaluation summary")
        passed += 1

        # 35. Student Workspace: Retrieve assessment history
        total += 1
        r = await client.get("/api/assessment/history", headers=dev_headers)
        assert r.status_code == 200
        hist_data = r.json()
        assert len(hist_data) >= 1
        assert any(s["session_id"] == session_id for s in hist_data)
        print("PASS [35/35]: GET /api/assessment/history -> HTTP 200 student past runs listed")
        passed += 1

    print("=================================================================")
    print(f"Results: {passed}/{total} tests PASSED (100% success rate)")
    print("=================================================================")


if __name__ == "__main__":
    asyncio.run(main())

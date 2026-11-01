"""
SkillProof AI — Live End-to-End Flow Demo Script
Demonstrates Modules 3, 4, 5, and 6 working against the running server.
"""

import json
import httpx

BASE_URL = "http://127.0.0.1:8000"
DEV_HEADERS = {"Authorization": "Bearer dev-student-token"}
SEPARATOR = "=" * 70


def run_demo():
    print(SEPARATOR)
    print("SKILLPROOF AI — LIVE END-TO-END DEMO (MODULES 3, 4, 5, 6)")
    print(SEPARATOR)

    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # Step 1: Health check
        r = client.get("/api/health")
        print(f"\n[1/6] Health Check: status {r.status_code}")
        print(f"      Response: {r.json()['name']} ({r.json()['status']})")

        # Step 2: Upload Student Portfolio (Module 3)
        sample_portfolio = {
            "projects": [
                {
                    "name": "Distributed Microservice Pipeline",
                    "description": "High-throughput asynchronous task queue with message broker",
                    "technologies": ["Python", "FastAPI", "Redis", "Docker", "PostgreSQL"]
                }
            ],
            "skills": {
                "programming_languages": ["Python", "TypeScript", "SQL"],
                "frameworks_and_tools": ["FastAPI", "Docker", "Redis", "Git"]
            },
            "domains": ["Backend Development", "Algorithms & DSA"],
            "dsa_topics": ["Arrays & Hash Tables", "Queues", "Binary Search"]
        }
        r = client.post(
            "/api/portfolio/upload",
            headers=DEV_HEADERS,
            files={"file": ("portfolio.json", json.dumps(sample_portfolio).encode("utf-8"), "application/json")}
        )
        print(f"\n[2/6] Portfolio Upload: status {r.status_code}")
        extracted = r.json()
        print(f"      Extracted Projects: {[p['name'] for p in extracted['data']['projects']]}")
        print(f"      Extracted Domains:  {extracted['data']['domains']}")
        print(f"      Initial Status:     confirmed={extracted['confirmed']}, skills={extracted['skills_status']}")

        # Step 3: Confirm Portfolio (Module 3)
        confirm_payload = {"data": extracted["data"]}
        r = client.post("/api/portfolio/confirm", headers=DEV_HEADERS, json=confirm_payload)
        print(f"\n[3/6] Confirm Portfolio: status {r.status_code}")
        confirmed = r.json()
        print(f"      Confirmed: {confirmed['confirmed']}, Skills Status: {confirmed['skills_status']}")
        print(f"      Timestamp: {confirmed['confirmed_at']}")

        # Step 4: Explore Question Bank (Module 4)
        r = client.get("/api/assessment/questions", headers=DEV_HEADERS)
        print(f"\n[4/6] Question Bank Query: status {r.status_code}")
        questions = r.json()
        print(f"      Available Verified Challenges: {len(questions)}")
        print(f"      First Question: '{questions[0]['title']}' ({questions[0]['difficulty'].upper()})")
        print(f"      Public Data Shielded: reference_solution in payload? {'reference_solution' in questions[0]}")

        # Step 5: Assessment Agent Coordinates Session (Module 5)
        gen_payload = {
            "tier": "novice",
            "track": "verified",
            "domain_filter": "Backend Development",
            "preferred_language": "python"
        }
        r = client.post("/api/assessment/generate", headers=DEV_HEADERS, json=gen_payload)
        print(f"\n[5/6] Assessment Agent Generator: status {r.status_code}")
        session = r.json()
        session_id = session["session_id"]
        print(f"      Session ID:    {session_id}")
        print(f"      Matched Tier:  {session['tier'].upper()} ({session['track'].upper()} track)")
        print(f"      Agent Guidance: \"{session.get('ai_guidance')}\"")
        assigned_titles = [q['title'] for q in session['questions']]
        print(f"      Assigned Challenges ({len(assigned_titles)}): {assigned_titles}")

        # Step 6: Solve and Submit in Student Workspace (Module 6)
        print(f"\n[6/6] Submitting Solutions in Assessment Workspace...")
        submissions = []
        for q in session["questions"]:
            qid = q["id"]
            if qid == "fizzbuzz-api":
                code = (
                    "def fizz_buzz(n):\n"
                    "    res = []\n"
                    "    for i in range(1, n + 1):\n"
                    "        if i % 15 == 0: res.append('FizzBuzz')\n"
                    "        elif i % 3 == 0: res.append('Fizz')\n"
                    "        elif i % 5 == 0: res.append('Buzz')\n"
                    "        else: res.append(str(i))\n"
                    "    return res\n"
                )
            elif qid == "factorial-memo":
                code = (
                    "def factorial(n):\n"
                    "    if n < 0: raise ValueError('Input must be non-negative')\n"
                    "    res = 1\n"
                    "    for i in range(2, n + 1): res *= i\n"
                    "    return res\n"
                )
            elif qid == "filter-active-users":
                code = (
                    "def filter_students(users):\n"
                    "    return sorted([u['name'] for u in users if u.get('status') == 'active' and u.get('role') == 'student'])\n"
                )
            else:
                code = q["starter_code"]
            submissions.append({"question_id": qid, "submitted_code": code})

        r = client.post(f"/api/assessment/session/{session_id}/submit", headers=DEV_HEADERS, json={"submissions": submissions})
        print(f"      Submission status: {r.status_code}")
        summary = r.json()
        print(f"      Final Status:      {summary['status'].upper()}")
        print(f"      Score Percentage:  {summary['score_percentage']}%")
        print(f"      Challenges Passed: {summary['questions_passed']} / {summary['total_questions']}")
        print(f"      Notice:            {summary['verification_notice']}")
        for qr in summary["results"]:
            status_icon = "PASS" if qr["all_passed"] else "FAIL"
            print(f"         [{status_icon}] {qr['title']}: {qr['passed_tests']}/{qr['total_tests']} tests ({qr['feedback']})")

    print(f"\n{SEPARATOR}")
    print("SUCCESS: Full End-to-End Flow (Modules 3-6) Executed Without Error!")
    print(SEPARATOR)


if __name__ == "__main__":
    run_demo()

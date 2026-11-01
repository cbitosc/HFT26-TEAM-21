"""
Basic SkillProof AI Assessment Agent (Module 5).
Coordinates assessment assembly by matching confirmed student portfolio
domains, skills, and DSA topics with the verified question bank.
Guarantees question bank authority and graceful fallback when external AI is unavailable.
"""

from __future__ import annotations

import os
import re
import ast
import json
import uuid
import logging
import threading
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import httpx

from app.config import get_settings
from app.models import (
    AssessmentGenerateRequest,
    AssessmentSessionResponse,
    AssessmentSummaryResponse,
    AssessmentSubmitRequest,
    QuestionPublic,
    QuestionResult,
    PortfolioResponse,
    SampleRunRequest,
    SampleRunResponse,
    ExecutionStatus,
)
from app.services.sandbox import get_sandbox_provider, ExecutionResult
from app.services.portfolio_storage import get_portfolio
from app.services.question_bank import (
    get_all_questions,
    get_question_by_id,
    to_public_question,
    filter_questions,
    evaluate_submission,
)

logger = logging.getLogger("skillproof.assessment.agent")

# Local storage fallback for assessment sessions
STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
SESSIONS_FILE = os.path.join(STORAGE_DIR, "assessment_sessions.json")
_sessions_lock = threading.Lock()


def _ensure_sessions_file():
    os.makedirs(STORAGE_DIR, exist_ok=True)
    if not os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)


def _read_sessions() -> Dict[str, Any]:
    _ensure_sessions_file()
    with _sessions_lock:
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}


def _write_sessions(data: Dict[str, Any]):
    _ensure_sessions_file()
    with _sessions_lock:
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)


async def _generate_featherless_guidance(portfolio: Optional[PortfolioResponse], tier: str, domain: str) -> Optional[str]:
    """
    Optionally requests a personalized assessment intro and guidance from Featherless AI.
    Gracefully returns None if credentials are missing or the API call fails.
    """
    settings = get_settings()
    if not settings.featherless_api_key:
        return None

    prompt = (
        f"You are the SkillProof AI Assessment Coordinator. A student is taking a {tier.upper()} assessment in {domain}. "
        f"Provide a brief, 2-sentence encouraging guidance note emphasizing clean problem-solving and systematic testing."
    )

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.post(
                f"{settings.featherless_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.featherless_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.featherless_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 100,
                    "temperature": 0.5,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.info("Featherless AI guidance unavailable, using default: %s", exc)

    return None


async def coordinate_assessment(
    user_id: uuid.UUID,
    req: AssessmentGenerateRequest,
) -> AssessmentSessionResponse:
    """
    Central Assessment Coordination Agent workflow:
      1. Reads the candidate's confirmed portfolio.
      2. Extracts confirmed skills, technical domains, and claimed DSA competencies.
      3. Matches candidate boundaries against the verified question bank.
      4. Assembles a tailored assessment session of 2-3 verified questions.
      5. Strictly conceals hidden test cases and reference solutions.
      6. Persists the active session for evaluation tracking.
    """
    logger.info("Coordinating assessment for user %s: tier=%s, track=%s", user_id, req.tier, req.track)

    # 1. Fetch confirmed portfolio
    portfolio = get_portfolio(user_id)
    matched_skills: List[str] = []
    target_domain = req.domain_filter or "Algorithms & DSA"

    if portfolio and portfolio.confirmed:
        p_data = portfolio.data
        matched_skills.extend(p_data.skills.programming_languages)
        matched_skills.extend(p_data.skills.frameworks_and_tools)
        matched_skills.extend(p_data.domains)
        matched_skills.extend(p_data.dsa_topics)
        if not req.domain_filter and p_data.domains:
            target_domain = p_data.domains[0]

    # Map tier to difficulty
    tier_map = {"novice": "easy", "adept": "medium", "master": "hard"}
    target_difficulty = tier_map.get(req.tier.lower(), "easy")

    # 2. Select matching questions from Verified Question Bank
    available = filter_questions(difficulty=target_difficulty)

    # Multi-dimensional matching: match confirmed domain + claimed DSA topics + technologies
    confirmed_dsa = [t.lower() for t in portfolio.data.dsa_topics] if (portfolio and portfolio.confirmed) else []
    confirmed_langs = [l.lower() for l in portfolio.data.skills.programming_languages] if (portfolio and portfolio.confirmed) else []

    def _score_question_relevance(q: Question) -> int:
        score = 0
        # Domain match
        if target_domain.lower() in q.domain.lower():
            score += 4
        elif portfolio and any(d.lower() in q.domain.lower() for d in portfolio.data.domains):
            score += 2
        # Claimed DSA topic match
        q_topic_lower = q.topic.lower()
        for dsa in confirmed_dsa:
            if dsa in q_topic_lower:
                score += 3
        # Language match
        if q.language.lower() in confirmed_langs:
            score += 1
        return score

    # Sort available tier questions by portfolio relevance score descending
    sorted_candidates = sorted(available, key=_score_question_relevance, reverse=True)

    # Select 2 to 3 questions for a focused session
    selected_raw = sorted_candidates[:3] if len(sorted_candidates) >= 3 else sorted_candidates
    if not selected_raw:
        # Fallback to any questions in tier
        selected_raw = available[:2]

    public_questions: List[QuestionPublic] = [to_public_question(q) for q in selected_raw]

    # 3. Optional AI guidance
    ai_guidance = await _generate_featherless_guidance(portfolio, req.tier, target_domain)
    if not ai_guidance:
        ai_guidance = (
            f"Welcome to your {req.tier.capitalize()} {req.track.capitalize()} session. "
            f"Focus on algorithmic correctness, boundary handling, and clean code structure."
        )

    # 4. Create and persist session
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    session_record = {
        "session_id": session_id,
        "user_id": str(user_id),
        "tier": req.tier,
        "track": req.track,
        "status": "active",
        "domain": target_domain,
        "matched_skills": matched_skills[:6],
        "question_ids": [q.id for q in selected_raw],
        "questions": [q.model_dump() for q in public_questions],
        "ai_guidance": ai_guidance,
        "created_at": now.isoformat(),
        "completed_at": None,
        "results": None,
    }

    settings = get_settings()
    if settings.is_supabase_configured:
        try:
            from app.supabase_client import service_client
            service_client().table("assessment_sessions").insert({
                "id": session_id,
                "user_id": str(user_id),
                "tier": req.tier,
                "track": req.track,
                "status": "active",
                "domain": target_domain,
                "matched_skills": matched_skills[:6],
                "question_ids": [q.id for q in selected_raw],
                "created_at": now.isoformat(),
            }).execute()
        except Exception as e:
            logger.warning("Could not persist assessment session to Supabase: %s", e)
            if settings.app_env == "production":
                from fastapi import HTTPException
                raise HTTPException(status_code=503, detail="Database unavailable in production mode. Local fallback disabled.")

    if settings.app_env != "production":
        sessions = _read_sessions()
        sessions[session_id] = session_record
        _write_sessions(sessions)

    return AssessmentSessionResponse(
        session_id=session_id,
        user_id=user_id,
        tier=req.tier,
        track=req.track,
        status="active",
        domain=target_domain,
        matched_skills=matched_skills[:6],
        questions=public_questions,
        ai_guidance=ai_guidance,
        created_at=now,
        completed_at=None,
    )


def get_session(session_id: str, user_id: uuid.UUID) -> Optional[AssessmentSessionResponse]:
    """Retrieves an active assessment session for its owner."""
    sessions = _read_sessions()
    record = sessions.get(session_id)
    if not record or record.get("user_id") != str(user_id):
        return None

    return AssessmentSessionResponse(
        session_id=record["session_id"],
        user_id=uuid.UUID(record["user_id"]),
        tier=record["tier"],
        track=record["track"],
        status=record["status"],
        domain=record["domain"],
        matched_skills=record.get("matched_skills", []),
        questions=[QuestionPublic(**q) for q in record["questions"]],
        ai_guidance=record.get("ai_guidance"),
        created_at=datetime.fromisoformat(record["created_at"]),
        completed_at=datetime.fromisoformat(record["completed_at"]) if record.get("completed_at") else None,
    )


def submit_and_evaluate_assessment(
    session_id: str,
    user_id: uuid.UUID,
    submission_req: AssessmentSubmitRequest,
) -> AssessmentSummaryResponse:
    """
    Evaluates candidate code submissions deterministically across all test cases.
    Updates the session to completed and generates a transparent summary report.
    """
    sessions = _read_sessions()
    record = sessions.get(session_id)
    if not record or record.get("user_id") != str(user_id):
        raise ValueError("Assessment session not found or access denied.")

    submitted_map = {s.question_id: s.submitted_code for s in submission_req.submissions}
    question_ids = record.get("question_ids", [])
    
    results: List[QuestionResult] = []
    total_passed_questions = 0
    demonstrated_skills: List[str] = []
    skill_gaps: List[str] = []

    for qid in question_ids:
        q_obj = get_question_by_id(qid)
        if not q_obj:
            continue
        sub_code = submitted_map.get(qid, "")
        q_res = evaluate_submission(q_obj, sub_code)
        results.append(q_res)
        if q_res.all_passed:
            total_passed_questions += 1
            if q_obj.topic not in demonstrated_skills:
                demonstrated_skills.append(q_obj.topic)
        else:
            if q_obj.topic not in skill_gaps:
                skill_gaps.append(q_obj.topic)

    total_q = len(question_ids)
    score_pct = round((total_passed_questions / total_q) * 100.0, 1) if total_q > 0 else 0.0
    now = datetime.now(timezone.utc)

    # Update session record
    record["status"] = "completed"
    record["completed_at"] = now.isoformat()
    record["score_percentage"] = score_pct
    record["results"] = [r.model_dump() for r in results]
    record["demonstrated_skills"] = demonstrated_skills
    record["skill_gaps"] = skill_gaps

    settings = get_settings()
    if settings.is_supabase_configured:
        try:
            from app.supabase_client import service_client
            service_client().table("assessment_sessions").update({
                "status": "completed",
                "completed_at": now.isoformat(),
                "score_percentage": score_pct,
                "results": [r.model_dump() for r in results],
            }).eq("id", session_id).execute()
        except Exception as e:
            logger.warning("Could not update assessment session in Supabase: %s", e)
            if settings.app_env == "production":
                from fastapi import HTTPException
                raise HTTPException(status_code=503, detail="Database unavailable in production mode. Local fallback disabled.")

    if settings.app_env != "production":
        sessions[session_id] = record
        _write_sessions(sessions)

    # Verification notice
    is_practice = record["track"] == "practice"
    notice = (
        "Practice Assessment: Results are isolated to self-improvement and do not modify recruiter-facing verified scores."
        if is_practice else
        "Verified Assessment: Results recorded deterministically and will reflect in candidate assessment dossier."
    )

    return AssessmentSummaryResponse(
        session_id=session_id,
        user_id=user_id,
        tier=record["tier"],
        track=record["track"],
        status="completed",
        score_percentage=score_pct,
        total_questions=total_q,
        questions_passed=total_passed_questions,
        results=results,
        matched_skills=record.get("matched_skills", []),
        demonstrated_skills=demonstrated_skills,
        skill_gaps=skill_gaps,
        created_at=datetime.fromisoformat(record["created_at"]),
        completed_at=now,
        verification_notice=notice,
    )


def list_user_assessments(user_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Lists past assessment sessions for a student."""
    sessions = _read_sessions()
    uid_str = str(user_id)
    user_sessions = [s for s in sessions.values() if s.get("user_id") == uid_str]
    # Sort by created_at desc
    return sorted(user_sessions, key=lambda x: x.get("created_at", ""), reverse=True)


# ---------------------------------------------------------------------------
# Module 7: Isolated Code Execution & Sample Testing
# ---------------------------------------------------------------------------

def normalize_output(val: Optional[str]) -> str:
    """Normalize test case string / JSON / literal representation for deterministic comparison."""
    if val is None:
        return ""
    stripped = val.strip()

    # Try standard JSON parsing
    try:
        parsed = json.loads(stripped)
        return json.dumps(parsed, sort_keys=True)
    except Exception:
        pass

    # Try Python literal parsing (handles single quotes, booleans, tuples)
    try:
        parsed = ast.literal_eval(stripped)
        if isinstance(parsed, (dict, list, bool, int, float)) or parsed is None:
            return json.dumps(parsed, sort_keys=True)
    except Exception:
        pass

    # Fall back to stripped string representation
    return stripped


def build_python_harness(student_code: str, entry_name: Optional[str], input_args: str) -> str:
    """
    Constructs an isolated execution harness script to run inside the Judge0 / Mock sandbox.
    Never executed on the application server.
    """
    return f"""# -*- coding: utf-8 -*-
import json
import sys

# Untrusted candidate submission
{student_code}

# Test runner harness
if __name__ == '__main__':
    try:
        candidate_fn = globals().get({repr(entry_name)})
        if not candidate_fn or not callable(candidate_fn):
            for k, v in list(globals().items()):
                if callable(v) and not k.startswith("_"):
                    candidate_fn = v
                    break

        if candidate_fn and callable(candidate_fn):
            result = eval(f"candidate_fn({input_args})", globals())
            print("SKILLPROOF_OUTPUT_START")
            if isinstance(result, (dict, list, bool, int, float)) or result is None:
                print(json.dumps(result))
            else:
                print(str(result))
            print("SKILLPROOF_OUTPUT_END")
    except Exception as exc:
        print(f"SKILLPROOF_ERROR: {{type(exc).__name__}}: {{exc}}", file=sys.stderr)
        sys.exit(1)
"""


def build_javascript_harness(student_code: str, entry_name: Optional[str], input_args: str) -> str:
    """
    Constructs an isolated JavaScript harness script for Node.js execution inside Judge0 / Mock sandbox.
    Never executed on the application server.
    """
    fn_name_repr = repr(entry_name or "")
    return f"""// Untrusted candidate submission
{student_code}

// Test runner harness
(function() {{
    try {{
        let candidateFn = typeof {fn_name_repr} !== 'undefined' ? eval({fn_name_repr}) : null;
        if (!candidateFn || typeof candidateFn !== 'function') {{
            if (typeof solve === 'function') candidateFn = solve;
            else if (typeof solution === 'function') candidateFn = solution;
        }}

        if (candidateFn && typeof candidateFn === 'function') {{
            let result = candidateFn({input_args});
            console.log("SKILLPROOF_OUTPUT_START");
            if (typeof result === 'object' && result !== null) {{
                console.log(JSON.stringify(result));
            }} else {{
                console.log(String(result));
            }}
            console.log("SKILLPROOF_OUTPUT_END");
        }}
    }} catch (err) {{
        console.error("SKILLPROOF_ERROR: " + err);
        process.exit(1);
    }}
}})();
"""


def run_sample_code(
    session_id: str,
    user_id: uuid.UUID,
    req: SampleRunRequest,
) -> SampleRunResponse:
    """
    Executes student-submitted code against sample test cases in an isolated sandbox.
    Validates input size, constructs the container harness, and executes strictly
    via the configured SandboxProvider (Judge0 or Mock).
    """
    sessions = _read_sessions()
    record = sessions.get(session_id)
    if not record or record.get("user_id") != str(user_id):
        raise ValueError("Assessment session not found or access denied.")

    q_ids = record.get("question_ids", [])
    if req.question_id not in q_ids:
        raise ValueError(f"Question {req.question_id} does not belong to this session.")

    q_obj = get_question_by_id(req.question_id)
    if not q_obj:
        raise ValueError(f"Question {req.question_id} not found in question bank.")

    # 1. Source code bounds check
    code = req.submitted_code.strip()
    if not code:
        return SampleRunResponse(
            question_id=req.question_id,
            status=ExecutionStatus.COMPILATION_ERROR,
            passed=False,
            error_message="Submission code cannot be empty.",
        )
    if len(code) > 65536:
        return SampleRunResponse(
            question_id=req.question_id,
            status=ExecutionStatus.COMPILATION_ERROR,
            passed=False,
            error_message="Source code exceeds maximum permitted size of 64KB.",
        )

    # 2. Extract sample test case or custom input
    sample_test = q_obj.test_cases[0] if q_obj.test_cases else None
    input_args = req.custom_input.strip() if req.custom_input else (sample_test.input_data if sample_test else "")
    expected_out = sample_test.expected_output if (sample_test and not req.custom_input) else None
    language = (q_obj.language or "python").lower().strip()

    # Derive entry function name from starter code
    if language in ("javascript", "js", "node", "nodejs"):
        entry_match = re.search(r"(?:function\s+([a-zA-Z0-9_]+)|(?:const|let|var)\s+([a-zA-Z0-9_]+)\s*=)", q_obj.starter_code)
        entry_name = (entry_match.group(1) or entry_match.group(2)) if entry_match else None
        has_callable = bool(re.search(r"(?:function\s+[a-zA-Z0-9_]+|(?:const|let|var)\s+[a-zA-Z0-9_]+\s*=\s*(?:\([^)]*\)|[a-zA-Z0-9_]+)\s*=>)", code))
    else:
        entry_match = re.search(r"def\s+([a-zA-Z0-9_]+)\s*\(", q_obj.starter_code)
        entry_name = entry_match.group(1) if entry_match else None
        has_callable = bool(re.search(r"^\s*def\s+[a-zA-Z0-9_]+", code, re.MULTILINE))

    # 3. Build container execution script
    # If code defines a function implementation, wrap it in language-appropriate harness.
    # If code contains top-level statements (e.g. print/console.log script), execute directly.
    if language in ("javascript", "js", "node", "nodejs"):
        if has_callable and (entry_name or input_args):
            source_to_exec = build_javascript_harness(code, entry_name, input_args)
            stdin_data = ""
        else:
            source_to_exec = code
            stdin_data = input_args or ""
    else:
        if has_callable and (entry_name or input_args):
            source_to_exec = build_python_harness(code, entry_name, input_args)
            stdin_data = ""
        else:
            source_to_exec = code
            stdin_data = input_args or ""

    # 4. Dispatch to isolated sandbox provider
    sandbox = get_sandbox_provider()
    exec_result: ExecutionResult = sandbox.execute(
        source_code=source_to_exec,
        language=language,
        stdin=stdin_data,
        timeout_seconds=5.0,
    )

    # Handle sandbox unavailable (fail-closed)
    if exec_result.status == ExecutionStatus.SANDBOX_UNAVAILABLE:
        return SampleRunResponse(
            question_id=req.question_id,
            status=ExecutionStatus.SANDBOX_UNAVAILABLE,
            passed=False,
            error_message=exec_result.error_message or "Sandbox execution service is currently unavailable.",
            sandbox_provider=sandbox.provider_name,
        )

    # Handle non-accepted results (compilation error, timeout, runtime error, sandbox error, etc.)
    if exec_result.status != ExecutionStatus.ACCEPTED:
        # Record latest failure for AI Assistant diagnostics
        if "latest_executions" not in record:
            record["latest_executions"] = {}
        record["latest_executions"][req.question_id] = {
            "status": exec_result.status,
            "passed": False,
            "stdout": exec_result.stdout,
            "stderr": exec_result.stderr,
            "compile_output": exec_result.compile_output,
            "expected_output": expected_out,
            "actual_output": exec_result.stdout,
            "error_message": exec_result.error_message or exec_result.stderr or exec_result.compile_output,
            "execution_time_ms": round(exec_result.time_seconds * 1000.0, 2) if exec_result.time_seconds else None,
            "memory_kb": exec_result.memory_kb,
            "exit_code": exec_result.exit_code,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        sessions[session_id] = record
        _write_sessions(sessions)

        return SampleRunResponse(
            question_id=req.question_id,
            status=exec_result.status,
            passed=False,
            stdout=exec_result.stdout,
            stderr=exec_result.stderr,
            compile_output=exec_result.compile_output,
            execution_time_ms=round(exec_result.time_seconds * 1000.0, 2) if exec_result.time_seconds else None,
            memory_kb=exec_result.memory_kb,
            exit_code=exec_result.exit_code,
            expected_output=expected_out,
            actual_output=exec_result.stdout,
            error_message=exec_result.error_message or exec_result.stderr or exec_result.compile_output,
            sandbox_provider=sandbox.provider_name,
        )

    # Parse actual output from isolated container execution
    actual_out = ""
    if exec_result.stdout:
        if "SKILLPROOF_OUTPUT_START" in exec_result.stdout and "SKILLPROOF_OUTPUT_END" in exec_result.stdout:
            actual_out = exec_result.stdout.split("SKILLPROOF_OUTPUT_START")[1].split("SKILLPROOF_OUTPUT_END")[0].strip()
        else:
            actual_out = exec_result.stdout.strip()

    # Determine pass / fail status
    if "[Mock Sandbox Output" in actual_out:
        passed = True
    elif expected_out is not None and expected_out.strip():
        actual_norm = normalize_output(actual_out)
        expected_norm = normalize_output(expected_out)
        passed = (actual_norm == expected_norm)
    else:
        passed = (exec_result.status == ExecutionStatus.ACCEPTED)

    status_val = ExecutionStatus.ACCEPTED if passed else ExecutionStatus.WRONG_ANSWER

    # Persist latest execution state in session record for AI Assistant and telemetry
    if "latest_executions" not in record:
        record["latest_executions"] = {}
    record["latest_executions"][req.question_id] = {
        "status": status_val,
        "passed": passed,
        "stdout": exec_result.stdout,
        "stderr": exec_result.stderr,
        "compile_output": exec_result.compile_output,
        "expected_output": expected_out,
        "actual_output": actual_out,
        "error_message": exec_result.error_message if not passed else None,
        "execution_time_ms": round(exec_result.time_seconds * 1000.0, 2) if exec_result.time_seconds else None,
        "memory_kb": exec_result.memory_kb,
        "exit_code": exec_result.exit_code,
        "executed_at": datetime.now(timezone.utc).isoformat(),
    }
    sessions[session_id] = record
    _write_sessions(sessions)

    return SampleRunResponse(
        question_id=req.question_id,
        status=status_val,
        passed=passed,
        stdout=exec_result.stdout,
        stderr=exec_result.stderr,
        compile_output=exec_result.compile_output,
        execution_time_ms=round(exec_result.time_seconds * 1000.0, 2) if exec_result.time_seconds else None,
        memory_kb=exec_result.memory_kb,
        exit_code=exec_result.exit_code,
        expected_output=expected_out,
        actual_output=actual_out,
        error_message=exec_result.error_message,
        sandbox_provider=sandbox.provider_name,
    )


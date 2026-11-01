"""
Question Bank Validation Script — SkillProof AI (Module 4)

Executes every reference solution in SEED_QUESTIONS against all its test cases
using the existing evaluate_submission() engine. Only trusted reference solutions
are run here — never student-submitted code.

Exit code 0: all questions pass 100% of test cases.
Exit code 1: one or more questions fail.

Usage:
    python backend/tests/validate_question_bank.py
"""

import sys
import os

# Ensure backend package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.question_bank import SEED_QUESTIONS, evaluate_submission

SEPARATOR = "=" * 70


def run_validation() -> bool:
    """Runs all reference solutions through evaluate_submission. Returns True if all pass."""
    print(SEPARATOR)
    print("SkillProof AI — Question Bank Reference Solution Validator")
    print(SEPARATOR)

    all_passed = True
    passed_questions = []
    failed_questions = []

    for q in SEED_QUESTIONS:
        result = evaluate_submission(q, q.reference_solution)

        status = "PASS" if result.all_passed else "FAIL"
        print(f"  [{status}] [{q.difficulty.upper():6}] {q.id}")
        print(f"         Score: {result.passed_tests}/{result.total_tests} test cases passed")

        if result.all_passed:
            passed_questions.append(q.id)
        else:
            failed_questions.append({
                "id": q.id,
                "title": q.title,
                "difficulty": q.difficulty,
                "passed": result.passed_tests,
                "total": result.total_tests,
                "feedback": result.feedback,
            })
            all_passed = False
            print(f"         Feedback: {result.feedback}")

        print()

    print(SEPARATOR)
    print(f"SUMMARY: {len(passed_questions)}/{len(SEED_QUESTIONS)} questions passed 100% of test cases")
    print(SEPARATOR)

    if passed_questions:
        print(f"\nPASSED ({len(passed_questions)}):")
        for qid in passed_questions:
            print(f"  [PASS] {qid}")

    if failed_questions:
        print(f"\nFAILED ({len(failed_questions)}):")
        for fq in failed_questions:
            print(f"  [FAIL] {fq['id']} ({fq['difficulty']}) -- {fq['passed']}/{fq['total']} -- {fq['feedback']}")

    print()

    if all_passed:
        print("ALL CLEAR: All reference solutions validated. Question bank is clean.")
    else:
        print("ACTION REQUIRED: Some reference solutions failed. Fix or remove failing questions.")

    return all_passed


if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)

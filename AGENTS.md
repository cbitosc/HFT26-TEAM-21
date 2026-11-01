# SkillProof AI — Development Instructions & Agent Guidelines

> **Document Type:** Developer and AI Agent Operating Guidelines  
> **Target System:** SkillProof AI  
> **Source of Truth (Architecture & Features):** [`PROJECT_REQUIREMENTS.md`](file:///C:/Users/vignesh/OneDrive/Desktop/SkillProofAI/PROJECT_REQUIREMENTS.md)  
> **Source of Truth (Development Progress):** [`PROJECT_STATUS.md`](file:///C:/Users/vignesh/OneDrive/Desktop/SkillProofAI/PROJECT_STATUS.md)  
> **Target Audience:** All AI Coding Assistants & Contributing Developers  

---

## 1. Project Context

You are working on **SkillProof AI**, an AI-assisted, Portfolio-Driven Adaptive Coding & Technical Assessment Platform designed to evaluate software engineering candidates based on verified technical ability, problem-solving methodologies, and project experience.

- [`PROJECT_REQUIREMENTS.md`](file:///C:/Users/vignesh/OneDrive/Desktop/SkillProofAI/PROJECT_REQUIREMENTS.md) is the **primary source of truth** for all project functionality, architecture, design constraints, and evaluation rules.
- [`PROJECT_STATUS.md`](file:///C:/Users/vignesh/OneDrive/Desktop/SkillProofAI/PROJECT_STATUS.md) is the **official source of truth** for real-time development progress, module states, pending tasks, and test verification.
- **Mandatory Starting Step:** Always read both [`PROJECT_REQUIREMENTS.md`](file:///C:/Users/vignesh/OneDrive/Desktop/SkillProofAI/PROJECT_REQUIREMENTS.md) and [`PROJECT_STATUS.md`](file:///C:/Users/vignesh/OneDrive/Desktop/SkillProofAI/PROJECT_STATUS.md) completely before planning or implementing any task or module.

---

## 2. Development Approach

- **One Module at a Time:** Focus exclusively on the current module in sequence. Never begin work on the next module until the active module is completed and verified.
- **Follow the 13-Module Roadmap:** Adhere strictly to the established 13-module progression plan across all four phases.
- **No Premature Implementation:** Do not create placeholders, stub functions, or partial implementations for future modules ahead of their phase.
- **No Unapproved Requirement Deviations:** Do not skip, alter, or add requirements without explicit discussion and developer approval.
- **Complete Before Transitioning:** Mark a module completed only after its features are fully functional and pass tests.
- **Simplicity and Reusability:** Favor simple, clean, maintainable, and reusable solutions over over-engineered patterns.
- **Working End-to-End Priority:** Always prioritize a working, cohesive end-to-end flow over unnecessary peripheral complexity.

---

## 3. Beginning Every Task

Before generating code or implementing any feature, perform the following 7-step inspection routine:

1. **Read Requirements:** Read [`PROJECT_REQUIREMENTS.md`](file:///C:/Users/vignesh/OneDrive/Desktop/SkillProofAI/PROJECT_REQUIREMENTS.md) to understand expected behavior, boundaries, and specifications.
2. **Read Status:** Read [`PROJECT_STATUS.md`](file:///C:/Users/vignesh/OneDrive/Desktop/SkillProofAI/PROJECT_STATUS.md) to verify current project state and prerequisites.
3. **Inspect Directory Structure:** Examine current workspace files and directories to ensure proper context.
4. **Inspect Existing Code:** Review relevant existing components, routes, utilities, and models to maintain consistency.
5. **Identify Relevant Requirements:** Isolate the exact subset of requirements that apply directly to the requested task.
6. **Explain Implementation Plan:** Present a concise, clear outline of what will be implemented and why before writing code.
7. **Identify Missing Configs & Dependencies:** Explicitly flag any required environment variables, third-party credentials, or missing packages before proceeding.

> **Rule:** Never duplicate existing functionality or re-create utilities that are already present in the codebase.

---

## 4. Coding Standards

- **Clean and Readable Code:** Write clear, self-explanatory code with logical flow and consistent formatting.
- **Descriptive Naming:** Use clear, intention-revealing names for all files, functions, classes, components, and variables.
- **Idiomatic Conventions:** Follow the established idioms and best practices of each technology (FastAPI/PEP 8 for Python; Vite/ESLint/Hooks for React).
- **Modular Component Design:** Build reusable, well-encapsulated React components with distinct separation of UI and business logic.
- **Strict Separation of Concerns:** Maintain a clean boundary between frontend presentation and backend API logic.
- **Robust Error Handling:** Wrap network requests, file parsing, and data queries in graceful error handling with informative feedback.
- **Strict Input Validation:** Validate and sanitize all user inputs, payloads, and file uploads (using Pydantic models on backend and schema validation on frontend).
- **Lean Dependencies:** Avoid installing external packages for functionality that can be cleanly achieved with standard libraries.
- **Zero Hardcoded Secrets:** Never hardcode API keys, passwords, database URLs, or sensitive tokens; always load them via environment variables.
- **No Deceptive Placeholders:** Never generate mock buttons, fake loading states, or dummy data that appears functional while concealing missing backend integration.

---

## 5. AI and Featherless AI Rules

- **Justified AI Usage:** Leverage Featherless AI exclusively for tasks that genuinely require language intelligence (e.g., portfolio semantic parsing, guided hint generation, adaptive question framing).
- **Availability Verification:** Never assume an AI model is operational without verifying its endpoint status and rate limits.
- **Model Compatibility:** Confirm model capabilities, context window sizes, and API parameter compatibility before integrating.
- **Structured JSON Schema:** Require structured JSON responses validated against strict Pydantic models for all AI outputs.
- **Output Validation:** Treat all LLM outputs as untrusted input; validate structure and content before passing data to downstream services.
- **Token Optimization:** Design concise, bounded system prompts to minimize latency, conserve quota, and lower token costs.
- **Comprehensive Fault Tolerance:** Implement resilient handling for API timeouts, rate-limit exceptions (HTTP 429), server errors (HTTP 5xx), and unexpected payload shapes.
- **Frontend Key Shielding:** Never expose Featherless AI credentials or private API keys in client-side bundles or frontend network requests.
- **Configurable Provider Architecture:** Decouple AI services behind an interface/adapter pattern to allow seamless model or provider switching.
- **Verified Bank Fallback:** If Featherless AI becomes unreachable or rate-limited, immediately fall back to the curated question bank without interrupting the user.
- **Absolute Grading Rule:** **Never allow an LLM to independently evaluate or assign grades to candidate code submissions.**

---

## 6. Assessment Reliability

- **Prioritize Verified Questions:** Curated, pre-verified questions from the bank are the primary source of truth; dynamically generated questions are strictly secondary.
- **Respect Skill Boundaries:** Strictly confine questions to the candidate's confirmed portfolio domains and claimed DSA topics.
- **Mandatory Question Validation:** Every dynamically generated question must pass automated validation (compilation check, reference solution execution against test cases) before being served.
- **Zero Blind Trust in AI Test Cases:** Never assume AI-authored test suites or expected outputs are correct without empirical execution.
- **100% Deterministic Grading:** Code evaluations must be based solely on automated test assertions, standard output validation, and exit code verification.
- **Shield Sensitive Test Data:** Hidden evaluation test cases and reference solutions must never be exposed to frontend code or client responses.
- **Conceal Solutions from Assistant:** The AI coding assistant must never be supplied with reference solutions in its prompt context.
- **Isolated Execution Sandboxing:** Untrusted candidate code must run exclusively in an isolated, sandboxed environment (e.g., Judge0) with strict memory, CPU, and networking constraints.

---

## 7. Security and Privacy

- **Backend-Enforced Authorization:** Enforce role-based access control (RBAC) at FastAPI route dependencies and Supabase Row-Level Security (RLS) policies—never rely solely on UI route guards.
- **Data Protection:** Safeguard student submissions, assessment metrics, and recruiter evaluation notes.
- **Secure Authentication:** Use industry-standard session management, encrypted cookies, and signed JWTs via Supabase Auth.
- **Safe File Upload Processing:** Restrict uploads to approved extensions (`.json`, `.pdf`, `.docx`), enforce file size limits, and scan for malicious input.
- **Secure Secret Storage:** Keep all API keys, service role credentials, and database connection strings in `.env` files; ensure `.env` is ignored by Git.
- **Zero Credential Commits:** Never commit actual secrets or test credentials to source control.
- **Explicit Recruiter Consent:** Recruiter access to a candidate's portfolio dossier and assessment history requires explicit, revocable student permission.
- **Fair Telemetry Interpretation:** Do not interpret raw paste actions or editing cadences as definitive evidence of cheating; use CodeTrace purely as constructive evidence of problem solving.

---

## 8. Testing Requirements

After implementing any feature or module:

1. **Execute Tests:** Run relevant unit, integration, or end-to-end tests across modified components.
2. **Log Verification:** Check terminal and browser consoles for unhandled errors, warnings, or promise rejections.
3. **Verify Expected Behavior:** Manually exercise the happy path to confirm functionality matches requirements.
4. **Test Edge Cases & Failure Scenarios:** Test invalid inputs, network failures, empty states, and unauthorized access attempts.
5. **Regression Verification:** Verify that existing features and previously passing tests continue to function properly.
6. **Report Limitations Honestly:** Explicitly document any edge cases, untested paths, or incomplete aspects in the task summary.

> **Rule:** Never claim a feature is complete merely because code files were created or modified without runtime verification.

---

## 9. Project Status Management

After completing any meaningful implementation task or module milestone:

- **Update [`PROJECT_STATUS.md`](file:///C:/Users/vignesh/OneDrive/Desktop/SkillProofAI/PROJECT_STATUS.md):**
  - Record completed features with specific details.
  - Record any newly identified pending tasks or requirements.
  - Document all known issues, limitations, or edge cases.
  - Update testing status (`Untested`, `In Progress`, `Passed`, `Failed`).
- **No False Completions:** Never mark a module or feature as `COMPLETED` unless it has been implemented, integrated, and verified through testing.
- **Preserve Progress History:** Preserve historical changelog records and completed items when updating [`PROJECT_STATUS.md`](file:///C:/Users/vignesh/OneDrive/Desktop/SkillProofAI/PROJECT_STATUS.md).
- **Requirements Immutability:** Never modify [`PROJECT_REQUIREMENTS.md`](file:///C:/Users/vignesh/OneDrive/Desktop/SkillProofAI/PROJECT_REQUIREMENTS.md) unless the user explicitly approves an architectural or functional change.

---

## 10. Explanation Requirements

> **Context:** The developer is a beginner learning modern full-stack development and AI agent engineering.

After every implementation step, provide an explanation structured with:

- **What Was Created:** A clear, high-level summary of the new feature or component.
- **Files Modified/Created:** A complete list of changed files with clickable links.
- **File Roles & Responsibilities:** A plain-language explanation of what each important file does.
- **How It Works:** A step-by-step description of data flow, logic, and component interaction.
- **How to Run & Test It:** Exact commands and instructions for running and verifying the feature locally.
- **Remaining Incomplete Work:** A clear statement of what is still pending.
- **Technical Concepts Explained:** Brief explanations of any important design patterns, libraries, or architectural concepts used.

> **Style Guideline:** Use accessible, encouraging, beginner-friendly language while preserving technical accuracy.

---

## 11. Budget Constraints

SkillProof AI is designed with a strict **zero-cost / free-tier first** philosophy.

Before recommending, integrating, or configuring any external service:
- **Verify Free-Tier Status:** Confirm that a genuine free tier is currently available.
- **Identify Usage Quotas:** Document exact rate limits, monthly request caps, storage limits, and compute restrictions.
- **Payment Method Disclosure:** Explicitly check and disclose whether signing up requires a credit card or payment method.
- **Transparent Trade-Offs:** Honestly state service trade-offs and performance limitations under free tiers.
- **No Automatic Charges:** Never activate paid tiers, incur cloud charges, or suggest paid subscriptions without explicit user authorization.

---

## 12. Change Control

- **File Preservation:** Do not delete existing files or directories without explicit approval.
- **Configuration Protection:** Do not overwrite existing configuration files (`.env`, `package.json`, `tsconfig.json`) without inspecting them first.
- **Tech Stack Stability:** Do not alter the technology stack (React, Vite, Tailwind, Monaco, FastAPI, Supabase, Featherless AI, LangGraph, Judge0) without explicit authorization.
- **Scope Discipline:** Do not introduce unrequested features or unnecessary architectural layers.
- **Consult on Architectural Shifts:** Ask for clarification before altering database schemas, authentication workflows, or agent routing.
- **Preserve Working Baseline:** Guarantee that working functionality is never broken by opportunistic refactoring.

---

## 13. Final Task Report

At the conclusion of each module, generate a structured closing report containing:

1. **Module Identification:** Module number and official name.
2. **Features Implemented:** Bulleted breakdown of all functional additions.
3. **Files Created or Modified:** Complete file roster with clickable links.
4. **Tests Performed & Results:** Test scenarios executed, assertions validated, and empirical results.
5. **Known Issues & Limitations:** Any edge cases, rate limits, or pending configurations.
6. **Remaining Work:** Pending items required before marking the module finalized.
7. **`PROJECT_STATUS.md` Confirmation:** Verification that [`PROJECT_STATUS.md`](file:///C:/Users/vignesh/OneDrive/Desktop/SkillProofAI/PROJECT_STATUS.md) was updated.

> **Rule:** Always stop and wait for the developer's explicit instruction before starting another module.

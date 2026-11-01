# SkillProof AI

> **Prove Your Skills. Showcase Your Ability.**

SkillProof AI is an AI-assisted, **Portfolio-Driven Adaptive Coding & Technical Assessment Platform** engineered to evaluate software engineering candidates on verified practical ability, problem-solving methodologies, and project experience rather than simple test completion counts.

---

## Table of Contents
1. [Project Title](#1-project-title)
2. [Project Overview](#2-project-overview)
3. [Problem Statement](#3-problem-statement)
4. [Key Features](#4-key-features)
5. [User Roles](#5-user-roles)
6. [Technology Stack](#6-technology-stack)
7. [AI Architecture](#7-ai-architecture)
8. [Development Roadmap](#8-development-roadmap)
9. [Project Structure](#9-project-structure)
10. [Setup and Configuration](#10-setup-and-configuration)
11. [Project Status](#11-project-status)
12. [Future Improvements](#12-future-improvements)

---

## 1. Project Title

- **Project Name:** SkillProof AI
- **Tagline:** *Prove Your Skills. Showcase Your Ability.*
- **Classification:** Portfolio-Driven Adaptive Coding & Technical Assessment Platform

---

## 2. Project Overview

Traditional technical evaluations typically rely on rote algorithmic puzzles, multiple-choice quizzes, or question-count leaderboards that fail to capture a candidate's actual engineering capabilities.

**SkillProof AI** introduces a portfolio-driven paradigm:
- **Verified Practical Competence:** Assessments are derived from the candidate's verified projects, confirmed technologies, and claimed Computer Science / Data Structures & Algorithms (DSA) competencies.
- **Problem-Solving Over Rote Memorization:** Candidates are evaluated on how they design, debug, test, and adapt code under realistic constraints.
- **Deterministic and Fair:** Grading is 100% deterministic through automated test suites and sandboxed execution. AI never independently grades student submissions.

---

## 3. Problem Statement

### Limitations of Traditional Assessments
- **Disconnect from Real-World Engineering:** Memorizing esoteric algorithmic tricks does not reflect day-to-day software development, API design, or debugging skills.
- **Resume and Portfolio Inflation:** Candidates frequently list technologies on resumes that they have only superficial exposure to; recruiters lack efficient tools to verify claimed experience.
- **Binary Grading Without Context:** Traditional platforms record pass/fail results but discard the candidate's thought process, architectural choices, and debugging iterations.
- **Opaque or Biased AI Grading:** Emerging automated systems that delegate code grading directly to generative LLMs suffer from non-deterministic evaluations, hallucinations, and scoring inconsistencies.

### The SkillProof AI Solution
SkillProof AI anchors assessments in **confirmed portfolio evidence**. By analyzing student project artifacts, the platform generates bounded, adaptive technical challenges tailored to the candidate's actual domain experience, evaluates results deterministically in isolated sandboxes, and captures a comprehensive coding journey timeline for verified recruiter review.

---

## 4. Key Features

- **Portfolio Upload and Analysis:** Ingests project dossiers (`.json`, `.pdf`, `.docx`), extracts claimed skills, technologies, and DSA topics, and standardizes them into structured JSON with mandatory student verification.
- **Personalized Coding Assessments:** Generates adaptive, skill-bounded challenges across three tiers (**Novice**, **Adept**, **Master**) matching the candidate's verified profile.
- **Easy, Medium and Hard Practice:** Dedicated non-evaluative practice environment with strict score isolation from verified recruiter-facing dossiers.
- **Verified Question Bank:** Curated, pre-verified seed repository of 30–50 domain-specific questions with benchmark reference solutions and unit test suites.
- **AI-Powered Hints and Debugging Assistance:** Progressive, guarded assistance powered by Featherless AI (conceptual tips, syntax clarifications, debugging guidance) with reference solutions strictly shielded.
- **Deterministic Code Evaluation:** Sandboxed code execution with automated test assertions, standard output validation, and runtime limit enforcement.
- **Coding Journey Tracking:** CodeTrace telemetry capturing code diffs, timestamps, and test attempts with student consent, visualized as a constructive problem-solving timeline.
- **Performance Analytics:** Multidimensional analytics powered by Recharts, tracking domain mastery, test resilience, and deterministic AI usage efficiency (capped at 20%).
- **College Assessment Management:** Cohort and batch administration, department-specific assessment authoring, task assignment, and academic progress monitoring.
- **Recruiter Portal:** Candidate discovery filtered by demonstrated technical proof and consent-governed assessment dossier inspection.
- **Live Collaborative Coding Interviews:** Interactive live pair-coding workspace supporting dynamic requirement updates, prompt refactoring, and real-time execution.

---

## 5. User Roles

The platform provides dedicated, backend-authorized experiences for three primary user archetypes:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Role-Based Capabilities                         │
├────────────────────┬─────────────────────────────┬─────────────────────┤
│      Student       │    College Administrator    │ Verified Recruiter  │
├────────────────────┼─────────────────────────────┼─────────────────────┤
│ • Portfolio upload │ • Cohort & batch management │ • Proof-based search│
│ • Adaptive tests   │ • Custom assessment authoring│ • Consent dossier  │
│ • Practice portal  │ • Department task assignment│   inspection        │
│ • Guarded AI help  │ • Deadline enforcement      │ • Live collaborative│
│ • Analytics graphs │ • Academic performance stats│   coding interviews │
└────────────────────┴─────────────────────────────┴─────────────────────┘
```

1. **Student:** Enrolls, uploads projects, confirms portfolio schema, completes verified or practice challenges, and shares verified assessment results with recruiters.
2. **College Administrator:** Manages academic cohorts, designs curriculum-aligned assessments, assigns challenges with deadlines, and monitors batch performance.
3. **Verified Recruiter:** Discovers talent based on empirical skill proofs, inspects candidate CodeTrace timelines with explicit consent, and conducts live collaborative coding interviews.

---

## 6. Technology Stack

| Layer | Technology | Role & Purpose |
| :--- | :--- | :--- |
| **Frontend** | React (Vite) + Tailwind CSS | High-performance, responsive single-page client interface |
| **Code Workspace** | Monaco Editor | In-browser professional coding environment with syntax tooling |
| **Analytics** | Recharts | Declarative charts for performance tracking and skill mastery |
| **Backend API** | Python + FastAPI | Asynchronous REST endpoints, business logic, and agent orchestration |
| **Database & Auth** | Supabase | Managed PostgreSQL, Row-Level Security (RLS), and JWT authentication |
| **AI LLM Inference** | Featherless AI API | High-throughput language intelligence for assistance and question framing |
| **Agent Workflow** | LangGraph | Stateful multi-step agent orchestration and validation pipelines |
| **Code Sandboxing** | Judge0 (or isolated service) | Containerized, secure, multi-language code execution engine |
| **Source Control** | Git & GitHub | Version management, issue tracking, and collaborative development |

---

## 7. AI Architecture

SkillProof AI enforces strict separation between generative AI assistance and deterministic code evaluation:

```
┌────────────────────────────────────────────────────────────────────────┐
│                    SkillProof AI Agent Architecture                    │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   [Student Portfolio] ───► [LangGraph Coordinator Agent]               │
│                                      │                                 │
│                   ┌──────────────────┴──────────────────┐              │
│                   ▼                                     ▼              │
│      [Verified Question Bank]               [Featherless AI Engine]    │
│         (Primary Source)                   (Specialized Generation)   │
│                   │                                     │              │
│                   │                                     ▼              │
│                   │                          [TrustGuard Validator]    │
│                   │                         (Empirical Self-Test)      │
│                   │                                     │              │
│                   └──────────────────┬──────────────────┘              │
│                                      ▼                                 │
│                         [Assessment Coding Workspace]                  │
│                                      │                                 │
│                                      ▼                                 │
│                       [Deterministic Test Engine (Judge0)]             │
│                                      │                                 │
│                                      ▼                                 │
│                          [Final Performance Report]                    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

- **SkillProof AI Agent (LangGraph):** Coordinates portfolio analysis, domain boundary checks, question selection, and generation workflows.
- **Featherless AI:** Supplies language intelligence for semantic portfolio parsing, guarded progressive hints, and adaptive question generation.
- **Verified Question Bank:** Acts as the primary, trusted source of pre-validated algorithmic and domain challenges.
- **TrustGuard:** Automated gatekeeper that validates generated questions by executing reference solutions against test suites before candidate exposure.
- **Deterministic Test Engine:** Sandboxed execution runner that evaluates code correctness strictly against unit assertions. **Generative models never assign grades.**

---

## 8. Development Roadmap

Development follows a strict 13-module progression plan divided across four phases:

### Phase 1: Foundation
- **Module 1:** Project Setup and Application Foundation
- **Module 2:** Authentication and Role-Based Dashboards
- **Module 3:** Portfolio Upload and JSON Conversion

### Phase 2: Assessment Intelligence
- **Module 4:** Verified Question Bank
- **Module 5:** SkillProof AI Assessment Agent
- **Module 6:** Assessment and Skill-Improvement Pages
- **Module 7:** Coding Workspace and Deterministic Grading
- **Module 8:** CodeTrace Coding Journey

### Phase 3: Assistance and Analytics
- **Module 9:** AI Coding Assistant
- **Module 10:** Performance Analytics and Scoring

### Phase 4: Organization and Recruiting
- **Module 11:** College Task Management
- **Module 12:** Recruiter Portal and Live Interviews
- **Module 13:** Integration, Security and Deployment

---

## 9. Project Structure

```text
SkillProofAI/
├── frontend/                   # React 18 + Vite + TypeScript + Tailwind CSS application
│   ├── public/                 # Static assets (favicons, icons)
│   ├── src/
│   │   ├── components/         # Reusable UI components (Navbar, Footer, Button, Input, Alert, ProtectedRoute)
│   │   ├── config/             # Client environment configuration
│   │   ├── contexts/           # AuthContext managing Supabase sessions and authoritative profiles
│   │   ├── lib/                # Supabase client initialization
│   │   ├── pages/              # Route pages (Landing, Login, Register, Forgot/Reset Password, Dashboards)
│   │   │   └── dashboards/     # Role-specific workspaces (Student, College Admin, Recruiter, Status notices)
│   │   ├── services/           # Backend API integration client
│   │   └── types/              # TypeScript interfaces for auth, roles, and profiles
│   ├── .env.example            # Frontend environment template
│   └── package.json
├── backend/                    # Python + FastAPI backend service
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/         # Endpoint routers (health, auth, colleges, requests, admin)
│   │   │   └── deps.py         # JWT verification, role enforcement, platform admin authorization
│   │   ├── config.py           # Application settings and Supabase configuration
│   │   ├── main.py             # FastAPI entrypoint and CORS middleware
│   │   ├── models.py           # Pydantic schemas for auth, profiles, and verification requests
│   │   └── supabase_client.py  # Supabase client factories (anon vs. service_role)
│   ├── tests/                  # Automated integration test suite
│   │   ├── test_auth_api.py    # Pytest integration tests for auth and authorization
│   │   └── run_tests.py        # Standalone direct test runner
│   ├── .env.example            # Backend environment template
│   └── requirements.txt
├── supabase/                   # Supabase database configurations
│   └── migrations/
│       └── 001_auth_and_profiles.sql  # Database schema, RLS, triggers, and approval functions
├── docs/                       # Architectural specifications
│   └── MODULE_2_AUTHENTICATION_ARCHITECTURE.md
├── .env.example                # Unified environment template
├── .gitignore                  # Git exclusions for secrets, builds, and dependencies
├── AGENTS.md                   # Permanent AI agent development guidelines
├── PROJECT_REQUIREMENTS.md     # Official system requirements and specifications
├── PROJECT_STATUS.md           # Real-time development progress tracker
└── README.md                   # Project overview and documentation
```

---

## 10. Setup and Configuration

### Prerequisites
- **Node.js:** v18+ and `npm`
- **Python:** v3.11+ (Python 3.14 virtual environment configured in `backend/venv`)
- **Supabase Account:** Free tier at [database.new](https://database.new)

### 1. Database Setup (Supabase)
1. Create a free project at [database.new](https://database.new) named `skillproof-ai`.
2. Open the **SQL Editor** in the Supabase Dashboard.
3. Paste and run the migration script: [`supabase/migrations/001_auth_and_profiles.sql`](file:///C:/Users/vignesh/OneDrive/Desktop/SkillProofAI/supabase/migrations/001_auth_and_profiles.sql).
4. Retrieve credentials from **Project Settings → API**:
   - Project URL (`https://<project-ref>.supabase.co`)
   - `anon` / public key
   - `service_role` key (backend only)

### 2. Backend Setup
```powershell
# Navigate to backend directory
cd backend

# Create and activate virtual environment (if needed)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit backend/.env and populate SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY

# Run automated tests
python tests/run_tests.py

# Start FastAPI backend server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Setup
```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env
# Edit frontend/.env and populate VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY

# Run production build check
npm run build

# Start Vite development server
npm run dev
```

---

## 11. Project Status

- **Current Stage:** Module 2 (Authentication and Role-Based Dashboards) Implemented & Verified
- **Application Code:** Functional React frontend and FastAPI backend with comprehensive auth routing, protected workspaces, and database security architecture.
- **Active Tracker:** See [`PROJECT_STATUS.md`](file:///C:/Users/vignesh/OneDrive/Desktop/SkillProofAI/PROJECT_STATUS.md) for live module states and upcoming tasks.
- **Operating Guidelines:** See [`AGENTS.md`](file:///C:/Users/vignesh/OneDrive/Desktop/SkillProofAI/AGENTS.md) for full development protocols.
- **Source of Truth:** See [`PROJECT_REQUIREMENTS.md`](file:///C:/Users/vignesh/OneDrive/Desktop/SkillProofAI/PROJECT_REQUIREMENTS.md) for complete technical requirements.

---

## 12. Future Improvements

The following capabilities are planned for prospective future iterations and are **not yet implemented**:
- **Multi-File Workspace Projects:** Support for complex full-stack repositories with multi-file refactoring tasks.
- **Expanded Execution Runtimes:** Additional programming language kernels and framework sandboxes (e.g., Rust, Go, Java).
- **Automated Peer Review Simulations:** Multi-agent simulated code review providing constructive feedback on code readability and structure.
- **Enterprise LMS Integrations:** LTI compliance for seamless integration with university Learning Management Systems (Canvas, Blackboard, Moodle).
- **Offline / Local Sandbox Runners:** Optional local Docker-based execution runners for air-gapped institutional environments.

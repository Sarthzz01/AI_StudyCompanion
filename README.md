# 🎓 AI Study Companion

<div align="center">

![AI Study Companion Banner](https://img.shields.io/badge/AI%20Study%20Companion-v1.0.0-6366f1?style=for-the-badge&logo=openai&logoColor=white)

**An intelligent, multi-modal, adaptive academic learning & assessment platform powered by FastAPI, React 18, and modern LLMs.**  
*Personalized AI Tutoring • RAG-Grounded Material Q&A • Active Recall Flashcards • Adaptive Quizzes • Smart Summaries & PDF Parser • Viva Voce Oral Defense • Instructor Analytics & Assessment Management*

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React_18-20232A?style=flat-square&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite_5-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS_3-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy_2.0-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

[Key Features](#-key-features) • [System Architecture](#-system-architecture) • [Tech Stack](#-technology-stack) • [Quick Start](#-quick-start-guide) • [Default Test Accounts](#-default-test-accounts) • [API Catalog](#-api-endpoints-reference) • [Project Report](#-comprehensive-project-report)

---

</div>

## 🌟 Overview

**AI Study Companion** bridges the gap between passive content consumption and active, verified learning. It empowers students with AI-grounded tutoring, automated summaries, active recall flashcards, oral defense simulations, and adaptive testing—while providing instructors with complete classroom analytics, assessment builders, and assignment dispatch mechanisms.

Built with a high-performance **FastAPI** backend and a responsive **React 18 + TailwindCSS** frontend, the platform integrates **Retrieval-Augmented Generation (RAG)**, multi-provider LLM intelligence (**OpenAI GPT-4o-mini** and **Google Gemini 2.5 Flash**), and a 24-table **SQLAlchemy** relational schema.

---

## 🚀 Key Features

### 🧑‍🎓 Student Learning Hub

1. **🧠 Intelligent RAG-Grounded AI Tutor (`/tutor`)**
   - **Multi-Turn Contextual Memory**: Engages in deep academic discussions with full memory of recent questions and explanations.
   - **Grounded Document Retrieval**: Answers link directly to uploaded textbooks, lecture notes, or slides with exact page numbers and snippet citations.
   - **Semantic Topic Detection**: Derives concise, 3–5 word semantic titles for chat sessions based on conversational intent.
   - **Inline Thread Management**: Rename, delete, and search conversation threads directly from the sidebar.

2. **📚 Study Material Ingestion & Processing (`/materials`)**
   - Upload course materials in PDF, Markdown, or raw text format.
   - Automated PyPDF text extraction, cleaning, and sliding-window chunking.
   - Cascading deletion with vector cleanup and read-progress tracking.

3. **📄 Smart Summaries & Dynamic PDF Parser (`/summaries`)**
   - **Dual Source Input**: Generate summaries from existing library materials or directly upload any external PDF on the fly.
   - **Structured Knowledge Extraction**: Produces Executive Summaries, Key Takeaways, Core Concepts, Critical Formulas, and Practical Applications.
   - **PDF Report Export**: One-click download of the generated summary as a clean, professionally formatted PDF document.

4. **⚡ Active Recall Flashcards & Spaced Repetition (`/flashcards`)**
   - AI generates customized question-and-answer flashcard decks tailored to key concepts.
   - 3D card-flip interaction with confidence ratings (`Easy`, `Medium`, `Hard`).
   - Updates student topic mastery scores dynamically to schedule optimal review intervals.

5. **🎯 Quizzes & Evaluations Dual Engine (`/quizzes`)**
   - **Tab 1 — Assigned Assessments**:
     - View instructor-assigned evaluations with due dates, maximum points, time limits, and instructions.
     - Live status badges: `Pending`, `Passed`, or `Needs Review`.
     - Direct exam runner (`/quizzes/:id?assessment=...`) that automatically calculates scores, updates learner records, and submits results to the instructor.
   - **Tab 2 — Self-Study Practice Quizzes**:
     - On-demand quiz generator: select any material or topic, adjust difficulty (`Easy`, `Medium`, `Hard`, `Mixed`), and choose question count (3 to 15 questions).
     - Detailed post-quiz feedback (`/quiz-result`) with question-by-question explanations.

6. **🎙️ Viva Voce Oral Defense Simulator (`/viva`)**
   - Interactive oral examination simulating real academic viva voce defenses.
   - Real-time examiner questioning grounded in syllabus topics and study material chunks.
   - Rubric-based scoring on technical accuracy, clarity, and depth, complete with a final transcript summary.

7. **📝 Markdown Notes & AI Enhancement (`/notes`)**
   - Rich Markdown note-taking with tag filtering, search, and pinned notes.
   - Direct linking between student notes and source study materials.
   - AI-assisted note enhancement and concept summarization.

8. **📅 Dynamic Study Planner (`/study-plan`)**
   - Personalized day-by-day study calendars generated from upcoming deadlines and topic mastery levels.
   - Spaced repetition queues prioritizing weaker topics before exams.

9. **📊 Comprehensive Progress Analytics (`/progress`, `/dashboard`)**
   - Real-time metrics including study streaks, total study hours, topic mastery progress bars, quiz accuracy rates, and AI-recommended focus areas.

10. **🔔 Real-Time Notification Center (`/notifications`)**
    - Instant in-app alerts for assigned assessments, study reminders, and grading feedback.
    - Human-readable relative timestamps (*"just now"*, *"2 hours ago"*, *"yesterday"*).
    - Deep links navigating directly to relevant materials or assessments.

---

### 👨‍🏫 Instructor Classroom Management Portal (`/instructor`)

1. **📊 Instructor Dashboard (`/instructor/dashboard`)**
   - Class-wide overview metrics: total students, active assessments, submission volume, class average score, and at-risk student counters.
   - Recent student submissions and quick action shortcuts.

2. **📋 Assessment Creation & Assignment Engine (`/instructor/create-assessment`, `/instructor/assessments`)**
   - Multi-question assessment builder supporting custom topics, time limits, passing scores, question weights, options, hints, and explanations.
   - Assign assessments to individual students or entire cohorts with due dates.
   - Automated push notifications dispatched directly to student notification centers upon assignment.

3. **👥 Student Directory & Individual Deep-Dives (`/instructor/students`)**
   - Complete roster of enrolled students with overall mastery percentages, quiz completion counts, and activity logs.
   - Detailed per-student breakdown of strengths, weaknesses, and assessment submissions.

4. **📈 Class Analytics & Topic Mastery Heatmaps (`/instructor/analytics`)**
   - Class performance distributions, topic difficulty rankings, and pass rate analysis across subjects.

5. **💬 Qualitative Feedback System (`/instructor/feedback`)**
   - Review student inquiries, provide qualitative commentary on submissions, and dispatch guidance notes.

6. **📑 Performance Reports & Export (`/instructor/reports`)**
   - Generate and export academic gradebooks, submission audits, and student performance summaries.

---

### 🔐 Authentication & Security

- **JWT Authentication**: Token-based authentication with expiration controls and user role identification (`student`, `instructor`, `admin`).
- **Password Hashing**: Salted `bcrypt` password encryption.
- **Forgot Password & Password Reset Flow**:
  - Secure, time-limited cryptographic reset tokens.
  - SMTP email integration via `email_service.py` (compatible with Gmail SMTP, SendGrid, Amazon SES, or local console fallback in development).
- **Strict Role-Based Access Control (RBAC)**: Protected routes on both frontend (`ProtectedRoute`) and backend (`deps.py`).

---

## 🏛 System Architecture

```mermaid
flowchart TD
    subgraph Client ["🖥️ Client Application (React 18 + Vite)"]
        Landing["Landing & Auth (/login, /signup, /forgot-password)"]
        StudentPortal["🧑‍🎓 Student Portal (/dashboard, /tutor, /quizzes, /summaries, /viva)"]
        InstructorPortal["👨‍🏫 Instructor Portal (/instructor/dashboard, /assessments, /students)"]
        APIClient["API Service Layer (Axios + JWT Interceptors)"]
    end

    subgraph Gateway ["⚙️ Backend Gateway (FastAPI)"]
        CORS["CORS & Request Middleware"]
        AuthMiddleware["JWT Authentication & RBAC Guards"]
        APIRouters["FastAPI Routers (/api/auth, /api/tutor, /api/instructor, etc.)"]
    end

    subgraph Engines ["🧠 Core Intelligence Engines"]
        RAGEngine["RAG Engine (PyPDF + Chunking + Hybrid Retrieval)"]
        LLMOrchestrator["LLM Orchestrator (OpenAI GPT-4o-mini / Gemini 2.5)"]
        AdaptiveEngine["Adaptive Engine (Mastery Scoring & Spaced Repetition)"]
        VivaEngine["Viva Voce Examiner (Dynamic Rubrics & Dialogue)"]
        EmailService["Email Service (SMTP Dispatch & Password Reset)"]
    end

    subgraph DataLayer ["💾 Persistence & Vector Storage"]
        RelationalDB[("SQLAlchemy Database (SQLite / PostgreSQL) - 24 Models")]
        VectorStore[("Document Chunks & Vector Embeddings")]
    end

    Client --> Gateway
    Landing --> APIClient
    StudentPortal --> APIClient
    InstructorPortal --> APIClient
    APIClient --> CORS --> AuthMiddleware --> APIRouters

    APIRouters --> RAGEngine
    APIRouters --> LLMOrchestrator
    APIRouters --> AdaptiveEngine
    APIRouters --> VivaEngine
    APIRouters --> EmailService
    APIRouters --> RelationalDB

    RAGEngine --> VectorStore
    RAGEngine --> LLMOrchestrator
```

---

## 🛠 Technology Stack

| Domain | Technology | Purpose & Role |
| :--- | :--- | :--- |
| **Frontend Framework** | **React 18** | High-performance component-driven user interface |
| **Build Tool** | **Vite 5** | Lightning-fast HMR and optimized production bundling |
| **Styling & Design** | **Tailwind CSS 3** | Responsive, modern utility styling with custom color tokens |
| **Icons & Visuals** | **Lucide React** | Clean, consistent UI iconography |
| **Data Visualization** | **Recharts** | Interactive charts for topic mastery, radar scores, and trends |
| **Document Export** | **html2pdf.js / html2canvas** | Client-side export of formatted AI summaries to downloadable PDF |
| **Backend Framework** | **FastAPI** | High-speed, asynchronous Python REST API framework |
| **Application Server** | **Uvicorn** | Asynchronous ASGI server with live reloading |
| **ORM & Database** | **SQLAlchemy 2.0** | Relational mapping across 24 database models |
| **Database Engine** | **SQLite / PostgreSQL** | Zero-config SQLite default with seamless PostgreSQL production support |
| **AI / LLMs** | **OpenAI GPT-4o-mini & Google Gemini** | Conversational tutoring, evaluation, and question generation |
| **Document Parsing** | **PyPDF** | PDF text extraction and sliding-window chunk extraction |
| **Authentication** | **PyJWT + Passlib (bcrypt)** | Stateless JWT tokens and salted cryptographic password hashing |
| **Email & Delivery** | **Python smtplib** | Password recovery emails with SMTP support and development fallback |

---

## ⚡ Quick Start Guide

### Prerequisites
- **Node.js**: `v18.0.0` or higher
- **Python**: `v3.10` or higher (compatible with Python 3.10 through 3.13)
- **Git**: Installed on your system

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/Sarthzz01/AI_StudyCompanion.git
cd AI_StudyCompanion
```

---

### Step 2: Set Up Backend (FastAPI)

1. Open a terminal and navigate to `backend/`:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Copy `.env.example` to `.env`:
   ```bash
   # Windows PowerShell
   Copy-Item .env.example .env

   # Linux / macOS
   cp .env.example .env
   ```

   Open `backend/.env` and configure your API keys:
   ```env
   # LLM Provider Configuration (Configure either or both)
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4o-mini

   # Optional Gemini configuration:
   # GEMINI_API_KEY=your_gemini_api_key_here
   # GEMINI_MODEL=gemini-2.5-flash

   # Secret Key for JWT Tokens
   JWT_SECRET=super-secret-jwt-key-for-ai-study-companion-phase-2-2026

   # Database (Defaults to SQLite automatically if PostgreSQL is omitted)
   # DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/ai_study_companion

   # Optional SMTP Email Configuration (For Forgot Password emails)
   # SMTP_HOST=smtp.gmail.com
   # SMTP_PORT=587
   # SMTP_USER=your_email@gmail.com
   # SMTP_PASSWORD=your_app_password
   # SMTP_FROM_EMAIL=noreply@aistudycompanion.com
   # SMTP_USE_TLS=true
   ```

5. Launch the FastAPI backend:
   ```bash
   # Windows PowerShell
   ..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

   # macOS / Linux
   python -m uvicorn app.main:app --reload --port 8000
   ```
   - **API Server**: `http://localhost:8000`
   - **Interactive Swagger Docs**: `http://localhost:8000/docs`
   - **Alternative ReDoc**: `http://localhost:8000/redoc`

---

### Step 3: Set Up Frontend (React + Vite)

1. Open a second terminal and navigate to the project root:
   ```bash
   cd AI_StudyCompanion
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   - **Frontend App**: `http://localhost:5173`

---

## 🔑 Default Test Accounts

On initial launch, the system automatically runs database migrations and seeds pre-configured test accounts and academic materials:

| Role | Email | Password | Name | Access Level |
| :--- | :--- | :--- | :--- | :--- |
| 🧑‍🎓 **Student** | `student@study.edu` | `password123` | Alex Mercer | Access personal materials, AI tutor, flashcards, quizzes, viva, notes |
| 👨‍🏫 **Instructor** | `instructor@study.edu` | `password123` | Dr. Alan Turing | Access instructor dashboard, student directory, assessment builder, grading |
| 🛡️ **Admin** | `admin@study.edu` | `admin123` | System Admin | System administration and user management |

> **Note**: You can also register a brand-new student account instantly via the **/signup** page, or test password recovery via **/forgot-password**.

---

## 📡 API Endpoints Reference

### 🔐 Authentication & Profile (`/api/auth`, `/api/profile`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register new account and initialize learner model |
| `POST` | `/api/auth/login` | Authenticate with email/password; returns JWT |
| `GET` | `/api/auth/me` | Fetch currently authenticated user profile |
| `POST` | `/api/auth/forgot-password` | Generate reset token and send recovery email |
| `POST` | `/api/auth/reset-password` | Validate reset token and update account password |
| `GET` | `/api/profile` | Retrieve student profile settings and preferences |
| `PUT` | `/api/profile` | Update profile info, avatar, and daily goals |

### 💬 AI Tutor & Conversations (`/api/tutor`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/tutor/ask` | Ask question with RAG grounding from study materials |
| `GET` | `/api/tutor/conversations` | Retrieve all user chat threads with semantic auto-titles |
| `GET` | `/api/tutor/conversations/{id}` | Retrieve full message history of a chat thread |
| `PATCH` | `/api/tutor/conversations/{id}/rename` | Rename chat thread title |
| `DELETE` | `/api/tutor/conversations/{id}` | Delete a chat thread |

### 📚 Study Materials (`/api/materials`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/materials` | List all uploaded study materials |
| `POST` | `/api/materials` | Upload new material (PDF or text) with automatic chunking |
| `GET` | `/api/materials/{id}` | Get material details, syllabus topics, and chunks |
| `DELETE` | `/api/materials/{id}` | Delete material with cascading chunk cleanup |

### 📄 Summaries & Concept Extraction (`/api/summaries`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/summaries/generate` | Generate structured summary from existing material |
| `POST` | `/api/summaries/generate-from-file` | Upload any PDF file directly and generate instant summary |
| `GET` | `/api/summaries` | List user's saved summaries |
| `GET` | `/api/summaries/{id}` | Retrieve specific summary details |

### 🗂️ Flashcards & Active Recall (`/api/flashcards`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/flashcards/generate` | Generate AI flashcards from topic or material |
| `GET` | `/api/flashcards` | Retrieve user flashcard decks |
| `POST` | `/api/flashcards/{id}/review` | Submit review rating (`easy`, `medium`, `hard`) |

### 📝 Quizzes & Practice Tests (`/api/quizzes`, `/api/quiz-attempts`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/quizzes/generate` | Generate practice quiz (`difficulty`, `count`, `topic`) |
| `GET` | `/api/quizzes/{id}` | Retrieve quiz questions (sanitized without answers) |
| `POST` | `/api/quizzes/{id}/attempt` | Start quiz attempt session |
| `POST` | `/api/quiz-attempts/{id}/submit` | Submit answers for instant grading & mastery update |

### 👨‍🏫 Instructor Module & Assessments (`/api/instructor`, `/api/assessments`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/instructor/dashboard` | Dashboard KPIs, class mastery, at-risk student count |
| `GET` | `/api/instructor/students` | Full student roster with individual mastery statistics |
| `GET` | `/api/instructor/students/{id}` | Detailed student profile, quiz history, and weak topics |
| `GET` | `/api/instructor/analytics` | Class-wide mastery heatmaps and question performance |
| `GET` | `/api/instructor/assessments` | List all instructor-created assessments |
| `POST` | `/api/instructor/assessments` | Create new multi-question assessment |
| `POST` | `/api/instructor/assessments/{id}/assign` | Assign assessment to students & dispatch notifications |
| `GET` | `/api/instructor/assessments/{id}/submissions` | View student submissions and scores for an assessment |
| `GET` | `/api/assessments/assigned` | *(Student)* List assigned assessments with deadlines & status |
| `GET` | `/api/assessments/{id}` | *(Student)* Get assessment questions for taking exam |
| `POST` | `/api/assessments/{id}/submit` | *(Student)* Submit assessment answers for grading |

### 🎙️ Viva Voce Oral Defense (`/api/viva`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/viva/start` | Start interactive oral defense session |
| `POST` | `/api/viva/{id}/answer` | Submit spoken/written answer and receive next question |
| `GET` | `/api/viva/{id}` | Get session transcript, rubric scoring, and evaluation |

### 📝 Notes System (`/api/notes`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/notes` | List student notes with search and tag filters |
| `POST` | `/api/notes` | Create new note linked to study material |
| `PUT` | `/api/notes/{id}` | Update note content, tags, or pinned state |
| `DELETE` | `/api/notes/{id}` | Delete note |

### 🔔 Notifications (`/api/notifications`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/notifications` | List user notifications with unread counter |
| `PATCH` | `/api/notifications/{id}/read` | Mark individual notification as read |
| `POST` | `/api/notifications/read-all` | Mark all notifications as read |

---

## 📂 Project Directory Structure

```text
ai-study-companion/
├── backend/
│   ├── app/
│   │   ├── models/             # 24 SQLAlchemy relational models (User, Material, Assessment, etc.)
│   │   ├── routers/            # 17 FastAPI route modules (auth, tutor, instructor, viva, etc.)
│   │   ├── schemas/            # Pydantic request/response validation schemas
│   │   ├── services/           # Business logic & AI engines (RAG, OpenAI, Gemini, Viva, Email)
│   │   ├── config.py           # Centralized configuration and environment settings
│   │   ├── database.py         # SQLAlchemy engine, session factory & auto-migration
│   │   ├── seed.py             # Database seed script for test accounts & sample materials
│   │   └── main.py             # FastAPI app entry point with lifespan and router mounting
│   ├── requirements.txt        # Python dependencies (fastapi, sqlalchemy, pypdf, openai, etc.)
│   ├── .env.example            # Environment variables template
│   └── ai_study_companion.db   # Local SQLite database file (auto-generated)
├── src/
│   ├── components/             # Reusable UI components (Navbar, Sidebar, Modals, Cards)
│   ├── context/                # React Context providers (AuthContext, StudyDataContext)
│   ├── layouts/                # DashboardLayout and Navigation wrappers
│   ├── pages/                  # Student & Public application pages
│   │   ├── instructor/         # Instructor Portal pages (Dashboard, Assessments, Students, etc.)
│   │   ├── Dashboard.jsx       # Student central hub & metrics
│   │   ├── Tutor.jsx           # RAG-grounded AI Tutor with chat history
│   │   ├── Summaries.jsx       # Smart Summaries with direct PDF file upload & PDF export
│   │   ├── Quizzes.jsx         # Dual-tab Quizzes (Assigned Assessments vs Self-Study Quizzes)
│   │   ├── QuizAttempt.jsx     # Interactive quiz/assessment exam runner
│   │   ├── Viva.jsx            # Viva Voce oral examination interface
│   │   ├── Notes.jsx           # Markdown notes manager
│   │   ├── Materials.jsx       # Study materials repository
│   │   └── ForgotPassword.jsx  # Password recovery request page
│   ├── services/
│   │   └── api.js              # Centralized Axios API client with auth interceptors
│   ├── utils/
│   │   ├── format.js           # Relative timestamp and string formatters
│   │   └── pdfExport.js        # PDF generation helper using html2canvas & html2pdf
│   ├── App.jsx                 # Client routing and role-protected routes
│   ├── main.jsx                # React root application bootstrap
│   └── index.css               # Design tokens, custom scrollbars, and Tailwind CSS styles
├── package.json                # Frontend dependencies and npm scripts
├── vite.config.js              # Vite bundler configuration
├── tailwind.config.js          # Tailwind CSS theme extension
├── README.md                   # Project overview and setup guide
└── PROJECT_REPORT.md           # In-depth architectural and engineering report
```

---

## 🔒 Security & Best Practices

- **Zero Hardcoded Secrets**: All API credentials, JWT keys, and database connection strings are loaded strictly from environment variables.
- **Salted Password Hashing**: Passwords are cryptographically salted using `bcrypt` via Passlib.
- **Role-Based Authorization**: Endpoints verify user roles (`student`, `instructor`, `admin`) before granting access to instructor dashboards or administrative actions.
- **Input Sanitization & Schema Validation**: Pydantic validates all incoming backend payloads; React forms sanitize user inputs.
- **Answer Masking in Tests**: Quiz and assessment endpoints sanitize questions before sending them to students, ensuring correct answers cannot be inspected in client network requests.

---

## 📄 Comprehensive Project Report

For an in-depth, end-to-end technical breakdown of the project architecture, engineering design choices, database schema relationships, RAG retrieval mechanisms, and step-by-step implementation journey, please review [`PROJECT_REPORT.md`](file:///c:/Users/Shubh/Desktop/ai-study-companion/PROJECT_REPORT.md).

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
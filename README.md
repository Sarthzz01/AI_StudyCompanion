# AI Study Companion — Full Stack (Phase 2)

An AI-powered student learning platform with a **React 18 + Vite** frontend, a **FastAPI + SQLAlchemy** backend, and a **Gemini 3.8 Flash** AI service foundation.

---

## 1. Quick Start Guide

### Prerequisites
- **Node.js**: v18 or newer
- **Python**: v3.10 or newer (tested with Python 3.13)
- **Database**: PostgreSQL (optional, falls back automatically to SQLite for zero-config local development)

---

### Step 1: Start the Backend

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. (Optional) Configure environment in `backend/.env`:
   ```env
   DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/ai_study_companion
   SECRET_KEY=super-secret-jwt-key-for-ai-study-companion-phase-2-2026
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-3.8-flash
   ```
   > **Note**: If PostgreSQL is not running on localhost:5432, the backend automatically logs a note and seamlessly connects to a local SQLite database (`ai_study_companion.db`).

4. Start the FastAPI server:
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```
   The backend will start at: `http://localhost:8000`
   - Interactive Swagger API documentation: `http://localhost:8000/docs`
   - ReDoc documentation: `http://localhost:8000/redoc`

---

### Step 2: Start the Frontend

1. Navigate to the `ai-study-companion/` directory:
   ```bash
   cd ai-study-companion
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Start Vite dev server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

## 2. Seeded Accounts & Testing Credentials

The database automatically seeds on first launch with 3 roles and initial study materials:

| Role | Email | Password | Name |
| :--- | :--- | :--- | :--- |
| **Student** | `student@study.edu` | `password123` | Alex Mercer |
| **Instructor** | `instructor@study.edu` | `password123` | Dr. Alan Turing |
| **Admin** | `admin@study.edu` | `admin123` | System Admin |

You can also sign up with any new account via `/signup`, which creates a real user in the database, generates a JWT token, and logs in automatically.

---

## 3. Implemented APIs (Phase 2)

### Authentication (`/api/auth`)
- `POST /api/auth/register` — Create user account & profile, return JWT access token
- `POST /api/auth/login` — Authenticate credentials, return JWT access token
- `POST /api/auth/logout` — Logout session
- `GET  /api/auth/me` — Retrieve current authenticated user

### Profile (`/api/profile`)
- `GET /api/profile` — Get full user profile, bio, joined date, and learning preferences
- `PUT /api/profile` — Update name, bio, and preferences
- `PUT /api/profile/password` — Change password with current password verification

### Subjects (`/api/subjects`)
- `GET /api/subjects` — List all subjects with topic counts
- `GET /api/subjects/{id}/topics` — List all topics for a specific subject

### Study Materials (`/api/materials`)
- `GET    /api/materials` — Retrieve all study materials formatted for the frontend
- `POST   /api/materials` — Create/upload study material (supports JSON and multipart/form-data)
- `GET    /api/materials/{id}` — Retrieve details and topic breakdown for a material
- `DELETE /api/materials/{id}` — Delete a material (owner or instructor/admin)

### Flashcards (`/api/flashcards`) — Phase 4
- `POST /api/flashcards/generate` — Generate structured high-yield flashcards from study material with Gemini
- `GET  /api/flashcards` — Retrieve user and material flashcards
- `GET  /api/flashcards/{id}` — Retrieve single flashcard by ID
- `POST /api/flashcards/{id}/review` — Record student practice rating ('easy', 'medium', 'hard') and update topic mastery in LearnerModel

### Quizzes & Evaluation (`/api/quizzes`, `/api/quiz-attempts`) — Phase 4
- `POST /api/quizzes/generate` — Generate difficulty-aware (easy, medium, hard, mixed) multiple-choice questions from material/topic with Gemini
- `GET  /api/quizzes` — List quizzes
- `GET  /api/quizzes/{id}` — Retrieve quiz details and questions
- `POST /api/quizzes/{id}/attempt` — Start an active quiz attempt
- `GET  /api/quiz-attempts/{id}` — Retrieve quiz attempt status or completed evaluation
- `POST /api/quiz-attempts/{id}/submit` — Submit quiz attempt for automatic grading, accuracy calculation, topic/difficulty breakdown, and learner performance recording
- `GET  /api/quiz-attempts` — List historical completed quiz attempts

### AI Tutor & Summaries (`/api/tutor`, `/api/summaries`) — Phase 3
- `POST /api/tutor/ask` — Grounded RAG academic tutor with citation page numbers
- `POST /api/summaries/generate` — Generate comprehensive structured summary with key concepts
- `GET  /api/summaries` — List generated summaries
- `GET  /api/summaries/{material_id}` — Get summary by material ID or numeric summary ID

### AI Service Foundation (`/api/ai`)
- `GET  /api/ai/health` — Check status of the server-side Gemini service
- `POST /api/ai/test` — Test prompt completion using Gemini 3.8 Flash SDK

---

## 4. Database Models

The schema defines all 16 requested tables with proper relationships and indexes:
1. `User` — Authentication and account details
2. `Role` — Role-based access control (Student, Instructor, Admin)
3. `Profile` — Extended user details, bio, avatar, preferences
4. `Subject` — Curriculum subjects (e.g. Data Structures, DBMS, OS, Networks)
5. `Topic` — Subject topics with difficulty levels and order
6. `Material` — Study materials with pages, progress, topics, and recent activity
7. `Question` — Assessment questions linked to topics
8. `Flashcard` — Active recall flashcards linked to topics/materials
9. `QuizAttempt` — Detailed quiz attempt history and scores
10. `StudySession` — Timed study sessions
11. `LearnerModel` — Topic mastery, recall reliability, quiz/flashcard/viva performance, review schedules
12. `Progress` — Overall user analytics, study time, streak
13. `RevisionSchedule` — Spaced repetition scheduling (ease factor, interval)
14. `Notification` — User notifications
15. `Recommendation` — AI-generated study recommendations
16. `Analytics` — Event tracking for study behaviors

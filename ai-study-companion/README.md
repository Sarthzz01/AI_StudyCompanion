# AI Study Companion — Fully Functional Full-Stack Platform

An AI-powered learning management and adaptive study companion platform built with **React 18 + Vite** frontend, **FastAPI + SQLAlchemy** backend, **SQLite database**, and **Google Gemini AI**.

---

## 🚀 Live Working Architecture

This project is a **complete, fully functional full-stack application**:
- **Backend API**: FastAPI running on `http://localhost:8000` with 16 RESTful modules and SQLite database.
- **Frontend App**: React 18 + Vite running on `http://localhost:5173`.
- **AI Intelligence**: Live Google Gemini integration with grounded RAG (Retrieval-Augmented Generation) and semantic study assistants.
- **Role-Based Portals**:
  - **Student Portal**: Study Plan, Materials Management (PDF/Text extraction), AI Grounded Tutor, Summary Generation, Flashcards & Spaced Repetition, Adaptive Quizzes & Evaluation, Viva Voice/Technical Assessment, Analytics & Progress Tracking, Goals & Notifications.
  - **Instructor Portal**: Class Analytics, Student Roster & Topic Weaknesses, Assessment Creator & Management, Student Submissions & Grading, Direct Performance Feedback, Exportable Reports.

---

## 🔑 Login Accounts (Pre-Seeded)

The database includes pre-configured accounts ready for immediate testing:

| Role | Email | Password | Details |
| :--- | :--- | :--- | :--- |
| **Student** | `student@study.edu` | `password123` | Alex Mercer (Full study data, progress, goals, flashcards, quizzes) |
| **Instructor** | `instructor@study.edu` | `password123` | Dr. Alan Turing (Access to `/instructor` portal, assessments, student metrics) |
| **Admin** | `admin@study.edu` | `admin123` | System Administrator |

> You can also register any brand new student or instructor account directly on the **Sign Up** page (`/signup`).

---

## ⚡ How to Run

### 1. Start the Backend API (FastAPI)
In a terminal at project root:
```bash
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --port 8000
```
- API root: `http://localhost:8000`
- Interactive Swagger docs: `http://localhost:8000/docs`

### 2. Start the Frontend Dev Server (Vite)
In another terminal at project root:
```bash
npm run dev
```
- Open in browser: `http://localhost:5173`

---

## 🌟 Modules & Features Overview

1. **Authentication & Profile**: JWT bearer tokens, secure bcrypt passwords, avatar & preferences.
2. **Study Materials**: Upload PDF/text files with automatic text parsing and chunking for AI.
3. **AI Tutor**: Real-time grounded answers with specific material citations and page references.
4. **Summaries**: Auto-generated structured concept breakdowns, key definitions, and takeaways.
5. **Flashcards**: Active-recall cards with spaced-repetition difficulty scoring ('easy', 'medium', 'hard').
6. **Adaptive Quizzes**: Topic-specific multiple choice assessments with instant grading and explanations.
7. **AI Viva (Technical Interview)**: Voice and text oral exams with conceptual evaluation and scoring.
8. **Student Progress & Analytics**: Daily study time, mastery matrices, streak tracking, and weak topic alerts.
9. **Instructor Module**: Classroom performance dashboard, assessment dispatching, and feedback delivery.

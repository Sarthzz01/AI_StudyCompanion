# AI Study Companion — Frontend

An AI-powered student learning platform. A student adds study material, and the app turns it into
summaries, flashcards, quizzes and an AI tutor, then tracks performance and recommends what to study
next.

This repository contains the **frontend only**. Every "AI" and "server" call is mocked locally, and
the code is structured so those mocks can be swapped for a FastAPI backend without touching the pages.

The learning cycle the app implements:

```
Study material → AI processing → Summary / Flashcards / AI Tutor / Quiz
              → Quiz attempt → Performance recorded → Weak topics identified
              → Personalised recommendations
```

This is a **student-only** application. There is no instructor module, no admin module, no revision
scheduler and no mock interview.

---

## 1. Technologies used

| Purpose | Library |
| --- | --- |
| UI | React 18 (functional components and hooks) |
| Build tool | Vite 5 |
| Language | JavaScript (no TypeScript) |
| Styling | Tailwind CSS 3 |
| Routing | React Router 6 |
| HTTP client | Axios (configured, ready for the backend) |
| Charts | Recharts |
| Icons | Lucide React |

---

## 2. Installation

You need Node.js 18 or newer.

```bash
npm install
```

## 3. How to run

```bash
npm run dev      # start the dev server on http://localhost:5173
npm run build    # production build into dist/
npm run preview  # preview the production build
```

Open the app, click **Get started** or **Log in**. Authentication is mocked: any valid email address
and a password of at least 6 characters will sign you in.

---

## 4. Project structure

```
ai-study-companion/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── public/
│   └── favicon.svg
└── src/
    ├── components/          # reusable UI pieces
    │   ├── Button.jsx       Card.jsx        Input.jsx
    │   ├── Select.jsx       Modal.jsx       ProgressBar.jsx
    │   ├── StatCard.jsx     MaterialCard.jsx
    │   ├── RecommendationCard.jsx
    │   ├── Flashcard.jsx    QuizCard.jsx    ChatMessage.jsx
    │   ├── NotificationItem.jsx
    │   ├── LoadingSpinner.jsx  EmptyState.jsx  ErrorState.jsx
    │   ├── ToastStack.jsx   PageHeader.jsx
    │   ├── Navbar.jsx       Sidebar.jsx
    │   └── ProtectedRoute.jsx
    ├── context/             # app-wide state
    │   ├── AuthContext.jsx        mock login/signup + localStorage session
    │   ├── StudyDataContext.jsx   progress, quiz attempts, goals, notifications
    │   ├── ThemeContext.jsx       light/dark mode
    │   └── ToastContext.jsx       toast messages
    ├── data/                # all mock data lives here, never inside pages
    │   ├── mockMaterials.js  mockQuiz.js     mockFlashcards.js
    │   ├── mockSummaries.js  mockTutor.js    mockProgress.js
    │   ├── mockNotifications.js  mockGoals.js  mockRecommendations.js
    ├── layouts/
    │   └── DashboardLayout.jsx    sidebar + navbar shell for signed-in pages
    ├── pages/               # one file per route
    │   ├── Landing.jsx  Login.jsx  Signup.jsx
    │   ├── Dashboard.jsx  Materials.jsx  MaterialDetails.jsx
    │   ├── Tutor.jsx  Summaries.jsx  Flashcards.jsx
    │   ├── Quizzes.jsx  QuizAttempt.jsx  QuizResult.jsx
    │   ├── Progress.jsx  Goals.jsx  Notifications.jsx  Profile.jsx
    │   └── NotFound.jsx
    ├── services/
    │   └── api.js           the single place that talks to "the backend"
    ├── utils/
    │   ├── storage.js       safe localStorage wrapper
    │   └── format.js        small formatting helpers
    ├── App.jsx              route table
    ├── main.jsx             entry point and context providers
    └── index.css            Tailwind layers and shared component classes
```

### Routes

| Route | Page |
| --- | --- |
| `/` | Landing |
| `/login` | Login |
| `/signup` | Sign up |
| `/dashboard` | Student dashboard |
| `/materials` | Study materials |
| `/materials/:id` | Material details |
| `/tutor` | AI tutor chat |
| `/summaries` | AI summaries |
| `/flashcards` | Flashcards |
| `/quizzes` | Quiz setup and previous attempts |
| `/quizzes/:id` | Quiz attempt |
| `/quiz-result` | Quiz result and answer review |
| `/progress` | Personal analytics |
| `/goals` | Study goals |
| `/notifications` | Notifications |
| `/profile` | Profile and settings |

Everything from `/dashboard` onwards sits behind `ProtectedRoute`, which redirects to `/login` when
there is no mock session.

---

## 5. Current features

- **Landing page** with hero, feature cards, a three-step explainer and footer.
- **Mock authentication** with form validation, show/hide password, remember me and a protected area.
- **Dashboard** with overall progress, today's goal, continue learning, AI recommendations, quick
  actions, a Recharts accuracy line chart and four performance stats.
- **Study materials** with search, type filter, responsive grid and an upload modal with a file picker.
- **Material details** with description, per-topic progress, recent activity and the four study actions.
- **AI tutor** — a realistic chat: user message, typing animation, mock grounded answer and source
  chips such as `Data Structures.pdf — Page 12`.
- **Summaries** with material switching, in-summary search, expand/collapse sections, key concepts and
  bookmarking (saved in localStorage).
- **Flashcards** with a 3D flip, previous/next, progress indicator and easy/medium/hard rating.
- **Quizzes** — setup by material, topic, difficulty and question count; a quiz runner with state that
  survives moving between questions, a question jump list, a submit confirmation, and a result page
  with score, accuracy, strong/weak topics and a full answer review with explanations.
- **Progress** with four Recharts visualisations (accuracy over time, topic-wise accuracy, quiz
  performance, weekly study time) plus strong, weak and recently improved topics.
- **Goals** — daily and weekly goals with add, complete and delete, persisted in localStorage.
- **Notifications** with unread state, filter, mark as read, mark all read and clear.
- **Profile** with editable details, preferences, notification settings, change-password UI, a dark
  mode toggle and logout.
- Loading, empty and error states throughout, toast messages, keyboard focus rings, `prefers-reduced-motion`
  support and a responsive layout with a sidebar on desktop and a drawer on mobile.

---

## 6. How the mock data works

There is no backend, so the app behaves like this:

1. Every page calls a function from `src/services/api.js` — never a mock file directly.
2. Those functions wait a few hundred milliseconds (so loading states are real) and then resolve with
   data from `src/data/`.
3. Anything the student *changes* lives in `src/context/StudyDataContext.jsx` and is mirrored into
   `localStorage`, so a refresh keeps it.

What is persisted in `localStorage` (all keys are prefixed with `asc:`):

| Key | Contents |
| --- | --- |
| `asc:user` | the mock signed-in student |
| `asc:progress` | analytics shown on Dashboard and Progress |
| `asc:attempts` | quiz attempt history |
| `asc:goals` | study goals |
| `asc:notifications` | notification list and read state |
| `asc:savedSummaries` | bookmarked summary sections |
| `asc:preferences` | study and notification preferences |
| `asc:theme` | light or dark |

**Progress really does update after a quiz.** `recordQuizAttempt` in `StudyDataContext` stores the
attempt, recalculates overall accuracy and questions attempted, adds a point to the accuracy-over-time
chart, merges the per-topic results into topic accuracy, and raises a notification. To go back to the
sample data, use *Reset demo progress* on the Profile page, or clear the site's localStorage.

---

## 7. Connecting the FastAPI backend later

All the work happens in `src/services/api.js`. It already exports an axios instance:

```js
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export const http = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})
```

Replace the body of each function, keeping the same return shape, and every page keeps working:

```js
// before (mock)
export async function getMaterials() {
  await delay(500)
  return mockMaterials
}

// after (FastAPI)
export async function getMaterials() {
  const { data } = await http.get('/materials')
  return data
}
```

Suggested endpoint mapping:

| Function | Endpoint |
| --- | --- |
| `loginUser` | `POST /auth/login` |
| `signupUser` | `POST /auth/signup` |
| `getMaterials` | `GET /materials` |
| `getMaterial` | `GET /materials/{id}` |
| `uploadMaterial` | `POST /materials` (multipart form data) |
| `askTutor` | `POST /tutor/ask` → `{ answer, sources }` |
| `generateSummary` | `POST /materials/{id}/summary` |
| `getFlashcards` | `GET /materials/{id}/flashcards` |
| `generateQuiz` | `POST /quizzes/generate` |
| `submitQuiz` | `POST /quizzes/{id}/submit` |
| `getQuizAttempts` | `GET /quizzes/attempts` |
| `getProgress` | `GET /progress` |
| `getRecommendations` | `GET /recommendations` |

Steps:

1. Create a `.env` file in the project root with `VITE_API_URL=http://localhost:8000/api`.
2. Rewrite the functions in `services/api.js` one at a time — the mock data files show the exact shape
   each one must return.
3. Once the backend owns progress, goals and notifications, replace the `useState` initialisers in
   `StudyDataContext.jsx` with a fetch on mount and POST the changes instead of writing to localStorage.
4. Add the auth token: store it in `AuthContext` and set a request interceptor on `http`.
5. Enable CORS in FastAPI for `http://localhost:5173`.

---

## 8. Notes

- Mock data never sits inside a page component — everything is in `src/data/`.
- Shared Tailwind classes (`.card`, `.field`, `.chip`, `.label`, `.muted`) are defined in `index.css`
  so styling stays consistent across pages.
- Colour, typography and shadows are defined once in `tailwind.config.js` under the `brand` and `ink`
  palettes. Changing `brand` recolours the whole app.

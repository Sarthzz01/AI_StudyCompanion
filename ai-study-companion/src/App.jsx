import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import DashboardLayout from './layouts/DashboardLayout.jsx'

import Landing from './pages/Landing.jsx'
import Login from './pages/Login.jsx'
import Signup from './pages/Signup.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Materials from './pages/Materials.jsx'
import MaterialDetails from './pages/MaterialDetails.jsx'
import Tutor from './pages/Tutor.jsx'
import Summaries from './pages/Summaries.jsx'
import Flashcards from './pages/Flashcards.jsx'
import Quizzes from './pages/Quizzes.jsx'
import QuizAttempt from './pages/QuizAttempt.jsx'
import QuizResult from './pages/QuizResult.jsx'
import Progress from './pages/Progress.jsx'
import Goals from './pages/Goals.jsx'
import Notifications from './pages/Notifications.jsx'
import Profile from './pages/Profile.jsx'
import NotFound from './pages/NotFound.jsx'

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      {/* Everything below requires a (mock) logged-in student */}
      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/materials" element={<Materials />} />
        <Route path="/materials/:id" element={<MaterialDetails />} />
        <Route path="/tutor" element={<Tutor />} />
        <Route path="/summaries" element={<Summaries />} />
        <Route path="/flashcards" element={<Flashcards />} />
        <Route path="/quizzes" element={<Quizzes />} />
        <Route path="/quizzes/:id" element={<QuizAttempt />} />
        <Route path="/quiz-result" element={<QuizResult />} />
        <Route path="/progress" element={<Progress />} />
        <Route path="/goals" element={<Goals />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/profile" element={<Profile />} />
      </Route>

      <Route path="/404" element={<NotFound />} />
      <Route path="*" element={<Navigate to="/404" replace />} />
    </Routes>
  )
}

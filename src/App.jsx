import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import DashboardLayout from './layouts/DashboardLayout.jsx'

import Landing from './pages/Landing.jsx'
import Login from './pages/Login.jsx'
import Signup from './pages/Signup.jsx'
import ForgotPassword from './pages/ForgotPassword.jsx'
import ResetPassword from './pages/ResetPassword.jsx'
import Dashboard from './pages/Dashboard.jsx'
import StudyPlan from './pages/StudyPlan.jsx'
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
import Viva from './pages/Viva.jsx'
import Notes from './pages/Notes.jsx'
import NotFound from './pages/NotFound.jsx'

// Instructor Module Pages
import InstructorDashboard from './pages/instructor/InstructorDashboard.jsx'
import Assessments from './pages/instructor/Assessments.jsx'
import CreateAssessment from './pages/instructor/CreateAssessment.jsx'
import Students from './pages/instructor/Students.jsx'
import ClassAnalytics from './pages/instructor/ClassAnalytics.jsx'
import Feedback from './pages/instructor/Feedback.jsx'
import Reports from './pages/instructor/Reports.jsx'

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />

      {/* Student Portal Routes */}
      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/study-plan" element={<StudyPlan />} />
        <Route path="/materials" element={<Materials />} />
        <Route path="/materials/:id" element={<MaterialDetails />} />
        <Route path="/tutor" element={<Tutor />} />
        <Route path="/summaries" element={<Summaries />} />
        <Route path="/flashcards" element={<Flashcards />} />
        <Route path="/quizzes" element={<Quizzes />} />
        <Route path="/quizzes/:id" element={<QuizAttempt />} />
        <Route path="/quiz-result" element={<QuizResult />} />
        <Route path="/viva" element={<Viva />} />
        <Route path="/notes" element={<Notes />} />
        <Route path="/progress" element={<Progress />} />
        <Route path="/goals" element={<Goals />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/profile" element={<Profile />} />
      </Route>

      {/* Instructor Portal Routes (Strict Role Protection) */}
      <Route
        path="/instructor"
        element={
          <ProtectedRoute requiredRole="instructor">
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/instructor/dashboard" replace />} />
        <Route path="dashboard" element={<InstructorDashboard />} />
        <Route path="assessments" element={<Assessments />} />
        <Route path="assessments/create" element={<CreateAssessment />} />
        <Route path="students" element={<Students />} />
        <Route path="analytics" element={<ClassAnalytics />} />
        <Route path="feedback" element={<Feedback />} />
        <Route path="reports" element={<Reports />} />
      </Route>

      <Route path="/404" element={<NotFound />} />
      <Route path="*" element={<Navigate to="/404" replace />} />
    </Routes>
  )
}

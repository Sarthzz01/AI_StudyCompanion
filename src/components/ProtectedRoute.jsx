import { Navigate, useLocation, Link } from 'react-router-dom'
import { ShieldAlert, ArrowLeft } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import LoadingSpinner from './LoadingSpinner.jsx'
import Button from './Button.jsx'

export default function ProtectedRoute({ children, requiredRole }) {
  const { user, isAuthenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-ink-50 dark:bg-ink-950">
        <LoadingSpinner label="Checking credentials…" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  // Role validation check
  if (requiredRole) {
    const userRole = (user?.role || 'student').toLowerCase()
    const allowed = Array.isArray(requiredRole)
      ? requiredRole.map((r) => r.toLowerCase()).includes(userRole)
      : userRole === requiredRole.toLowerCase() || userRole === 'admin'

    if (!allowed) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-ink-50 p-6 text-center dark:bg-ink-950">
          <div className="mx-auto max-w-md rounded-2xl border border-rose-200 bg-white p-8 shadow-sm dark:border-rose-900/50 dark:bg-ink-900">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-100 text-rose-600 dark:bg-rose-950/60 dark:text-rose-400">
              <ShieldAlert size={28} />
            </div>
            <h2 className="mt-4 text-xl font-bold text-ink-900 dark:text-ink-100">
              Access Restricted
            </h2>
            <p className="mt-2 text-sm text-ink-600 dark:text-ink-400">
              This section is reserved for verified <span className="font-semibold capitalize text-brand-600 dark:text-brand-400">{requiredRole}</span> accounts. Your current role is <span className="font-semibold capitalize text-ink-900 dark:text-ink-100">{user?.role || 'student'}</span>.
            </p>
            <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
              <Link to="/dashboard">
                <Button variant="primary" size="md">
                  <ArrowLeft size={16} />
                  Return to Dashboard
                </Button>
              </Link>
            </div>
          </div>
        </div>
      )
    }
  }

  return children
}

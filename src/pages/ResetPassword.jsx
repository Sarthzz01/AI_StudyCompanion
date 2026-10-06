import { useState, useMemo } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { Lock, Eye, EyeOff, CheckCircle2, AlertCircle, GraduationCap, ArrowRight } from 'lucide-react'
import Input from '../components/Input.jsx'
import Button from '../components/Button.jsx'
import { resetPassword } from '../services/api.js'
import { useToast } from '../context/ToastContext.jsx'

export default function ResetPassword() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const navigate = useNavigate()
  const toast = useToast()

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  // Password strength calculation
  const strength = useMemo(() => {
    if (!password) return 0
    let score = 0
    if (password.length >= 6) score += 1
    if (password.length >= 8) score += 1
    if (/[0-9]/.test(password)) score += 1
    if (/[^A-Za-z0-9]/.test(password)) score += 1
    return score // 0 to 4
  }, [password])

  const strengthLabel = useMemo(() => {
    switch (strength) {
      case 0:
      case 1:
        return { text: 'Weak', color: 'bg-rose-500', width: '25%' }
      case 2:
        return { text: 'Fair', color: 'bg-amber-500', width: '50%' }
      case 3:
        return { text: 'Good', color: 'bg-blue-500', width: '75%' }
      case 4:
        return { text: 'Strong', color: 'bg-emerald-500', width: '100%' }
      default:
        return { text: '', color: '', width: '0%' }
    }
  }, [strength])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!token) {
      setError('Missing password reset token. Please use the link provided in your email.')
      return
    }

    if (!password || password.length < 6) {
      setError('Password must be at least 6 characters long.')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match. Please re-enter.')
      return
    }

    setLoading(true)
    try {
      await resetPassword({ token, new_password: password })
      setSuccess(true)
      toast('Password reset successfully! You can now log in.', 'success')
    } catch (err) {
      setError(err.message || 'Failed to reset password. The link may have expired.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink-50 p-4 dark:bg-ink-950">
      <div className="w-full max-w-md">
        {/* Brand Header */}
        <Link to="/" className="mb-6 flex items-center justify-center gap-2.5">
          <span className="rounded-lg bg-brand-600 p-1.5 text-white">
            <GraduationCap size={18} />
          </span>
          <span className="font-display text-base font-semibold">AI Study Companion</span>
        </Link>

        <div className="card">
          {!token ? (
            /* Missing Token Warning */
            <div className="text-center py-4">
              <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-rose-100 text-rose-600 dark:bg-rose-950/50 dark:text-rose-400">
                <AlertCircle size={26} />
              </div>
              <h2 className="font-display text-xl font-bold text-ink-900 dark:text-white">
                Invalid Reset Link
              </h2>
              <p className="mt-2 text-sm text-ink-600 dark:text-ink-400">
                This password reset link is invalid or incomplete because it is missing a security token.
              </p>
              <div className="mt-6 flex flex-col gap-2.5">
                <Link to="/login">
                  <Button variant="primary" className="w-full">
                    Back to Login
                  </Button>
                </Link>
              </div>
            </div>
          ) : success ? (
            /* Success State */
            <div className="text-center py-4">
              <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 dark:bg-emerald-950/50 dark:text-emerald-400">
                <CheckCircle2 size={28} />
              </div>
              <h2 className="font-display text-xl font-bold text-ink-900 dark:text-white">
                Password Reset Complete
              </h2>
              <p className="mt-2 text-sm text-ink-600 dark:text-ink-400">
                Your password has been successfully updated. You can now log in with your new credentials.
              </p>
              <div className="mt-6">
                <Button
                  variant="primary"
                  onClick={() => navigate('/login')}
                  className="w-full"
                >
                  Proceed to Login <ArrowRight size={16} className="ml-1.5" />
                </Button>
              </div>
            </div>
          ) : (
            /* Password Reset Form */
            <div>
              <div className="mb-5">
                <h2 className="font-display text-xl font-bold text-ink-900 dark:text-white">
                  Reset Your Password
                </h2>
                <p className="mt-1 text-sm text-ink-600 dark:text-ink-400">
                  Choose a new, strong password for your account.
                </p>
              </div>

              {error && (
                <div className="mb-4 flex items-start gap-2.5 rounded-xl border border-rose-200 bg-rose-50/80 p-3 text-xs text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300">
                  <AlertCircle size={16} className="shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <div className="relative">
                    <Input
                      label="New Password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="At least 6 characters"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      icon={Lock}
                      autoFocus
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-[38px] text-ink-400 hover:text-ink-600 dark:hover:text-ink-300"
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>

                  {/* Password Strength Indicator */}
                  {password && (
                    <div className="mt-2">
                      <div className="flex items-center justify-between text-xs text-ink-500 mb-1">
                        <span>Strength</span>
                        <span className="font-semibold text-ink-700 dark:text-ink-300">
                          {strengthLabel.text}
                        </span>
                      </div>
                      <div className="h-1.5 w-full rounded-full bg-ink-100 dark:bg-ink-800 overflow-hidden">
                        <div
                          className={`h-full transition-all duration-300 ${strengthLabel.color}`}
                          style={{ width: strengthLabel.width }}
                        />
                      </div>
                    </div>
                  )}
                </div>

                <Input
                  label="Confirm New Password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Re-enter your new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  icon={Lock}
                />

                <Button type="submit" loading={loading} className="w-full mt-4">
                  Update Password
                </Button>
              </form>

              <p className="mt-5 text-center text-xs text-ink-500">
                Remember your password?{' '}
                <Link to="/login" className="font-medium text-brand-600 hover:text-brand-700 dark:text-brand-400">
                  Back to Login
                </Link>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

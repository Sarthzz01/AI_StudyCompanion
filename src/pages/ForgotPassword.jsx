import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Mail, ArrowLeft, CheckCircle2, AlertCircle, ExternalLink, GraduationCap } from 'lucide-react'
import Input from '../components/Input.jsx'
import Button from '../components/Button.jsx'
import { requestPasswordReset } from '../services/api.js'
import { useToast } from '../context/ToastContext.jsx'

export default function ForgotPassword() {
  const toast = useToast()
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    const cleanEmail = email.trim()
    if (!cleanEmail) {
      setError('Please enter your email address.')
      return
    }
    if (!/^\S+@\S+\.\S+$/.test(cleanEmail)) {
      setError('Please enter a valid email address.')
      return
    }

    setLoading(true)
    try {
      const data = await requestPasswordReset(cleanEmail)
      setResult(data)
      toast('Password reset link processed.', 'info')
    } catch (err) {
      setError(err.message || 'Failed to send reset link. Please try again.')
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
          {!result ? (
            <div>
              <div className="mb-5">
                <div className="mb-3 inline-flex rounded-xl bg-brand-50 p-2.5 text-brand-600 dark:bg-brand-950/50 dark:text-brand-400">
                  <Mail size={22} />
                </div>
                <h2 className="font-display text-xl font-bold text-ink-900 dark:text-white">
                  Forgot Password
                </h2>
                <p className="mt-1 text-sm text-ink-600 dark:text-ink-400">
                  Enter your registered email address and we'll send you a link to reset your password.
                </p>
              </div>

              {error && (
                <div className="mb-4 flex items-start gap-2.5 rounded-xl border border-rose-200 bg-rose-50/80 p-3 text-xs text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300">
                  <AlertCircle size={16} className="shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <Input
                  label="Email address"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value)
                    if (error) setError('')
                  }}
                  icon={Mail}
                  autoFocus
                />

                <Button type="submit" loading={loading} className="w-full mt-4">
                  Send Reset Link
                </Button>
              </form>

              <p className="mt-5 text-center text-xs text-ink-500">
                Remember your password?{' '}
                <Link to="/login" className="font-medium text-brand-600 hover:text-brand-700 dark:text-brand-400">
                  Back to Login
                </Link>
              </p>
            </div>
          ) : (
            <div className="py-2 text-center">
              <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 dark:bg-emerald-950/50 dark:text-emerald-400">
                <CheckCircle2 size={26} />
              </div>
              <h3 className="font-display text-lg font-bold text-ink-900 dark:text-white">
                Check your inbox
              </h3>
              <p className="mt-2 text-sm text-ink-600 dark:text-ink-300">
                {result.message}
              </p>

              {result.dev_reset_link && (
                <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50/80 p-3.5 text-left text-xs dark:border-amber-900/50 dark:bg-amber-950/30">
                  <div className="flex items-center gap-1.5 font-semibold text-amber-900 dark:text-amber-300">
                    <AlertCircle size={14} /> Local Dev Helper (No SMTP configured)
                  </div>
                  <p className="mt-1 text-ink-600 dark:text-ink-400">
                    Click the link below or check your server terminal logs:
                  </p>
                  <a
                    href={result.dev_reset_link}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-2 inline-flex items-center gap-1 font-medium text-brand-600 underline hover:text-brand-700 dark:text-brand-400"
                  >
                    Open Reset Page <ExternalLink size={12} />
                  </a>
                </div>
              )}

              <div className="mt-6 flex flex-col gap-2">
                <Link to="/login">
                  <Button variant="primary" className="w-full">
                    Return to Login
                  </Button>
                </Link>
                <Button
                  variant="ghost"
                  onClick={() => {
                    setResult(null)
                    setEmail('')
                  }}
                  className="w-full"
                >
                  Send another link
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

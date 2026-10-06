import { useState } from 'react'
import { Mail, ArrowLeft, CheckCircle2, AlertCircle, ExternalLink, X } from 'lucide-react'
import Input from './Input.jsx'
import Button from './Button.jsx'
import { requestPasswordReset } from '../services/api.js'
import { useToast } from '../context/ToastContext.jsx'

export default function ForgotPasswordModal({ isOpen, onClose }) {
  const toast = useToast()
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  if (!isOpen) return null

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

  const handleResetState = () => {
    setResult(null)
    setEmail('')
    setError('')
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-950/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-md rounded-2xl border border-ink-200/80 bg-white p-6 shadow-2xl dark:border-ink-800 dark:bg-ink-900">
        {/* Close Button */}
        <button
          type="button"
          onClick={handleResetState}
          className="absolute right-4 top-4 rounded-lg p-1.5 text-ink-400 hover:bg-ink-100 hover:text-ink-600 dark:hover:bg-ink-800 dark:hover:text-ink-200"
          aria-label="Close"
        >
          <X size={18} />
        </button>

        {!result ? (
          <div>
            <div className="mb-5">
              <div className="mb-3 inline-flex rounded-xl bg-brand-50 p-2.5 text-brand-600 dark:bg-brand-950/50 dark:text-brand-400">
                <Mail size={22} />
              </div>
              <h3 className="font-display text-xl font-bold text-ink-900 dark:text-white">
                Forgot your password?
              </h3>
              <p className="mt-1 text-sm text-ink-600 dark:text-ink-400">
                Enter your registered email address below. We'll send you a secure link to reset your password.
              </p>
            </div>

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
                error={error}
                autoFocus
              />

              <div className="mt-6 flex flex-col gap-2.5">
                <Button type="submit" loading={loading} className="w-full">
                  Send Reset Link
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={handleResetState}
                  className="w-full"
                >
                  <ArrowLeft size={16} className="mr-1.5" /> Back to Login
                </Button>
              </div>
            </form>
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

            {/* Development Mode Helper Banner */}
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

            <div className="mt-6">
              <Button variant="secondary" onClick={handleResetState} className="w-full">
                Done
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

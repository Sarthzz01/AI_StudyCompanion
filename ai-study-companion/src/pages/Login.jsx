import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Mail, Lock, Eye, EyeOff, GraduationCap } from 'lucide-react'
import Input from '../components/Input.jsx'
import Button from '../components/Button.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { useToast } from '../context/ToastContext.jsx'

export default function Login() {
  const { login } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const location = useLocation()

  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [showPassword, setShowPassword] = useState(false)
  const [remember, setRemember] = useState(true)
  const [loading, setLoading] = useState(false)

  const update = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const validate = () => {
    const next = {}
    if (!form.email.trim()) next.email = 'Enter your email address.'
    else if (!/^\S+@\S+\.\S+$/.test(form.email)) next.email = 'That email address does not look right.'
    if (!form.password) next.password = 'Enter your password.'
    else if (form.password.length < 6) next.password = 'Passwords are at least 6 characters.'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const onSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    try {
      await login(form)
      toast('Logged in', 'success')
      navigate(location.state?.from || '/dashboard', { replace: true })
    } catch (err) {
      toast(err.message || 'Login failed. Check your details and try again.', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink-50 p-4 dark:bg-ink-950">
      <div className="w-full max-w-md">
        <Link to="/" className="mb-6 flex items-center justify-center gap-2.5">
          <span className="rounded-lg bg-brand-600 p-1.5 text-white">
            <GraduationCap size={18} />
          </span>
          <span className="font-display text-base font-semibold">AI Study Companion</span>
        </Link>

        <div className="card">
          <h1 className="font-display text-xl font-semibold">Welcome back</h1>
          <p className="muted mt-1">Log in to pick up where you left off.</p>

          <form onSubmit={onSubmit} className="mt-6 space-y-4" noValidate>
            <Input
              label="Email"
              type="email"
              icon={Mail}
              placeholder="you@college.edu"
              value={form.email}
              onChange={update('email')}
              error={errors.email}
              autoComplete="email"
            />

            <div>
              <div className="relative">
                <Input
                  label="Password"
                  type={showPassword ? 'text' : 'password'}
                  icon={Lock}
                  placeholder="Your password"
                  value={form.password}
                  onChange={update('password')}
                  error={errors.password}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((s) => !s)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  className="absolute right-3 top-[34px] text-ink-400 hover:text-ink-600"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm text-ink-600 dark:text-ink-400">
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                  className="h-4 w-4 rounded accent-brand-600"
                />
                Remember me
              </label>
              <button
                type="button"
                onClick={() => toast('Password reset needs the backend. It is mocked for now.', 'info')}
                className="text-sm font-medium text-brand-600 hover:text-brand-700 dark:text-brand-400"
              >
                Forgot password?
              </button>
            </div>

            <Button type="submit" className="w-full" loading={loading}>
              Log in
            </Button>
          </form>

          <p className="muted mt-6 text-center">
            New here?{' '}
            <Link to="/signup" className="font-medium text-brand-600 hover:text-brand-700 dark:text-brand-400">
              Create an account
            </Link>
          </p>
        </div>

        <p className="mt-4 text-center text-xs text-ink-500">
          Authentication is mocked — any valid email and a 6-character password will sign you in.
        </p>
      </div>
    </div>
  )
}

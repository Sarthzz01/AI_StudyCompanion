import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Mail, Lock, User, GraduationCap, Eye, EyeOff } from 'lucide-react'
import Input from '../components/Input.jsx'
import Button from '../components/Button.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { useToast } from '../context/ToastContext.jsx'

export default function Signup() {
  const { signup } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()

  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' })
  const [accepted, setAccepted] = useState(false)
  const [errors, setErrors] = useState({})
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)

  const update = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const validate = () => {
    const next = {}
    if (!form.name.trim()) next.name = 'Enter your name.'
    if (!form.email.trim()) next.email = 'Enter your email address.'
    else if (!/^\S+@\S+\.\S+$/.test(form.email)) next.email = 'That email address does not look right.'
    if (form.password.length < 6) next.password = 'Use at least 6 characters.'
    if (form.confirm !== form.password) next.confirm = 'Both passwords must match.'
    if (!accepted) next.terms = 'Accept the terms to continue.'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const onSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    try {
      await signup(form)
      toast('Account created', 'success')
      navigate('/dashboard', { replace: true })
    } catch (err) {
      toast(err.message || 'We could not create the account. Try again.', 'error')
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
          <h1 className="font-display text-xl font-semibold">Create your account</h1>
          <p className="muted mt-1">Start studying from your own material in a couple of minutes.</p>

          <form onSubmit={onSubmit} className="mt-6 space-y-4" noValidate>
            <Input label="Name" icon={User} placeholder="Your full name" value={form.name} onChange={update('name')} error={errors.name} />
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
            <div className="relative">
              <Input
                label="Password"
                type={showPassword ? 'text' : 'password'}
                icon={Lock}
                placeholder="At least 6 characters"
                value={form.password}
                onChange={update('password')}
                error={errors.password}
                autoComplete="new-password"
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
            <Input
              label="Confirm password"
              type={showPassword ? 'text' : 'password'}
              icon={Lock}
              placeholder="Repeat your password"
              value={form.confirm}
              onChange={update('confirm')}
              error={errors.confirm}
              autoComplete="new-password"
            />

            <div>
              <label className="flex items-start gap-2 text-sm text-ink-600 dark:text-ink-400">
                <input
                  type="checkbox"
                  checked={accepted}
                  onChange={(e) => setAccepted(e.target.checked)}
                  className="mt-0.5 h-4 w-4 rounded accent-brand-600"
                />
                I agree to the terms of use and privacy policy.
              </label>
              {errors.terms && <p className="mt-1.5 text-xs text-rose-600">{errors.terms}</p>}
            </div>

            <Button type="submit" className="w-full" loading={loading}>
              Create account
            </Button>
          </form>

          <p className="muted mt-6 text-center">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-brand-600 hover:text-brand-700 dark:text-brand-400">
              Log in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

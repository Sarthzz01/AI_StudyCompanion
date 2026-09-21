import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Camera, LogOut, Moon, Sun, Lock, RefreshCw } from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import Card, { CardHeader } from '../components/Card.jsx'
import Input from '../components/Input.jsx'
import Button from '../components/Button.jsx'
import Select from '../components/Select.jsx'
import Modal from '../components/Modal.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { useTheme } from '../context/ThemeContext.jsx'
import { useStudyData } from '../context/StudyDataContext.jsx'
import { useToast } from '../context/ToastContext.jsx'
import { readStorage, writeStorage } from '../utils/storage.js'
import { getProfile, updateProfile, changeUserPassword } from '../services/api.js'

export default function Profile() {
  const { user, updateUser, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const { resetProgress } = useStudyData()
  const toast = useToast()
  const navigate = useNavigate()

  const [form, setForm] = useState({ name: user?.name || '', email: user?.email || '' })
  const [errors, setErrors] = useState({})
  const [preferences, setPreferences] = useState(() =>
    readStorage('preferences', { difficulty: 'medium', sessionLength: '30', quizAlerts: true, goalAlerts: true, weeklySummary: false })
  )
  const [passwordOpen, setPasswordOpen] = useState(false)
  const [passwords, setPasswords] = useState({ current: '', next: '', confirm: '' })
  const [saving, setSaving] = useState(false)
  const [changingPassword, setChangingPassword] = useState(false)

  useEffect(() => {
    getProfile()
      .then((profile) => {
        if (profile.full_name) {
          setForm({ name: profile.full_name, email: profile.email })
          updateUser({ name: profile.full_name, email: profile.email, joined: profile.joined })
        }
        if (profile.preferences && Object.keys(profile.preferences).length > 0) {
          setPreferences(profile.preferences)
          writeStorage('preferences', profile.preferences)
        }
      })
      .catch((err) => {
        console.warn('Could not load profile from backend, using session data:', err.message)
      })
  }, [])

  const savePreferences = (next) => {
    setPreferences(next)
    writeStorage('preferences', next)
    updateProfile({ preferences: next }).catch(() => {
      // Best-effort sync
    })
  }

  const saveProfile = async () => {
    const next = {}
    if (!form.name.trim()) next.name = 'Enter your name.'
    if (!/^\S+@\S+\.\S+$/.test(form.email)) next.email = 'That email address does not look right.'
    setErrors(next)
    if (Object.keys(next).length) return

    setSaving(true)
    try {
      await updateProfile({ name: form.name.trim(), preferences })
      updateUser({ name: form.name.trim() })
      toast('Profile saved', 'success')
    } catch (err) {
      toast(err.message || 'Failed to update profile.', 'error')
    } finally {
      setSaving(false)
    }
  }

  const changePassword = async () => {
    if (!passwords.current) return toast('Enter your current password.', 'error')
    if (passwords.next.length < 6) return toast('Use at least 6 characters for the new password.', 'error')
    if (passwords.next !== passwords.confirm) return toast('Both new passwords must match.', 'error')

    setChangingPassword(true)
    try {
      await changeUserPassword({
        current_password: passwords.current,
        new_password: passwords.next,
      })
      setPasswords({ current: '', next: '', confirm: '' })
      setPasswordOpen(false)
      toast('Password changed successfully', 'success')
    } catch (err) {
      toast(err.message || 'Failed to change password.', 'error')
    } finally {
      setChangingPassword(false)
    }
  }

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <>
      <PageHeader title="Profile" subtitle="Your account details and study preferences." />

      <div className="grid gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader title="Account" subtitle="Manage your personal details and learning settings." />
          <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
            <div className="flex flex-col items-center gap-2">
              <div className="relative">
                <span className="flex h-20 w-20 items-center justify-center rounded-full bg-brand-600 font-display text-2xl font-semibold text-white">
                  {(user?.name || 'S').charAt(0).toUpperCase()}
                </span>
                <button
                  onClick={() => toast('Photo upload will be available with cloud storage.', 'info')}
                  aria-label="Change photo"
                  className="absolute -bottom-1 -right-1 rounded-full border border-ink-200 bg-white p-1.5 text-ink-600 shadow-sm dark:border-ink-700 dark:bg-ink-800 dark:text-ink-200"
                >
                  <Camera size={14} />
                </button>
              </div>
              <p className="muted">Member since {user?.joined || '2026'}</p>
            </div>

            <div className="flex-1 space-y-4">
              <Input label="Name" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} error={errors.name} />
              <Input
                label="Email"
                type="email"
                value={form.email}
                disabled
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                error={errors.email}
                hint="Account email address"
              />
              <div className="flex flex-wrap gap-2">
                <Button onClick={saveProfile} loading={saving}>Save changes</Button>
                <Button variant="secondary" icon={Lock} onClick={() => setPasswordOpen(true)}>
                  Change password
                </Button>
              </div>
            </div>
          </div>
        </Card>

        <Card className="h-fit">
          <CardHeader title="Appearance" />
          <button
            onClick={toggleTheme}
            className="flex w-full items-center justify-between rounded-xl border border-ink-200 p-4 text-sm font-medium hover:bg-ink-50 dark:border-ink-800 dark:hover:bg-ink-800/50"
          >
            <span className="flex items-center gap-2.5">
              {theme === 'dark' ? <Moon size={16} /> : <Sun size={16} />}
              {theme === 'dark' ? 'Dark mode' : 'Light mode'}
            </span>
            <span className="muted">Switch</span>
          </button>

          <CardHeader title="Study preferences" />
          <div className="space-y-4">
            <Select
              label="Default quiz difficulty"
              options={['easy', 'medium', 'hard']}
              value={preferences.difficulty}
              onChange={(e) => savePreferences({ ...preferences, difficulty: e.target.value })}
            />
            <Select
              label="Preferred session length"
              options={[
                { value: '15', label: '15 minutes' },
                { value: '30', label: '30 minutes' },
                { value: '60', label: '60 minutes' },
              ]}
              value={preferences.sessionLength}
              onChange={(e) => savePreferences({ ...preferences, sessionLength: e.target.value })}
            />
          </div>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader title="Notification settings" subtitle="Choose what is worth interrupting you for." />
          <div className="space-y-3">
            {[
              { key: 'quizAlerts', label: 'Quiz results', hint: 'When a quiz is scored.' },
              { key: 'goalAlerts', label: 'Goal updates', hint: 'When you complete a study goal.' },
              { key: 'weeklySummary', label: 'Weekly summary', hint: 'A recap of accuracy and study time every Sunday.' },
            ].map(({ key, label, hint }) => (
              <label
                key={key}
                className="flex cursor-pointer items-center justify-between gap-4 rounded-xl border border-ink-200 p-4 dark:border-ink-800"
              >
                <span>
                  <span className="block text-sm font-medium">{label}</span>
                  <span className="muted">{hint}</span>
                </span>
                <input
                  type="checkbox"
                  checked={Boolean(preferences[key])}
                  onChange={(e) => savePreferences({ ...preferences, [key]: e.target.checked })}
                  className="h-4 w-4 accent-brand-600"
                />
              </label>
            ))}
          </div>
        </Card>

        <Card className="h-fit">
          <CardHeader title="Session" />
          <div className="space-y-2">
            <Button
              variant="secondary"
              icon={RefreshCw}
              className="w-full"
              onClick={() => {
                resetProgress()
                toast('Progress reset to the sample data', 'success')
              }}
            >
              Reset demo progress
            </Button>
            <Button variant="danger" icon={LogOut} className="w-full" onClick={handleLogout}>
              Log out
            </Button>
          </div>
        </Card>
      </div>

      <Modal
        open={passwordOpen}
        onClose={() => setPasswordOpen(false)}
        title="Change password"
        description="Enter your current password and pick a new one."
        footer={
          <>
            <Button variant="secondary" onClick={() => setPasswordOpen(false)}>
              Cancel
            </Button>
            <Button onClick={changePassword} loading={changingPassword}>Change password</Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="Current password"
            type="password"
            value={passwords.current}
            onChange={(e) => setPasswords((p) => ({ ...p, current: e.target.value }))}
          />
          <Input
            label="New password"
            type="password"
            value={passwords.next}
            onChange={(e) => setPasswords((p) => ({ ...p, next: e.target.value }))}
            hint="At least 6 characters."
          />
          <Input
            label="Confirm new password"
            type="password"
            value={passwords.confirm}
            onChange={(e) => setPasswords((p) => ({ ...p, confirm: e.target.value }))}
          />
        </div>
      </Modal>
    </>
  )
}

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Camera,
  LogOut,
  Moon,
  Sun,
  Lock,
  RefreshCw,
  ShieldCheck,
  GraduationCap,
  Sparkles,
  LayoutDashboard,
  Users,
  BarChart3,
  ArrowRight,
  BookOpenCheck
} from 'lucide-react'
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

  const [role, setRole] = useState(user?.role || 'student')
  const isInstructor =
    (role || user?.role || '').toLowerCase() === 'instructor' ||
    (role || user?.role || '').toLowerCase() === 'admin'

  const [form, setForm] = useState({
    name: user?.name || '',
    email: user?.email || '',
    bio: user?.bio || '',
    title: 'Senior Professor of Computer Science & AI',
    department: 'Department of Computer Science & AI',
    officeHours: 'Mon & Wed 2:00 PM – 4:00 PM (Room CS-304 / Online)',
  })
  const [errors, setErrors] = useState({})

  const [preferences, setPreferences] = useState(() =>
    readStorage('preferences', {
      difficulty: 'medium',
      sessionLength: '30',
      quizAlerts: true,
      goalAlerts: true,
      weeklySummary: false,
      gradingScale: 'percentage',
      publishingPolicy: 'auto',
      riskThreshold: '55',
      questionRigor: 'rigorous',
      submissionAlerts: true,
      atRiskAlerts: true,
      escalationAlerts: true,
      weeklyDigest: true,
      feedbackAlerts: true,
    })
  )

  const [passwordOpen, setPasswordOpen] = useState(false)
  const [passwords, setPasswords] = useState({ current: '', next: '', confirm: '' })
  const [saving, setSaving] = useState(false)
  const [changingPassword, setChangingPassword] = useState(false)

  useEffect(() => {
    getProfile()
      .then((profile) => {
        if (profile.role) {
          setRole(profile.role)
        }
        const userBio =
          profile.bio ||
          (profile.role === 'instructor'
            ? 'Senior Professor of Computer Science. Research focus on theoretical computing, cryptography, and intelligent systems. Dedicated to mastery-based active learning.'
            : '')
        const prefs = profile.preferences || {}

        setForm((prev) => ({
          ...prev,
          name: profile.full_name || prev.name,
          email: profile.email || prev.email,
          bio: userBio,
          title:
            prefs.title ||
            (profile.role === 'instructor' ? 'Senior Professor of Computer Science & AI' : ''),
          department: prefs.department || prev.department,
          officeHours: prefs.officeHours || prev.officeHours,
        }))

        updateUser({
          name: profile.full_name,
          email: profile.email,
          joined: profile.joined,
          role: profile.role,
          bio: userBio,
        })

        if (profile.preferences && Object.keys(profile.preferences).length > 0) {
          setPreferences((prev) => ({ ...prev, ...profile.preferences }))
          writeStorage('preferences', { ...preferences, ...profile.preferences })
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
      const updatedPrefs = {
        ...preferences,
        ...(isInstructor
          ? {
              title: form.title,
              department: form.department,
              officeHours: form.officeHours,
            }
          : {}),
      }
      await updateProfile({
        name: form.name.trim(),
        bio: form.bio.trim(),
        preferences: updatedPrefs,
      })
      setPreferences(updatedPrefs)
      writeStorage('preferences', updatedPrefs)
      updateUser({
        name: form.name.trim(),
        bio: form.bio.trim(),
      })
      toast('Profile saved successfully', 'success')
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
    <div className="space-y-6">
      <PageHeader
        title={isInstructor ? 'Instructor Profile' : 'Profile'}
        subtitle={
          isInstructor
            ? 'Manage your faculty credentials, academic department, teaching policies, and cohort notifications.'
            : 'Your account details and study preferences.'
        }
        actions={
          isInstructor && (
            <div className="flex items-center gap-2.5">
              <span className="hidden sm:inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 dark:border-emerald-800/80 dark:bg-emerald-950/50 dark:text-emerald-300">
                <ShieldCheck size={14} className="text-emerald-600 dark:text-emerald-400" />
                Verified Faculty
              </span>
              <Button
                variant="secondary"
                size="sm"
                icon={ArrowRight}
                onClick={() => navigate('/instructor/dashboard')}
              >
                Instructor Portal
              </Button>
            </div>
          )
        }
      />

      <div className="grid gap-5 lg:grid-cols-3">
        {/* Left Column: Account / Faculty Credentials */}
        <Card className="lg:col-span-2">
          <CardHeader
            title={isInstructor ? 'Faculty Credentials & Identity' : 'Account'}
            subtitle={
              isInstructor
                ? 'Public faculty details visible to students across assessments, course materials, and consultations.'
                : 'Manage your personal details and learning settings.'
            }
          />
          <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
            <div className="flex flex-col items-center gap-2 sm:w-44 text-center">
              <div className="relative">
                <span className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-tr from-brand-600 via-indigo-600 to-purple-600 font-display text-2xl font-bold text-white shadow-md shadow-brand-500/20">
                  {(form.name || user?.name || 'I').charAt(0).toUpperCase()}
                </span>
                <button
                  onClick={() => toast('Photo upload will be synced with university credentials.', 'info')}
                  aria-label="Change photo"
                  className="absolute -bottom-1 -right-1 rounded-full border border-ink-200 bg-white p-1.5 text-ink-600 shadow-sm transition hover:scale-105 hover:text-brand-600 dark:border-ink-700 dark:bg-ink-800 dark:text-ink-200"
                >
                  <Camera size={14} />
                </button>
              </div>

              {isInstructor ? (
                <div className="mt-1 flex flex-col items-center gap-1">
                  <span className="inline-flex items-center gap-1 rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-semibold text-indigo-700 dark:bg-indigo-950/80 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                    <GraduationCap size={13} />
                    Instructor
                  </span>
                  <span className="text-[11px] font-mono text-ink-400">FAC-ID: #8924</span>
                  <p className="text-xs text-ink-500 dark:text-ink-400">
                    Faculty since {user?.joined || 'September 2026'}
                  </p>
                </div>
              ) : (
                <p className="muted text-xs">Member since {user?.joined || 'September 2026'}</p>
              )}
            </div>

            <div className="flex-1 space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <Input
                  label="Full name"
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  error={errors.name}
                />
                <Input
                  label="Institutional Email"
                  type="email"
                  value={form.email}
                  disabled
                  error={errors.email}
                  hint={isInstructor ? 'Verified university faculty address' : 'Account email address'}
                />
              </div>

              {isInstructor && (
                <>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <Input
                      label="Academic title / Designation"
                      value={form.title}
                      placeholder="e.g. Senior Professor of Computer Science"
                      onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                    />
                    <Select
                      label="Department / Faculty"
                      options={[
                        'Department of Computer Science & AI',
                        'Department of Software Engineering',
                        'Department of Mathematics & Computing',
                        'Department of Data Science & Analytics',
                        'School of Electrical & Information Sciences',
                      ]}
                      value={form.department}
                      onChange={(e) => setForm((f) => ({ ...f, department: e.target.value }))}
                    />
                  </div>

                  <Input
                    label="Office hours & Student consultation"
                    value={form.officeHours}
                    placeholder="e.g. Mon & Wed 2:00 PM – 4:00 PM (Room CS-304 / Online)"
                    onChange={(e) => setForm((f) => ({ ...f, officeHours: e.target.value }))}
                    hint="Displayed to students on your course overview and assignments."
                  />

                  <div>
                    <label className="label">Faculty Bio & Teaching Statement</label>
                    <textarea
                      rows={3}
                      value={form.bio}
                      placeholder="Share your academic background, research interests, and teaching philosophy..."
                      onChange={(e) => setForm((f) => ({ ...f, bio: e.target.value }))}
                      className="field resize-none"
                    />
                    <p className="mt-1.5 text-xs text-ink-500">
                      Brief summary presented on assessment rubrics and student course materials.
                    </p>
                  </div>
                </>
              )}

              <div className="flex flex-wrap gap-2 pt-2">
                <Button onClick={saveProfile} loading={saving}>
                  Save changes
                </Button>
                <Button variant="secondary" icon={Lock} onClick={() => setPasswordOpen(true)}>
                  Change password
                </Button>
              </div>
            </div>
          </div>
        </Card>

        {/* Right Top Column: Appearance & Preferences */}
        <Card className="h-fit">
          <CardHeader title="Appearance" />
          <button
            onClick={toggleTheme}
            className="flex w-full items-center justify-between rounded-xl border border-ink-200 p-4 text-sm font-medium hover:bg-ink-50 dark:border-ink-800 dark:hover:bg-ink-800/50 transition-colors"
          >
            <span className="flex items-center gap-2.5">
              {theme === 'dark' ? <Moon size={16} className="text-indigo-400" /> : <Sun size={16} className="text-amber-500" />}
              {theme === 'dark' ? 'Dark mode' : 'Light mode'}
            </span>
            <span className="muted font-normal">Switch</span>
          </button>

          {isInstructor ? (
            <>
              <div className="mt-6">
                <CardHeader
                  title="Teaching & Grading Policies"
                  subtitle="Default evaluation policies applied to assessments."
                />
              </div>
              <div className="space-y-4">
                <Select
                  label="Default grading scale"
                  options={[
                    { value: 'percentage', label: 'Percentage scale (0–100%)' },
                    { value: 'letter', label: 'Standard Letter (A, B, C, D, F)' },
                    { value: 'mastery', label: 'Mastery based (Mastered / Novice)' },
                    { value: 'pass_fail', label: 'Pass / Fail benchmark (60%)' },
                  ]}
                  value={preferences.gradingScale || 'percentage'}
                  onChange={(e) => savePreferences({ ...preferences, gradingScale: e.target.value })}
                />
                <Select
                  label="Assessment publishing policy"
                  options={[
                    { value: 'auto', label: 'Auto-publish AI scored results instantly' },
                    { value: 'review_flags', label: 'Hold flagged & borderline (<60%)' },
                    { value: 'manual', label: 'Manual instructor approval required' },
                  ]}
                  value={preferences.publishingPolicy || 'auto'}
                  onChange={(e) => savePreferences({ ...preferences, publishingPolicy: e.target.value })}
                />
                <Select
                  label="At-risk alert threshold"
                  options={[
                    { value: '65', label: 'Strict (< 65% topic mastery)' },
                    { value: '55', label: 'Standard (< 55% topic mastery)' },
                    { value: '45', label: 'Lenient (< 45% topic mastery)' },
                  ]}
                  value={preferences.riskThreshold || '55'}
                  onChange={(e) => savePreferences({ ...preferences, riskThreshold: e.target.value })}
                />
                <Select
                  label="AI question rigor calibration"
                  options={[
                    { value: 'rigorous', label: 'Advanced & Rigorous (University level)' },
                    { value: 'balanced', label: 'Balanced Academic (Standard syllabus)' },
                    { value: 'foundational', label: 'Foundational & Practical' },
                  ]}
                  value={preferences.questionRigor || 'rigorous'}
                  onChange={(e) => savePreferences({ ...preferences, questionRigor: e.target.value })}
                />
              </div>
            </>
          ) : (
            <>
              <div className="mt-6">
                <CardHeader title="Study preferences" />
              </div>
              <div className="space-y-4">
                <Select
                  label="Default quiz difficulty"
                  options={['easy', 'medium', 'hard']}
                  value={preferences.difficulty || 'medium'}
                  onChange={(e) => savePreferences({ ...preferences, difficulty: e.target.value })}
                />
                <Select
                  label="Preferred session length"
                  options={[
                    { value: '15', label: '15 minutes' },
                    { value: '30', label: '30 minutes' },
                    { value: '60', label: '60 minutes' },
                  ]}
                  value={preferences.sessionLength || '30'}
                  onChange={(e) => savePreferences({ ...preferences, sessionLength: e.target.value })}
                />
              </div>
            </>
          )}
        </Card>

        {/* Bottom Left: Notification Settings */}
        <Card className="lg:col-span-2">
          <CardHeader
            title={isInstructor ? 'Cohort Alerts & Notification Settings' : 'Notification settings'}
            subtitle={
              isInstructor
                ? 'Configure instant alerts and automated cohort performance updates.'
                : 'Choose what is worth interrupting you for.'
            }
          />
          <div className="space-y-3">
            {(isInstructor
              ? [
                  {
                    key: 'submissionAlerts',
                    label: 'Student Assessment Submissions',
                    hint: 'Instant notification when a student submits an exam, quiz, or completes a viva voce session.',
                  },
                  {
                    key: 'atRiskAlerts',
                    label: 'At-Risk Student Warnings',
                    hint: 'Automatic warning when a student’s topic mastery or overall score drops below your threshold.',
                  },
                  {
                    key: 'escalationAlerts',
                    label: 'AI Tutor Question Escalations',
                    hint: 'Receive alerts when students request human instructor review or dispute an AI answer.',
                  },
                  {
                    key: 'weeklyDigest',
                    label: 'Weekly Cohort Performance Digest',
                    hint: 'Comprehensive summary of student pass rates, topic mastery decay, and engagement every Monday.',
                  },
                  {
                    key: 'feedbackAlerts',
                    label: 'Course Material Inquiries & Feedback',
                    hint: 'Notifications when students post questions, remarks, or feedback on course materials.',
                  },
                ]
              : [
                  { key: 'quizAlerts', label: 'Quiz results', hint: 'When a quiz is scored.' },
                  { key: 'goalAlerts', label: 'Goal updates', hint: 'When you complete a study goal.' },
                  { key: 'weeklySummary', label: 'Weekly summary', hint: 'A recap of accuracy and study time every Sunday.' },
                ]
            ).map(({ key, label, hint }) => (
              <label
                key={key}
                className="flex cursor-pointer items-center justify-between gap-4 rounded-xl border border-ink-200 p-4 transition-colors hover:border-brand-300 dark:border-ink-800 dark:hover:border-brand-700/60"
              >
                <span>
                  <span className="block text-sm font-medium text-ink-900 dark:text-ink-100">{label}</span>
                  <span className="muted text-xs">{hint}</span>
                </span>
                <input
                  type="checkbox"
                  checked={Boolean(preferences[key] ?? true)}
                  onChange={(e) => savePreferences({ ...preferences, [key]: e.target.checked })}
                  className="h-4 w-4 accent-brand-600 cursor-pointer"
                />
              </label>
            ))}
          </div>
        </Card>

        {/* Bottom Right: Session & Workspace */}
        <Card className="h-fit">
          <CardHeader
            title={isInstructor ? 'Instructor Workspace' : 'Session'}
            subtitle={isInstructor ? 'Quick shortcuts & portal controls' : undefined}
          />
          <div className="space-y-2.5">
            {isInstructor ? (
              <>
                <Button
                  variant="secondary"
                  icon={LayoutDashboard}
                  className="w-full justify-start text-xs font-semibold"
                  onClick={() => navigate('/instructor/dashboard')}
                >
                  Instructor Dashboard
                </Button>
                <Button
                  variant="secondary"
                  icon={Sparkles}
                  className="w-full justify-start text-xs font-semibold"
                  onClick={() => navigate('/instructor/assessments/create')}
                >
                  Create AI Assessment
                </Button>
                <Button
                  variant="secondary"
                  icon={Users}
                  className="w-full justify-start text-xs font-semibold"
                  onClick={() => navigate('/instructor/students')}
                >
                  Manage Students & Roster
                </Button>
                <Button
                  variant="secondary"
                  icon={BarChart3}
                  className="w-full justify-start text-xs font-semibold"
                  onClick={() => navigate('/instructor/analytics')}
                >
                  Topic Mastery Analytics
                </Button>
                <div className="my-2 border-t border-ink-200 dark:border-ink-800" />
              </>
            ) : (
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
            )}
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
            <Button onClick={changePassword} loading={changingPassword}>
              Change password
            </Button>
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
    </div>
  )
}

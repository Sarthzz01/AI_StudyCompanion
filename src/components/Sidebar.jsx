import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  CalendarClock,
  Library,
  Bot,
  FileText,
  Layers,
  ClipboardCheck,
  Mic,
  TrendingUp,
  Target,
  Bell,
  User,
  LogOut,
  GraduationCap,
  X,
  Users,
  BarChart3,
  MessageSquareQuote,
  Sparkles,
  ShieldCheck,
  BookOpenCheck,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import { useStudyData } from '../context/StudyDataContext.jsx'

export const studentNavSections = [
  {
    title: 'Overview',
    items: [
      { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
      { to: '/study-plan', label: 'Study Plan', icon: CalendarClock },
      { to: '/materials', label: 'Study Materials', icon: Library },
    ],
  },
  {
    title: 'AI Learning Tools',
    items: [
      { to: '/tutor', label: 'AI Tutor', icon: Bot, isNew: true },
      { to: '/summaries', label: 'Summaries', icon: FileText },
      { to: '/flashcards', label: 'Flashcards', icon: Layers },
      { to: '/quizzes', label: 'Quizzes', icon: ClipboardCheck },
      { to: '/viva', label: 'AI Viva / Interview', icon: Mic, badge: 'Voice' },
    ],
  },
  {
    title: 'Performance',
    items: [
      { to: '/progress', label: 'My Progress', icon: TrendingUp },
      { to: '/goals', label: 'Goals', icon: Target },
      { to: '/notifications', label: 'Notifications', icon: Bell, hasCount: true },
    ],
  },
]

export const instructorNavSections = [
  {
    title: 'Teaching Hub',
    items: [
      { to: '/instructor/dashboard', label: 'Dashboard', icon: LayoutDashboard },
      { to: '/instructor/assessments', label: 'Assessments', icon: BookOpenCheck },
      { to: '/instructor/assessments/create', label: 'Create Assessment', icon: Sparkles },
    ],
  },
  {
    title: 'Class Insights',
    items: [
      { to: '/instructor/students', label: 'Students & Progress', icon: Users },
      { to: '/instructor/analytics', label: 'Class Analytics', icon: BarChart3 },
      { to: '/instructor/feedback', label: 'Feedback & Notes', icon: MessageSquareQuote },
      { to: '/instructor/reports', label: 'Class Reports', icon: FileText },
    ],
  },
]

export default function Sidebar({ mobileOpen, onClose }) {
  const { user, logout } = useAuth()
  const { unreadCount } = useStudyData()
  const navigate = useNavigate()

  const isInstructor =
    (user?.role || '').toLowerCase() === 'instructor' ||
    (user?.role || '').toLowerCase() === 'admin'

  const sections = isInstructor ? instructorNavSections : studentNavSections
  const defaultHome = isInstructor ? '/instructor/dashboard' : '/dashboard'

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const linkClass = ({ isActive }) =>
    `group flex items-center gap-3 rounded-xl px-3 py-2 text-[13px] font-medium transition-all duration-150 ${
      isActive
        ? 'border-l-2 border-brand-600 bg-brand-50/80 font-semibold text-brand-700 shadow-2xs dark:border-brand-500 dark:bg-brand-950/60 dark:text-brand-300'
        : 'border-l-2 border-transparent text-ink-600 hover:translate-x-0.5 hover:bg-ink-100/70 hover:text-ink-900 dark:text-ink-400 dark:hover:bg-ink-800/50 dark:hover:text-white'
    }`

  const content = (
    <div className="flex h-full flex-col">
      {/* Brand Header */}
      <div className="flex items-center justify-between px-2 py-1.5">
        <NavLink to={defaultHome} className="flex items-center gap-2.5" onClick={onClose}>
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-600 via-indigo-600 to-purple-600 text-white shadow-md shadow-brand-500/25">
            <GraduationCap size={20} />
          </span>
          <div>
            <span className="font-display text-base font-bold tracking-tight text-ink-900 block leading-tight dark:text-white">
              Study Companion
            </span>
            {isInstructor ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-purple-100 px-2 py-0.2 text-[10px] font-semibold text-purple-700 dark:bg-purple-950/60 dark:text-purple-300">
                <ShieldCheck size={10} />
                Instructor Portal
              </span>
            ) : (
              <span className="text-[10px] font-medium text-brand-600 dark:text-brand-400">
                AI Learning Platform
              </span>
            )}
          </div>
        </NavLink>
        <button
          onClick={onClose}
          className="rounded-lg p-1.5 text-ink-500 hover:bg-ink-100 lg:hidden dark:hover:bg-ink-800"
          aria-label="Close menu"
        >
          <X size={18} />
        </button>
      </div>

      {/* Navigation Sections */}
      <nav className="mt-5 flex-1 space-y-4 overflow-y-auto pr-1">
        {sections.map((sec, secIdx) => (
          <div key={secIdx}>
            <div className="px-3 pb-1 text-[10px] font-bold uppercase tracking-wider text-ink-400 dark:text-ink-500">
              {sec.title}
            </div>
            <div className="space-y-0.5">
              {sec.items.map(({ to, label, icon: Icon, isNew, badge, hasCount }) => (
                <NavLink key={to} to={to} className={linkClass} onClick={onClose}>
                  <Icon
                    size={16}
                    className="shrink-0 transition-transform duration-150 group-hover:scale-110"
                  />
                  <span className="flex-1 truncate">{label}</span>
                  {hasCount && unreadCount > 0 && (
                    <span className="rounded-full bg-brand-600 px-1.5 py-0.2 text-[10px] font-bold text-white shadow-xs">
                      {unreadCount}
                    </span>
                  )}
                  {badge && (
                    <span className="rounded-full bg-emerald-100 px-1.5 py-0.2 text-[9px] font-semibold text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">
                      {badge}
                    </span>
                  )}
                  {isNew && (
                    <span className="rounded-full bg-brand-100 px-1.5 py-0.2 text-[9px] font-bold text-brand-700 dark:bg-brand-950 dark:text-brand-300">
                      AI
                    </span>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* Profile & Logout Footer */}
      <div className="mt-3 border-t border-ink-100/90 pt-3 dark:border-ink-800/90">
        <NavLink
          to="/profile"
          className="flex items-center gap-2.5 rounded-xl p-2 transition hover:bg-ink-100/70 dark:hover:bg-ink-800/50"
          onClick={onClose}
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-tr from-brand-600 to-indigo-600 text-xs font-bold text-white shadow-xs">
            {(user?.name || 'U').charAt(0).toUpperCase()}
          </span>
          <div className="flex-1 truncate">
            <span className="truncate font-semibold capitalize block text-xs text-ink-900 dark:text-white">
              {user?.name || 'User'}
            </span>
            <span className="text-[10px] text-ink-400 capitalize block">
              {user?.role || 'Student'} • Account
            </span>
          </div>
        </NavLink>
        <button
          onClick={handleLogout}
          className="mt-1 flex w-full items-center gap-2.5 rounded-xl px-2.5 py-2 text-xs font-medium text-ink-600 transition hover:bg-rose-50 hover:text-rose-600 dark:text-ink-400 dark:hover:bg-rose-950/40 dark:hover:text-rose-400"
        >
          <LogOut size={15} />
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  )

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden w-64 shrink-0 border-r border-ink-200/80 bg-white/95 p-4 lg:block dark:border-ink-800/80 dark:bg-ink-900/95">
        {content}
      </aside>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-ink-900/60 backdrop-blur-xs"
            onClick={onClose}
            role="button"
            tabIndex={-1}
            aria-label="Close menu"
          />
          <aside className="absolute left-0 top-0 h-full w-72 animate-fade-in border-r border-ink-200 bg-white p-4 shadow-2xl dark:border-ink-800 dark:bg-ink-900">
            {content}
          </aside>
        </div>
      )}
    </>
  )
}

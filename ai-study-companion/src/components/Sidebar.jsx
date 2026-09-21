import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Library,
  Bot,
  FileText,
  Layers,
  ClipboardCheck,
  TrendingUp,
  Target,
  Bell,
  User,
  LogOut,
  GraduationCap,
  X,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import { useStudyData } from '../context/StudyDataContext.jsx'

export const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/materials', label: 'Study Materials', icon: Library },
  { to: '/tutor', label: 'AI Tutor', icon: Bot },
  { to: '/summaries', label: 'Summaries', icon: FileText },
  { to: '/flashcards', label: 'Flashcards', icon: Layers },
  { to: '/quizzes', label: 'Quizzes', icon: ClipboardCheck },
  { to: '/progress', label: 'My Progress', icon: TrendingUp },
  { to: '/goals', label: 'Goals', icon: Target },
  { to: '/notifications', label: 'Notifications', icon: Bell },
  { to: '/profile', label: 'Profile', icon: User },
]

export default function Sidebar({ mobileOpen, onClose }) {
  const { user, logout } = useAuth()
  const { unreadCount } = useStudyData()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const linkClass = ({ isActive }) =>
    `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
      isActive
        ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/50 dark:text-brand-200'
        : 'text-ink-600 hover:bg-ink-100 dark:text-ink-400 dark:hover:bg-ink-800'
    }`

  const content = (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between px-2 py-1">
        <NavLink to="/dashboard" className="flex items-center gap-2.5" onClick={onClose}>
          <span className="rounded-lg bg-brand-600 p-1.5 text-white">
            <GraduationCap size={18} />
          </span>
          <span className="font-display text-base font-semibold">AI Study Companion</span>
        </NavLink>
        <button onClick={onClose} className="rounded-lg p-1.5 text-ink-500 hover:bg-ink-100 lg:hidden dark:hover:bg-ink-800" aria-label="Close menu">
          <X size={18} />
        </button>
      </div>

      <nav className="mt-6 flex-1 space-y-1 overflow-y-auto">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} className={linkClass} onClick={onClose}>
            <Icon size={18} />
            <span className="flex-1">{label}</span>
            {to === '/notifications' && unreadCount > 0 && (
              <span className="rounded-full bg-brand-600 px-1.5 py-0.5 text-[11px] font-semibold text-white">
                {unreadCount}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="mt-4 border-t border-ink-200 pt-4 dark:border-ink-800">
        <NavLink to="/profile" className={linkClass} onClick={onClose}>
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600 text-xs font-semibold text-white">
            {(user?.name || 'S').charAt(0).toUpperCase()}
          </span>
          <span className="truncate capitalize">{user?.name || 'Student'}</span>
        </NavLink>
        <button
          onClick={handleLogout}
          className="mt-1 flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-ink-600 hover:bg-rose-50 hover:text-rose-600 dark:text-ink-400 dark:hover:bg-rose-950/40"
        >
          <LogOut size={18} />
          Log out
        </button>
      </div>
    </div>
  )

  return (
    <>
      {/* Desktop */}
      <aside className="hidden w-64 shrink-0 border-r border-ink-200 bg-white p-4 lg:block dark:border-ink-800 dark:bg-ink-900">
        {content}
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-ink-900/50" onClick={onClose} role="button" tabIndex={-1} aria-label="Close menu" />
          <aside className="absolute left-0 top-0 h-full w-72 animate-fade-in border-r border-ink-200 bg-white p-4 dark:border-ink-800 dark:bg-ink-900">
            {content}
          </aside>
        </div>
      )}
    </>
  )
}

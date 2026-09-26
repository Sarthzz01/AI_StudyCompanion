import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Menu, Search, Bell, Moon, Sun, Sparkles, Bot } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import { useStudyData } from '../context/StudyDataContext.jsx'
import { useTheme } from '../context/ThemeContext.jsx'

export default function Navbar({ onMenuClick }) {
  const { user } = useAuth()
  const { unreadCount } = useStudyData()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')

  const onSearch = (e) => {
    e.preventDefault()
    if (query.trim()) navigate(`/materials?q=${encodeURIComponent(query.trim())}`)
  }

  return (
    <header className="glass-nav sticky top-0 z-30 flex items-center gap-3 px-4 py-2.5 sm:px-6">
      <button
        onClick={onMenuClick}
        className="rounded-xl p-2 text-ink-600 transition hover:bg-ink-100 lg:hidden dark:text-ink-300 dark:hover:bg-ink-800"
        aria-label="Open menu"
      >
        <Menu size={20} />
      </button>

      {/* Global Search Bar */}
      <form onSubmit={onSearch} className="relative hidden flex-1 sm:block sm:max-w-md">
        <Search size={15} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-400" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search materials, topics, quizzes…"
          aria-label="Search materials and topics"
          className="field pl-9 pr-14 text-xs py-2 bg-ink-50/70 border-ink-200/80 rounded-xl focus:bg-white dark:bg-ink-950/60 dark:border-ink-800 dark:focus:bg-ink-900"
        />
        <kbd className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 rounded border border-ink-200/80 bg-ink-100/70 px-1.5 py-0.5 text-[10px] font-medium text-ink-500 dark:border-ink-700 dark:bg-ink-800 dark:text-ink-400">
          ⌘K
        </kbd>
      </form>

      {/* Quick Launch AI Tutor button */}
      <button
        onClick={() => navigate('/tutor')}
        className="hidden md:inline-flex items-center gap-1.5 rounded-xl border border-brand-200/80 bg-gradient-to-r from-brand-50 to-indigo-50/50 px-3 py-1.5 text-xs font-semibold text-brand-700 shadow-2xs transition hover:border-brand-400 hover:shadow-xs active:scale-98 dark:border-brand-800/80 dark:from-brand-950/60 dark:to-indigo-950/40 dark:text-brand-300"
      >
        <Bot size={14} className="text-brand-600 dark:text-brand-400" />
        <span>Ask AI Tutor</span>
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
      </button>

      <div className="ml-auto flex items-center gap-2">
        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="rounded-xl p-2 text-ink-600 transition hover:bg-ink-100 dark:text-ink-300 dark:hover:bg-ink-800"
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? (
            <Sun size={18} className="text-amber-400 transition-transform duration-300 hover:rotate-45" />
          ) : (
            <Moon size={18} className="text-ink-600 transition-transform duration-300 hover:-rotate-12" />
          )}
        </button>

        {/* Notifications */}
        <button
          onClick={() => navigate('/notifications')}
          className="relative rounded-xl p-2 text-ink-600 transition hover:bg-ink-100 dark:text-ink-300 dark:hover:bg-ink-800"
          aria-label={`Notifications${unreadCount ? `, ${unreadCount} unread` : ''}`}
        >
          <Bell size={18} />
          {unreadCount > 0 && (
            <span className="absolute right-1.5 top-1.5 flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-rose-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-rose-500" />
            </span>
          )}
        </button>

        {/* User Profile Pill */}
        <button
          onClick={() => navigate('/profile')}
          className="flex items-center gap-2.5 rounded-xl border border-transparent p-1 pl-1.5 pr-2.5 transition hover:border-ink-200/80 hover:bg-ink-100/60 dark:hover:border-ink-800 dark:hover:bg-ink-800/60"
        >
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-tr from-brand-600 to-indigo-600 text-xs font-bold text-white shadow-xs shadow-brand-500/20">
            {(user?.name || 'S').charAt(0).toUpperCase()}
          </span>
          <div className="hidden text-left sm:block">
            <span className="block text-xs font-semibold capitalize text-ink-900 leading-tight dark:text-white">
              {user?.name || 'Student'}
            </span>
            <span className="block text-[10px] text-ink-400 capitalize">
              {user?.role || 'Student'}
            </span>
          </div>
        </button>
      </div>
    </header>
  )
}

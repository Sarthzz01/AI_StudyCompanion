import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Menu, Search, Bell, Moon, Sun } from 'lucide-react'
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
    <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-ink-200 bg-white/90 px-4 py-3 backdrop-blur dark:border-ink-800 dark:bg-ink-900/90">
      <button
        onClick={onMenuClick}
        className="rounded-lg p-2 text-ink-600 hover:bg-ink-100 lg:hidden dark:text-ink-300 dark:hover:bg-ink-800"
        aria-label="Open menu"
      >
        <Menu size={20} />
      </button>

      <form onSubmit={onSearch} className="relative hidden flex-1 sm:block sm:max-w-md">
        <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search materials and topics"
          aria-label="Search materials and topics"
          className="field pl-9"
        />
      </form>

      <div className="ml-auto flex items-center gap-1.5">
        <button
          onClick={toggleTheme}
          className="rounded-lg p-2 text-ink-600 hover:bg-ink-100 dark:text-ink-300 dark:hover:bg-ink-800"
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        <button
          onClick={() => navigate('/notifications')}
          className="relative rounded-lg p-2 text-ink-600 hover:bg-ink-100 dark:text-ink-300 dark:hover:bg-ink-800"
          aria-label={`Notifications${unreadCount ? `, ${unreadCount} unread` : ''}`}
        >
          <Bell size={18} />
          {unreadCount > 0 && (
            <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-rose-500" />
          )}
        </button>

        <button
          onClick={() => navigate('/profile')}
          className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-ink-100 dark:hover:bg-ink-800"
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-600 text-sm font-semibold text-white">
            {(user?.name || 'S').charAt(0).toUpperCase()}
          </span>
          <span className="hidden text-sm font-medium capitalize sm:block">{user?.name || 'Student'}</span>
        </button>
      </div>
    </header>
  )
}

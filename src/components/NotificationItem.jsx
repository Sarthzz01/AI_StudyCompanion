import { Check, Trophy, Sparkles, FileText, ClipboardCheck, Mic, CalendarClock, BookOpen, AlertCircle, MessageSquare } from 'lucide-react'

const typeIcon = {
  quiz: ClipboardCheck,
  recommendation: Sparkles,
  goal: Trophy,
  summary: FileText,
  viva: Mic,
  revision: CalendarClock,
  assessment: BookOpen,
  feedback: MessageSquare,
  alert: AlertCircle,
  info: Sparkles,
}

export default function NotificationItem({ notification, onMarkRead }) {
  const Icon = typeIcon[notification.type] || Sparkles
  return (
    <div
      className={`flex items-start gap-3 rounded-xl border p-4 ${
        notification.read
          ? 'border-ink-200 bg-white dark:border-ink-800 dark:bg-ink-900'
          : 'border-brand-200 bg-brand-50/60 dark:border-brand-900 dark:bg-brand-950/40'
      }`}
    >
      <span className="rounded-lg bg-white p-2 text-brand-600 shadow-sm dark:bg-ink-800 dark:text-brand-300">
        <Icon size={16} />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <h4 className="text-sm font-semibold">{notification.title}</h4>
          {!notification.read && <span className="h-2 w-2 rounded-full bg-brand-600" aria-label="Unread" />}
        </div>
        <p className="muted mt-1">{notification.body}</p>
        <p className="mt-2 text-xs text-ink-400">{notification.time}</p>
      </div>
      {!notification.read && (
        <button
          onClick={() => onMarkRead(notification.id)}
          className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium text-brand-700 hover:bg-brand-100 dark:text-brand-300 dark:hover:bg-brand-900/60"
        >
          <Check size={13} /> Mark read
        </button>
      )}
    </div>
  )
}

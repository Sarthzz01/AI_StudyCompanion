import { Link } from 'react-router-dom'
import {
  ArrowRight,
  Layers,
  ClipboardCheck,
  FileText,
  Target,
  Network,
  Sparkles,
  Bot,
} from 'lucide-react'

const priorityTone = {
  high: 'bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300',
  medium: 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300',
  low: 'bg-ink-100 text-ink-600 dark:bg-ink-800 dark:text-ink-300',
}

const iconMap = {
  layers: Layers,
  flashcards: Layers,
  clipboardCheck: ClipboardCheck,
  quiz: ClipboardCheck,
  fileText: FileText,
  summary: FileText,
  target: Target,
  network: Network,
  tutor: Bot,
  sparkles: Sparkles,
}

export default function RecommendationCard({ recommendation }) {
  const { title, reason, action, to, icon, priority } = recommendation
  const IconComponent = typeof icon === 'function' ? icon : (iconMap[icon] || Layers)

  return (
    <div className="flex items-start gap-3 rounded-xl border border-ink-200 p-4 dark:border-ink-800">
      <span className="rounded-lg bg-brand-50 p-2 text-brand-600 dark:bg-brand-900/40 dark:text-brand-300">
        <IconComponent size={16} />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <h4 className="truncate text-sm font-semibold">{title}</h4>
          <span className={`chip ${priorityTone[priority] || priorityTone.low}`}>{priority}</span>
        </div>
        <p className="muted mt-1 text-xs leading-relaxed">{reason}</p>
        <Link
          to={to}
          className="mt-2.5 inline-flex items-center gap-1 text-xs font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400"
        >
          {action}
          <ArrowRight size={13} />
        </Link>
      </div>
    </div>
  )
}

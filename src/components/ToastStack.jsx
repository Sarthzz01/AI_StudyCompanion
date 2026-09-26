import { CheckCircle2, Info, AlertCircle, X } from 'lucide-react'

const icons = { success: CheckCircle2, info: Info, error: AlertCircle }
const tones = {
  success: 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/60 dark:text-emerald-200',
  info: 'border-brand-200 bg-brand-50 text-brand-800 dark:border-brand-900 dark:bg-brand-950/60 dark:text-brand-200',
  error: 'border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-900 dark:bg-rose-950/60 dark:text-rose-200',
}

export default function ToastStack({ toasts, onDismiss }) {
  if (!toasts.length) return null
  return (
    <div className="fixed bottom-4 right-4 z-[60] flex w-[min(22rem,calc(100vw-2rem))] flex-col gap-2">
      {toasts.map((t) => {
        const Icon = icons[t.variant] || Info
        return (
          <div
            key={t.id}
            role="status"
            className={`flex animate-fade-in items-start gap-2.5 rounded-xl border px-3.5 py-3 text-sm shadow-card ${tones[t.variant] || tones.info}`}
          >
            <Icon size={16} className="mt-0.5 shrink-0" />
            <p className="flex-1">{t.message}</p>
            <button onClick={() => onDismiss(t.id)} aria-label="Dismiss" className="opacity-60 hover:opacity-100">
              <X size={14} />
            </button>
          </div>
        )
      })}
    </div>
  )
}

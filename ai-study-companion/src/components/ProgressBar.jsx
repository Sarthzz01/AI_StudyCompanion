import { clamp } from '../utils/format.js'

const tones = {
  brand: 'bg-brand-600',
  emerald: 'bg-emerald-500',
  amber: 'bg-amber-500',
  sky: 'bg-sky-500',
  rose: 'bg-rose-500',
}

export default function ProgressBar({ value = 0, tone = 'brand', size = 'md', label, showValue = false }) {
  const pct = clamp(Math.round(value))
  return (
    <div>
      {(label || showValue) && (
        <div className="mb-1.5 flex items-center justify-between text-xs font-medium text-ink-600 dark:text-ink-400">
          <span>{label}</span>
          {showValue && <span>{pct}%</span>}
        </div>
      )}
      <div
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label || 'Progress'}
        className={`w-full overflow-hidden rounded-full bg-ink-200 dark:bg-ink-800 ${size === 'sm' ? 'h-1.5' : 'h-2.5'}`}
      >
        <div className={`h-full rounded-full transition-all duration-500 ${tones[tone] || tones.brand}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

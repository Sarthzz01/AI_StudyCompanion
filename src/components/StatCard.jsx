export default function StatCard({
  icon: Icon,
  label,
  value,
  sublabel,
  tone = 'brand',
  trend,
  className = '',
}) {
  const tones = {
    brand: 'bg-brand-50 text-brand-600 shadow-sm shadow-brand-500/15 dark:bg-brand-950/60 dark:text-brand-300',
    emerald: 'bg-emerald-50 text-emerald-600 shadow-sm shadow-emerald-500/15 dark:bg-emerald-950/60 dark:text-emerald-300',
    amber: 'bg-amber-50 text-amber-600 shadow-sm shadow-amber-500/15 dark:bg-amber-950/60 dark:text-amber-300',
    sky: 'bg-sky-50 text-sky-600 shadow-sm shadow-sky-500/15 dark:bg-sky-950/60 dark:text-sky-300',
    purple: 'bg-purple-50 text-purple-600 shadow-sm shadow-purple-500/15 dark:bg-purple-950/60 dark:text-purple-300',
  }

  return (
    <div className={`card card-hover group relative overflow-hidden ${className}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3.5">
          {Icon && (
            <span
              className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl transition-transform duration-200 group-hover:scale-105 ${tones[tone]}`}
            >
              <Icon size={20} />
            </span>
          )}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-ink-500 dark:text-ink-400">
              {label}
            </p>
            <p className="font-display text-2xl font-bold tracking-tight text-ink-900 mt-0.5 dark:text-white">
              {value}
            </p>
          </div>
        </div>

        {trend && (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">
            {trend}
          </span>
        )}
      </div>

      {sublabel && (
        <p className="mt-3 text-xs text-ink-500 dark:text-ink-400 flex items-center gap-1">
          {sublabel}
        </p>
      )}
    </div>
  )
}

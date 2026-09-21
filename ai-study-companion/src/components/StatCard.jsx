export default function StatCard({ icon: Icon, label, value, sublabel, tone = 'brand' }) {
  const tones = {
    brand: 'bg-brand-50 text-brand-600 dark:bg-brand-900/40 dark:text-brand-300',
    emerald: 'bg-emerald-50 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-300',
    amber: 'bg-amber-50 text-amber-600 dark:bg-amber-900/40 dark:text-amber-300',
    sky: 'bg-sky-50 text-sky-600 dark:bg-sky-900/40 dark:text-sky-300',
  }
  return (
    <div className="card">
      <div className="flex items-center gap-3">
        {Icon && (
          <span className={`rounded-xl p-2.5 ${tones[tone]}`}>
            <Icon size={18} />
          </span>
        )}
        <div>
          <p className="muted">{label}</p>
          <p className="font-display text-2xl font-semibold text-ink-900 dark:text-white">{value}</p>
        </div>
      </div>
      {sublabel && <p className="mt-3 text-xs text-ink-500">{sublabel}</p>}
    </div>
  )
}

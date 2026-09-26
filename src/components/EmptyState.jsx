import Button from './Button.jsx'

export default function EmptyState({ icon: Icon, title, description, actionLabel, onAction }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-ink-300 px-6 py-14 text-center dark:border-ink-700">
      {Icon && (
        <span className="mb-4 rounded-xl bg-brand-50 p-3 text-brand-600 dark:bg-brand-900/40 dark:text-brand-300">
          <Icon size={22} />
        </span>
      )}
      <h3 className="text-base font-semibold">{title}</h3>
      {description && <p className="muted mt-1 max-w-sm">{description}</p>}
      {actionLabel && onAction && (
        <Button className="mt-5" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  )
}

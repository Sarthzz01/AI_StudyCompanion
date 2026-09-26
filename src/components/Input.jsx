import { useId } from 'react'

export default function Input({ label, error, hint, icon: Icon, className = '', ...props }) {
  const id = useId()
  return (
    <div className={className}>
      {label && (
        <label htmlFor={id} className="label">
          {label}
        </label>
      )}
      <div className="relative">
        {Icon && (
          <Icon size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
        )}
        <input
          id={id}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${id}-error` : undefined}
          className={`field ${Icon ? 'pl-9' : ''} ${error ? 'field-error' : ''}`}
          {...props}
        />
      </div>
      {error ? (
        <p id={`${id}-error`} className="mt-1.5 text-xs text-rose-600 dark:text-rose-400">
          {error}
        </p>
      ) : hint ? (
        <p className="mt-1.5 text-xs text-ink-500">{hint}</p>
      ) : null}
    </div>
  )
}

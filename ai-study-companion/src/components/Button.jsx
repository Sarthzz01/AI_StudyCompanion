import { Loader2 } from 'lucide-react'

const variants = {
  primary:
    'bg-brand-600 text-white hover:bg-brand-700 disabled:bg-brand-300 dark:disabled:bg-brand-900 dark:disabled:text-brand-300',
  secondary:
    'bg-white text-ink-800 border border-ink-300 hover:bg-ink-50 disabled:text-ink-400 dark:bg-ink-900 dark:text-ink-100 dark:border-ink-700 dark:hover:bg-ink-800',
  ghost:
    'bg-transparent text-ink-700 hover:bg-ink-100 disabled:text-ink-400 dark:text-ink-300 dark:hover:bg-ink-800',
  danger: 'bg-rose-600 text-white hover:bg-rose-700 disabled:bg-rose-300',
}

const sizes = {
  sm: 'px-3 py-1.5 text-sm rounded-lg gap-1.5',
  md: 'px-4 py-2.5 text-sm rounded-xl gap-2',
  lg: 'px-5 py-3 text-base rounded-xl gap-2',
}

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  icon: Icon,
  loading = false,
  className = '',
  disabled,
  type = 'button',
  ...props
}) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center font-medium transition-colors disabled:cursor-not-allowed ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {loading ? <Loader2 size={16} className="animate-spin" /> : Icon ? <Icon size={16} /> : null}
      {children}
    </button>
  )
}

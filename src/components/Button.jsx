import { Loader2 } from 'lucide-react'

const variants = {
  primary:
    'bg-brand-600 text-white hover:bg-brand-700 shadow-sm shadow-brand-500/20 hover:shadow-md hover:shadow-brand-500/25 active:scale-[0.98] disabled:bg-brand-300 dark:disabled:bg-brand-900 dark:disabled:text-brand-300',
  gradient:
    'bg-gradient-to-r from-brand-600 via-indigo-600 to-purple-600 text-white hover:from-brand-500 hover:to-purple-500 shadow-md shadow-brand-500/25 hover:shadow-lg hover:shadow-brand-500/35 active:scale-[0.98] disabled:opacity-50',
  secondary:
    'bg-white text-ink-800 border border-ink-200/90 hover:bg-ink-50 hover:border-brand-300/60 active:scale-[0.98] disabled:text-ink-400 dark:bg-ink-900 dark:text-ink-100 dark:border-ink-800 dark:hover:bg-ink-800',
  ghost:
    'bg-transparent text-ink-700 hover:bg-ink-100/80 active:scale-[0.98] disabled:text-ink-400 dark:text-ink-300 dark:hover:bg-ink-800/60',
  danger:
    'bg-rose-600 text-white hover:bg-rose-700 shadow-sm shadow-rose-500/20 active:scale-[0.98] disabled:bg-rose-300',
  success:
    'bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm shadow-emerald-500/20 active:scale-[0.98] disabled:bg-emerald-300',
}

const sizes = {
  sm: 'px-3 py-1.5 text-xs rounded-lg gap-1.5 font-medium',
  md: 'px-4 py-2.5 text-sm rounded-xl gap-2 font-medium',
  lg: 'px-5 py-3 text-base rounded-xl gap-2.5 font-semibold',
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
      className={`inline-flex items-center justify-center transition-all duration-150 disabled:cursor-not-allowed ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {loading ? <Loader2 size={16} className="animate-spin" /> : Icon ? <Icon size={16} /> : null}
      {children}
    </button>
  )
}

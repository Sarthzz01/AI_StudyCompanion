import { AlertTriangle } from 'lucide-react'
import Button from './Button.jsx'

export default function ErrorState({ message = 'Something went wrong while loading this page.', onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-rose-200 bg-rose-50 px-6 py-12 text-center dark:border-rose-900/60 dark:bg-rose-950/30">
      <AlertTriangle size={24} className="mb-3 text-rose-600 dark:text-rose-400" />
      <p className="text-sm font-medium text-rose-700 dark:text-rose-300">{message}</p>
      {onRetry && (
        <Button className="mt-5" variant="secondary" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  )
}

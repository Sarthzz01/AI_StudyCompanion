import { Link } from 'react-router-dom'
import Button from '../components/Button.jsx'

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-ink-50 p-4 text-center dark:bg-ink-950">
      <p className="font-display text-5xl font-bold text-brand-600">404</p>
      <h1 className="mt-4 font-display text-xl font-semibold">This page does not exist</h1>
      <p className="muted mt-2 max-w-sm">The link may be out of date, or the material was removed from your library.</p>
      <Link to="/dashboard" className="mt-6">
        <Button>Back to dashboard</Button>
      </Link>
    </div>
  )
}

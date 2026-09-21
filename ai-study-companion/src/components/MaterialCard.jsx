import { Link } from 'react-router-dom'
import { FileText, Clock, Layers, Trash2 } from 'lucide-react'
import ProgressBar from './ProgressBar.jsx'
import Button from './Button.jsx'

export default function MaterialCard({ material, onDelete }) {
  return (
    <article className="card flex flex-col transition-shadow hover:shadow-lg">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="rounded-xl bg-brand-50 p-2.5 text-brand-600 dark:bg-brand-900/40 dark:text-brand-300">
            <FileText size={18} />
          </span>
          <div>
            <h3 className="font-semibold leading-tight">{material.title}</h3>
            <p className="muted mt-0.5">{material.type}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          {material.processing_status === 'processing' ? (
            <span className="chip animate-pulse bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300">
              Processing
            </span>
          ) : material.processing_status === 'failed' ? (
            <span className="chip bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300">
              Failed
            </span>
          ) : null}
          <span className="chip bg-ink-100 text-ink-600 dark:bg-ink-800 dark:text-ink-300">{material.progress}%</span>
        </div>
      </div>

      <p className="muted mt-3 line-clamp-2">{material.description}</p>

      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-500">
        <span className="inline-flex items-center gap-1.5">
          <Layers size={13} /> {material.topicsCount} topics
        </span>
        <span className="inline-flex items-center gap-1.5">
          <FileText size={13} /> {material.pages} pages
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Clock size={13} /> {material.lastStudied}
        </span>
      </div>

      <div className="mt-4">
        <ProgressBar value={material.progress} size="sm" />
      </div>

      <div className="mt-5 flex items-center gap-2">
        <Link to={`/materials/${material.id}`} className="flex-1">
          <Button variant="secondary" className="w-full">
            Open
          </Button>
        </Link>
        {onDelete && (
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              onDelete(material)
            }}
            aria-label={`Delete ${material.title}`}
            title="Delete material"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-ink-200 text-ink-400 transition-colors hover:border-rose-300 hover:bg-rose-50 hover:text-rose-600 dark:border-ink-800 dark:hover:border-rose-800 dark:hover:bg-rose-950/40 dark:hover:text-rose-400"
          >
            <Trash2 size={16} />
          </button>
        )}
      </div>
    </article>
  )
}

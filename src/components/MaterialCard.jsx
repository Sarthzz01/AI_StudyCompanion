import { Link } from 'react-router-dom'
import { FileText, Clock, Layers, Trash2, ArrowUpRight } from 'lucide-react'
import ProgressBar from './ProgressBar.jsx'
import Button from './Button.jsx'

export default function MaterialCard({ material, onDelete }) {
  return (
    <article className="card card-hover group flex flex-col justify-between">
      <div>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-50 to-indigo-100 text-brand-600 shadow-2xs transition-transform duration-200 group-hover:scale-105 dark:from-brand-950 dark:to-indigo-900/40 dark:text-brand-300">
              <FileText size={18} />
            </span>
            <div>
              <h3 className="font-display font-bold leading-snug text-ink-900 group-hover:text-brand-600 transition-colors dark:text-white dark:group-hover:text-brand-400">
                {material.title}
              </h3>
              <p className="muted mt-0.5 text-xs">{material.type}</p>
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
            <span className="chip bg-brand-50 text-brand-700 dark:bg-brand-950/80 dark:text-brand-300 border border-brand-200/50">
              {material.progress}%
            </span>
          </div>
        </div>

        <p className="muted mt-3 line-clamp-2 text-xs leading-relaxed">{material.description}</p>

        <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-ink-500 dark:text-ink-400">
          <span className="inline-flex items-center gap-1.5">
            <Layers size={13} className="text-brand-500" /> {material.topicsCount} topics
          </span>
          <span className="inline-flex items-center gap-1.5">
            <FileText size={13} className="text-brand-500" /> {material.pages} pages
          </span>
          <span className="inline-flex items-center gap-1.5">
            <Clock size={13} className="text-brand-500" /> {material.lastStudied}
          </span>
        </div>

        <div className="mt-4">
          <ProgressBar value={material.progress} size="sm" />
        </div>
      </div>

      <div className="mt-5 flex items-center gap-2 border-t border-ink-100/90 pt-3 dark:border-ink-800/90">
        <Link to={`/materials/${material.id}`} className="flex-1">
          <Button variant="secondary" size="sm" className="w-full justify-between px-3">
            <span>Study Document</span>
            <ArrowUpRight size={14} className="text-ink-400 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
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
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-ink-200/80 text-ink-400 transition-all hover:border-rose-300 hover:bg-rose-50 hover:text-rose-600 dark:border-ink-800 dark:hover:border-rose-800 dark:hover:bg-rose-950/40 dark:hover:text-rose-400"
          >
            <Trash2 size={14} />
          </button>
        )}
      </div>
    </article>
  )
}

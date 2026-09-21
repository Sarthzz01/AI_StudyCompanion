import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { Bot, FileText, Layers, ClipboardCheck, ArrowLeft, Activity } from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import Card, { CardHeader } from '../components/Card.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import Button from '../components/Button.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import ErrorState from '../components/ErrorState.jsx'
import EmptyState from '../components/EmptyState.jsx'
import { getMaterial } from '../services/api.js'

export default function MaterialDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [material, setMaterial] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      setMaterial(await getMaterial(id))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  if (loading) return <LoadingSpinner label="Opening material…" />
  if (error) return <ErrorState message={error} onRetry={load} />

  const actions = [
    { label: 'AI Tutor', icon: Bot, to: `/tutor?material=${material.id}` },
    { label: 'Generate summary', icon: FileText, to: `/summaries?material=${material.id}` },
    { label: 'Flashcards', icon: Layers, to: `/flashcards?material=${material.id}` },
    { label: 'Take quiz', icon: ClipboardCheck, to: `/quizzes?material=${material.id}` },
  ]

  return (
    <>
      <button
        onClick={() => navigate('/materials')}
        className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-ink-600 hover:text-brand-600 dark:text-ink-400"
      >
        <ArrowLeft size={15} /> All materials
      </button>

      <PageHeader
        title={material.title}
        subtitle={`${material.type} · ${material.pages} pages · ${material.topicsCount} topics · Status: ${material.processing_status || 'ready'}`}
        actions={
          material.processing_status === 'processing' ? (
            <span className="chip animate-pulse bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300">
              Indexing Chunks…
            </span>
          ) : (
            <span className="chip bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300">
              Ready for AI Study
            </span>
          )
        }
      />

      <div className="grid gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          {material.processing_status === 'processing' && (
            <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50/50 p-3 text-sm text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-300">
              ⚡ <strong>Processing:</strong> Text extraction and RAG embeddings are indexing in the background. Tutor and summaries will refresh automatically.
            </div>
          )}
          <p className="leading-relaxed text-ink-700 dark:text-ink-300">{material.description}</p>
          <div className="mt-5">
            <ProgressBar value={material.progress} label="Material progress" showValue />
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {actions.map(({ label, icon: Icon, to }) => (
              <Link
                key={label}
                to={to}
                className="flex flex-col items-center gap-2 rounded-xl border border-ink-200 px-3 py-4 text-center text-sm font-medium transition-colors hover:border-brand-300 hover:bg-brand-50 dark:border-ink-800 dark:hover:bg-brand-950/40"
              >
                <Icon size={18} className="text-brand-600 dark:text-brand-300" />
                {label}
              </Link>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader title="Recent activity" action={<Activity size={18} className="text-ink-400" />} />
          {material.recentActivity.length === 0 ? (
            <EmptyState
              icon={Activity}
              title="Nothing here yet"
              description="Attempt a quiz or generate a summary and it will show up here."
            />
          ) : (
            <ul className="space-y-4">
              {material.recentActivity.map((item) => (
                <li key={item.id} className="border-l-2 border-brand-200 pl-3 dark:border-brand-800">
                  <p className="text-sm font-medium">{item.label}</p>
                  <p className="muted">{item.detail}</p>
                  <p className="mt-0.5 text-xs text-ink-400">{item.time}</p>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader title="Topics" subtitle="Progress per topic in this material" />
          {material.topics.length === 0 ? (
            <EmptyState
              icon={Layers}
              title="No topics extracted yet"
              description="Topic extraction happens during AI processing, which needs the backend."
            />
          ) : (
            <div className="grid gap-x-8 gap-y-5 sm:grid-cols-2">
              {material.topics.map((topic) => (
                <ProgressBar
                  key={topic.name}
                  value={topic.progress}
                  label={topic.name}
                  showValue
                  tone={topic.progress < 50 ? 'rose' : topic.progress < 80 ? 'amber' : 'emerald'}
                />
              ))}
            </div>
          )}
        </Card>
      </div>

      <div className="mt-6">
        <Button variant="secondary" onClick={() => navigate(`/quizzes?material=${material.id}`)}>
          Test yourself on this material
        </Button>
      </div>
    </>
  )
}

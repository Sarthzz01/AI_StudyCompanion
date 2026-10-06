import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { Bot, FileText, Layers, ClipboardCheck, ArrowLeft, Activity, Trash2, AlertTriangle } from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import Card, { CardHeader } from '../components/Card.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import Button from '../components/Button.jsx'
import Modal from '../components/Modal.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import ErrorState from '../components/ErrorState.jsx'
import EmptyState from '../components/EmptyState.jsx'
import { getMaterial, deleteMaterial } from '../services/api.js'
import { useToast } from '../context/ToastContext.jsx'

export default function MaterialDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const [material, setMaterial] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)

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

  const handleDelete = async () => {
    if (!material) return
    setDeleting(true)
    try {
      await deleteMaterial(material.id)
      toast(`'${material.title}' was successfully deleted.`, 'success')
      navigate('/materials')
    } catch (err) {
      toast(err.message || 'Failed to delete material.', 'error')
      setDeleting(false)
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
          <div className="flex items-center gap-2">
            {material.processing_status === 'processing' ? (
              <span className="chip animate-pulse bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300">
                Indexing Chunks…
              </span>
            ) : (
              <span className="chip bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300">
                Ready for AI Study
              </span>
            )}
            <Button
              variant="danger"
              size="sm"
              icon={Trash2}
              onClick={() => setConfirmDelete(true)}
            >
              Delete
            </Button>
          </div>
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

      {/* Delete Confirmation Modal */}
      <Modal
        open={confirmDelete}
        onClose={() => !deleting && setConfirmDelete(false)}
        title="Delete study material"
        description="Permanent removal confirmation"
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => setConfirmDelete(false)}
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleDelete}
              loading={deleting}
              icon={Trash2}
            >
              Delete document
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50/80 p-4 dark:border-rose-900/60 dark:bg-rose-950/30">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-rose-100 text-rose-600 dark:bg-rose-900/50 dark:text-rose-300">
              <AlertTriangle size={18} />
            </span>
            <div>
              <h4 className="text-sm font-semibold text-rose-900 dark:text-rose-200">
                Are you sure you want to delete this material?
              </h4>
              <p className="mt-1 text-xs leading-relaxed text-rose-700 dark:text-rose-300">
                You are about to delete <strong className="font-semibold">{material.title}</strong>. This will permanently remove the document, all RAG vector embeddings, summaries, and associated interactions.
              </p>
            </div>
          </div>
        </div>
      </Modal>
    </>
  )
}

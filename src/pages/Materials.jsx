import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Search, Upload, Library } from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import MaterialCard from '../components/MaterialCard.jsx'
import Button from '../components/Button.jsx'
import Input from '../components/Input.jsx'
import Select from '../components/Select.jsx'
import Modal from '../components/Modal.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import EmptyState from '../components/EmptyState.jsx'
import ErrorState from '../components/ErrorState.jsx'
import { getMaterials, uploadMaterial, deleteMaterial } from '../services/api.js'
import { useToast } from '../context/ToastContext.jsx'

export default function Materials() {
  const [searchParams, setSearchParams] = useSearchParams()
  const toast = useToast()

  const [materials, setMaterials] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [query, setQuery] = useState(searchParams.get('q') || '')
  const [typeFilter, setTypeFilter] = useState('All types')
  const [uploadOpen, setUploadOpen] = useState(searchParams.get('upload') === '1')
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadStatus, setUploadStatus] = useState('')
  const [newMaterial, setNewMaterial] = useState({ title: '', type: 'PDF', file: null })

  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      setMaterials(await getMaterials())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const types = useMemo(() => ['All types', ...new Set(materials.map((m) => m.type))], [materials])

  const visible = materials.filter((m) => {
    const matchesQuery =
      !query.trim() ||
      m.title.toLowerCase().includes(query.toLowerCase()) ||
      m.topics.some((t) => t.name.toLowerCase().includes(query.toLowerCase()))
    const matchesType = typeFilter === 'All types' || m.type === typeFilter
    return matchesQuery && matchesType
  })

  const closeUpload = () => {
    setUploadOpen(false)
    setUploadProgress(0)
    setUploadStatus('')
    if (searchParams.get('upload')) setSearchParams({})
  }

  const handleUpload = async () => {
    if (!newMaterial.title.trim() && !newMaterial.file) {
      toast('Give the material a title or pick a file first.', 'error')
      return
    }
    setUploading(true)
    setUploadProgress(20)
    setUploadStatus('Uploading file to server…')
    try {
      const created = await uploadMaterial({
        ...newMaterial,
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 65) / progressEvent.total)
            setUploadProgress(percent)
            if (percent >= 65) {
              setUploadStatus('Extracting text, chunking & generating embeddings…')
            }
          }
        },
      })
      setUploadProgress(100)
      setUploadStatus('Processing completed!')
      setMaterials((list) => [created, ...list])
      toast('Material uploaded and indexed for AI study', 'success')
      setNewMaterial({ title: '', type: 'PDF', file: null })
      setTimeout(() => {
        closeUpload()
      }, 500)
    } catch (err) {
      toast(err.message || 'Upload failed. Try again.', 'error')
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await deleteMaterial(deleteTarget.id)
      setMaterials((list) => list.filter((m) => m.id !== deleteTarget.id))
      toast(`'${deleteTarget.title}' and its processed AI data have been removed.`, 'success')
      setDeleteTarget(null)
    } catch (err) {
      toast(err.message || 'Failed to delete material. Please try again.', 'error')
    } finally {
      setDeleting(false)
    }
  }

  return (
    <>
      <PageHeader
        title="Study materials"
        subtitle="Everything you have uploaded or added from your syllabus."
        actions={
          <Button icon={Upload} onClick={() => setUploadOpen(true)}>
            Upload material
          </Button>
        }
      />

      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <Input
          className="flex-1"
          icon={Search}
          placeholder="Search by title or topic"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search materials"
        />
        <Select
          className="sm:w-48"
          options={types}
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          aria-label="Filter by type"
        />
      </div>

      {loading ? (
        <LoadingSpinner label="Loading materials…" />
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : visible.length === 0 ? (
        <EmptyState
          icon={Library}
          title="No materials match that search"
          description="Try a different title or topic, or upload something new to study from."
          actionLabel="Upload material"
          onAction={() => setUploadOpen(true)}
        />
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {visible.map((m) => (
            <MaterialCard key={m.id} material={m} onDelete={setDeleteTarget} />
          ))}
        </div>
      )}

      <Modal
        open={uploadOpen}
        onClose={closeUpload}
        title="Upload study material"
        description="PDFs, notes and slides. Processing runs on the backend once it is connected."
        footer={
          <>
            <Button variant="secondary" onClick={closeUpload}>
              Cancel
            </Button>
            <Button onClick={handleUpload} loading={uploading}>
              Upload
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="Title"
            placeholder="e.g. Compiler Design — Unit 2"
            value={newMaterial.title}
            onChange={(e) => setNewMaterial((m) => ({ ...m, title: e.target.value }))}
          />
          <Select
            label="Type"
            options={['PDF', 'Notes', 'Slides']}
            value={newMaterial.type}
            onChange={(e) => setNewMaterial((m) => ({ ...m, type: e.target.value }))}
          />
          <div>
            <span className="label">File</span>
            <label className="flex cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-ink-300 px-4 py-8 text-center hover:border-brand-400 dark:border-ink-700">
              <Upload size={20} className="mb-2 text-ink-400" />
              <span className="text-sm font-medium">
                {newMaterial.file ? newMaterial.file.name : 'Choose a file'}
              </span>
              <span className="muted mt-1">PDF, DOCX or PPTX up to 25 MB</span>
              <input
                type="file"
                className="sr-only"
                accept=".pdf,.doc,.docx,.ppt,.pptx,.txt"
                onChange={(e) => setNewMaterial((m) => ({ ...m, file: e.target.files?.[0] || null }))}
              />
            </label>
          </div>

          {uploading && (
            <div className="space-y-2 rounded-xl border border-brand-200 bg-brand-50/50 p-3.5 dark:border-brand-900/50 dark:bg-brand-950/30">
              <div className="flex justify-between text-xs font-medium text-brand-700 dark:text-brand-300">
                <span>{uploadStatus || 'Processing material…'}</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-ink-200 dark:bg-ink-800">
                <div
                  className="h-full bg-brand-600 transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </Modal>
    </>
  )
}

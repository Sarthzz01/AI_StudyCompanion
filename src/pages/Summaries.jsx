import { useEffect, useState, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  ChevronDown,
  Search,
  Bookmark,
  BookmarkCheck,
  FileText,
  Upload,
  Sparkles,
  Download,
  RotateCcw,
  X,
  FileUp,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers
} from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import Card, { CardHeader } from '../components/Card.jsx'
import Select from '../components/Select.jsx'
import Input from '../components/Input.jsx'
import Button from '../components/Button.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import ErrorState from '../components/ErrorState.jsx'
import EmptyState from '../components/EmptyState.jsx'
import { generateSummary, getMaterials, uploadAndSummarizePdf } from '../services/api.js'
import { useToast } from '../context/ToastContext.jsx'
import { readStorage, writeStorage } from '../utils/storage.js'
import { exportSummaryToPDF } from '../utils/pdfExport.js'

export default function Summaries() {
  const [searchParams] = useSearchParams()
  const toast = useToast()
  const fileInputRef = useRef(null)

  const [materials, setMaterials] = useState([])
  const [materialId, setMaterialId] = useState(searchParams.get('material') || 'data-structures')
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [openSections, setOpenSections] = useState(['s1'])
  const [query, setQuery] = useState('')
  const [saved, setSaved] = useState(() => readStorage('savedSummaries', []))

  // PDF Upload State
  const [showUploadPanel, setShowUploadPanel] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [customTitle, setCustomTitle] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadStep, setUploadStep] = useState('')
  const [uploadError, setUploadError] = useState('')
  const [dragActive, setDragActive] = useState(false)

  const fetchMaterialsList = async () => {
    try {
      const data = await getMaterials()
      setMaterials(data)
      return data
    } catch {
      setMaterials([])
      return []
    }
  }

  useEffect(() => {
    fetchMaterialsList()
  }, [])

  const load = async (id, forceRefresh = false) => {
    setLoading(true)
    setError(null)
    try {
      const data = await generateSummary(id)
      setSummary(data)
      setOpenSections(data.sections.length ? [data.sections[0].id] : [])
    } catch (err) {
      setError(err.message || 'Failed to load summary.')
      setSummary(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load(materialId)
  }, [materialId])

  const toggleSection = (id) =>
    setOpenSections((list) => (list.includes(id) ? list.filter((s) => s !== id) : [...list, id]))

  const toggleSave = (sectionId) => {
    const key = `${materialId}:${sectionId}`
    const next = saved.includes(key) ? saved.filter((s) => s !== key) : [...saved, key]
    setSaved(next)
    writeStorage('savedSummaries', next)
    toast(saved.includes(key) ? 'Removed from saved' : 'Saved for revision', 'success')
  }

  // Handle Drag & Drop
  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processSelectedFile(e.dataTransfer.files[0])
    }
  }

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      processSelectedFile(e.target.files[0])
    }
  }

  const processSelectedFile = (file) => {
    setUploadError('')
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      setUploadError('Please choose a valid PDF file.')
      return
    }
    setSelectedFile(file)
    // Clean filename for initial title
    const nameWithoutExt = file.name.replace(/\.pdf$/i, '').replace(/[-_]/g, ' ')
    setCustomTitle(nameWithoutExt.charAt(0).toUpperCase() + nameWithoutExt.slice(1))
  }

  const handleUploadAndSummarize = async (e) => {
    e.preventDefault()
    if (!selectedFile) {
      setUploadError('Please select a PDF file first.')
      return
    }

    setUploading(true)
    setUploadError('')
    setUploadStep('Extracting PDF text and analyzing with AI...')

    try {
      const result = await uploadAndSummarizePdf(selectedFile, customTitle || selectedFile.name)
      toast(`AI Summary generated for "${result.materialTitle || 'your PDF'}"!`, 'success')

      // Refresh materials dropdown
      const updatedList = await fetchMaterialsList()
      const newMatId = result.materialId
      setMaterialId(newMatId)
      setSummary(result)
      setOpenSections(result.sections?.length ? [result.sections[0].id] : [])

      // Reset upload panel
      setSelectedFile(null)
      setCustomTitle('')
      setShowUploadPanel(false)
    } catch (err) {
      setUploadError(err.message || 'Failed to analyze and summarize this PDF. Please try again.')
    } finally {
      setUploading(false)
      setUploadStep('')
    }
  }

  const handleExportPDF = () => {
    if (!summary) return
    const curMat = materials.find((m) => m.id === materialId)
    exportSummaryToPDF(summary, curMat?.title || summary.materialTitle || 'Study Material')
    toast('Summary exported to PDF!', 'success')
  }

  const materialOptions = materials.length
    ? materials.map((m) => ({ value: m.id, label: m.title }))
    : [{ value: 'data-structures', label: 'Data Structures' }]

  const sections =
    summary?.sections?.filter(
      (s) =>
        !query.trim() ||
        s.title.toLowerCase().includes(query.toLowerCase()) ||
        s.body.toLowerCase().includes(query.toLowerCase())
    ) || []

  return (
    <>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <PageHeader
          title="Summaries"
          subtitle="AI-generated chapter notes, key concept extraction, and high-yield study points."
        />
        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            icon={Sparkles}
            onClick={() => setShowUploadPanel(!showUploadPanel)}
            className="shrink-0"
          >
            {showUploadPanel ? 'Close Upload' : 'Upload Any PDF for AI Summary'}
          </Button>
        </div>
      </div>

      {/* Upload Any PDF Dropzone Card */}
      {showUploadPanel && (
        <Card className="mb-6 border-brand-200 bg-brand-50/40 p-5 dark:border-brand-800/60 dark:bg-brand-950/20 animate-fade-in">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white shadow-sm">
                <FileUp size={20} />
              </span>
              <div>
                <h3 className="font-display text-base font-bold text-ink-900 dark:text-white">
                  Upload Any PDF Document
                </h3>
                <p className="text-xs text-ink-500 dark:text-ink-400">
                  Our AI (OpenAI GPT-4o-mini & PyPDF) will extract all chapters and generate structured notes.
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                setShowUploadPanel(false)
                setSelectedFile(null)
                setUploadError('')
              }}
              className="rounded-lg p-1.5 text-ink-400 hover:bg-ink-100 hover:text-ink-600 dark:hover:bg-ink-800"
            >
              <X size={18} />
            </button>
          </div>

          {uploadError && (
            <div className="mb-4 flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300">
              <AlertCircle size={15} className="shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}

          {!selectedFile ? (
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center transition-all ${
                dragActive
                  ? 'border-brand-500 bg-brand-100/60 dark:bg-brand-900/40'
                  : 'border-ink-300/80 bg-white hover:border-brand-400 hover:bg-ink-50/80 dark:border-ink-700 dark:bg-ink-900/80 dark:hover:border-brand-500'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                className="hidden"
                onChange={handleFileInputChange}
              />
              <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-100 text-brand-600 dark:bg-brand-950/60 dark:text-brand-400">
                <Upload size={28} />
              </div>
              <p className="font-display text-sm font-semibold text-ink-800 dark:text-ink-100">
                Click to browse or drop any study PDF here
              </p>
              <p className="mt-1 text-xs text-ink-500 dark:text-ink-400">
                Supports lecture slides, textbook chapters, syllabus notes (PDF up to 50MB)
              </p>
            </div>
          ) : (
            <form onSubmit={handleUploadAndSummarize} className="space-y-4">
              <div className="flex items-center justify-between rounded-xl border border-brand-200 bg-white p-3.5 dark:border-ink-800 dark:bg-ink-900">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-rose-50 text-rose-600 dark:bg-rose-950/50 dark:text-rose-400">
                    <FileText size={22} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-ink-900 dark:text-white">
                      {selectedFile.name}
                    </p>
                    <p className="text-xs text-ink-500">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • PDF Document
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedFile(null)}
                  disabled={uploading}
                  className="rounded-lg p-1.5 text-ink-400 hover:bg-ink-100 hover:text-rose-600 dark:hover:bg-ink-800"
                >
                  <X size={16} />
                </button>
              </div>

              <Input
                label="Summary / Document Title"
                placeholder="e.g. Operating Systems Chapter 7: Memory Management"
                value={customTitle}
                onChange={(e) => setCustomTitle(e.target.value)}
                disabled={uploading}
              />

              {uploading && (
                <div className="rounded-xl border border-brand-200 bg-brand-50 p-3.5 dark:border-brand-900/50 dark:bg-brand-950/40">
                  <div className="flex items-center gap-3 text-xs font-semibold text-brand-700 dark:text-brand-300">
                    <LoadingSpinner size={16} />
                    <span>{uploadStep}</span>
                  </div>
                </div>
              )}

              <div className="flex items-center justify-end gap-2.5 pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setSelectedFile(null)}
                  disabled={uploading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="gradient"
                  icon={Sparkles}
                  loading={uploading}
                >
                  Summarize with AI
                </Button>
              </div>
            </form>
          )}
        </Card>
      )}

      {/* Material Selector & Search Bar */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <Select
          className="sm:w-80"
          options={materialOptions}
          value={materialId}
          onChange={(e) => setMaterialId(e.target.value)}
          aria-label="Choose material"
        />
        <Input
          className="flex-1"
          icon={Search}
          placeholder="Search inside this summary..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search summary"
        />
      </div>

      {loading ? (
        <div className="flex min-h-[300px] items-center justify-center">
          <LoadingSpinner size={32} label="Extracting concepts & generating AI summary..." />
        </div>
      ) : error ? (
        <ErrorState message={error} onRetry={() => load(materialId)} />
      ) : (
        <div className="grid gap-5 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <div className="flex flex-col gap-3 border-b border-ink-100 pb-4 dark:border-ink-800/80 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="font-display text-lg font-bold text-ink-900 dark:text-white">
                  {summary.materialTitle || 'Document Summary'}
                </h2>
                <div className="mt-1 flex items-center gap-3 text-xs text-ink-500">
                  <span className="flex items-center gap-1">
                    <Clock size={13} /> {summary.generatedAt}
                  </span>
                  <span>•</span>
                  <span>{summary.sections?.length || 0} Key Sections</span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  icon={Download}
                  onClick={handleExportPDF}
                  title="Download Summary as PDF"
                >
                  Export PDF
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  icon={RotateCcw}
                  onClick={() => load(materialId, true)}
                  title="Regenerate with AI"
                >
                  Regenerate
                </Button>
              </div>
            </div>

            {sections.length === 0 ? (
              <EmptyState
                icon={FileText}
                title="No section matches that search"
                description="Try another word or clear the search query."
              />
            ) : (
              <div className="mt-4 space-y-3">
                {sections.map((section, index) => {
                  const open = openSections.includes(section.id)
                  const isSaved = saved.includes(`${materialId}:${section.id}`)
                  return (
                    <div
                      key={section.id}
                      className="rounded-2xl border border-ink-200/90 transition-all dark:border-ink-800"
                    >
                      <div className="flex items-center gap-2 p-4">
                        <button
                          onClick={() => toggleSection(section.id)}
                          aria-expanded={open}
                          className="flex flex-1 items-center gap-3 text-left"
                        >
                          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-50 font-display text-xs font-bold text-brand-600 dark:bg-brand-950/60 dark:text-brand-400">
                            {index + 1}
                          </span>
                          <span className="flex-1 text-sm font-semibold text-ink-900 dark:text-white">
                            {section.title}
                          </span>
                          <ChevronDown
                            size={16}
                            className={`text-ink-400 transition-transform ${open ? 'rotate-180' : ''}`}
                          />
                        </button>
                        <button
                          onClick={() => toggleSave(section.id)}
                          aria-label={isSaved ? 'Remove from saved' : 'Save section'}
                          className="rounded-lg p-1.5 text-ink-400 hover:bg-ink-100 hover:text-brand-600 dark:hover:bg-ink-800"
                        >
                          {isSaved ? <BookmarkCheck size={18} className="text-brand-600" /> : <Bookmark size={18} />}
                        </button>
                      </div>

                      {open && (
                        <div className="animate-fade-in border-t border-ink-100 px-5 py-4 dark:border-ink-800">
                          <p className="text-sm leading-relaxed text-ink-700 dark:text-ink-300">
                            {section.body}
                          </p>
                          {section.points && section.points.length > 0 && (
                            <div className="mt-4 rounded-xl bg-ink-50/80 p-3.5 dark:bg-ink-950/50">
                              <p className="mb-2 text-xs font-bold uppercase tracking-wider text-ink-500 dark:text-ink-400">
                                High-Yield Takeaways
                              </p>
                              <ul className="space-y-2">
                                {section.points.map((point, pIdx) => (
                                  <li
                                    key={pIdx}
                                    className="flex items-start gap-2.5 text-xs sm:text-sm text-ink-700 dark:text-ink-300"
                                  >
                                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-600" />
                                    <span>{point}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </Card>

          {/* Sidebar Column: Key Concepts & Quick Stats */}
          <div className="space-y-5">
            <Card className="h-fit">
              <CardHeader
                title="Key Concepts"
                subtitle="Core terms and principles extracted from this PDF"
              />
              <div className="flex flex-wrap gap-2">
                {summary.keyConcepts && summary.keyConcepts.length > 0 ? (
                  summary.keyConcepts.map((concept, idx) => (
                    <button
                      key={idx}
                      onClick={() => setQuery(concept)}
                      className="chip bg-brand-50 text-brand-700 transition-colors hover:bg-brand-100 dark:bg-brand-950/60 dark:text-brand-300 dark:hover:bg-brand-900/50"
                    >
                      {concept}
                    </button>
                  ))
                ) : (
                  <p className="text-xs text-ink-400">No key concepts identified yet.</p>
                )}
              </div>
              <p className="muted mt-5 text-xs">
                {saved.filter((s) => s.startsWith(`${materialId}:`)).length} section(s) saved for revision.
              </p>
            </Card>

            <Card className="border-ink-200/80 bg-linear-to-br from-brand-50/50 to-indigo-50/50 p-4 dark:border-ink-800 dark:from-brand-950/20 dark:to-indigo-950/20">
              <div className="flex items-center gap-2 font-display text-xs font-bold text-brand-700 dark:text-brand-300 mb-2">
                <Sparkles size={14} /> AI Engine Tip
              </div>
              <p className="text-xs leading-relaxed text-ink-600 dark:text-ink-400">
                Uploaded PDFs are also automatically indexed into the RAG vector store. You can ask questions about this document in the <strong>AI Tutor</strong> or take adaptive quizzes based on it!
              </p>
            </Card>
          </div>
        </div>
      )}
    </>
  )
}

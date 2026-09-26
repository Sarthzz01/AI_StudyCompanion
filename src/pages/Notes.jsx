import { useState, useEffect, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  FileText,
  Plus,
  Search,
  Star,
  Trash2,
  Download,
  Printer,
  Sparkles,
  Save,
  Check,
  BookOpen,
  Code,
  Tag,
  Calendar,
  AlertCircle,
  Loader2,
  ExternalLink,
} from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import Card, { CardHeader } from '../components/Card.jsx'
import Button from '../components/Button.jsx'
import Input from '../components/Input.jsx'
import Select from '../components/Select.jsx'
import Modal from '../components/Modal.jsx'
import EmptyState from '../components/EmptyState.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import {
  getNotes,
  createNote,
  updateNote,
  deleteNote,
  generateStructuredNote,
  getMaterials,
} from '../services/api.js'
import { exportNoteToPDF } from '../utils/pdfExport.js'
import { useToast } from '../context/ToastContext.jsx'

export default function Notes() {
  const [searchParams] = useSearchParams()
  const toast = useToast()

  const [notes, setNotes] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeNoteId, setActiveNoteId] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTopic, setSelectedTopic] = useState('all')

  // Editor form state
  const [title, setTitle] = useState('')
  const [topic, setTopic] = useState('Data Structures')
  const [content, setContent] = useState('')
  const [keyPoints, setKeyPoints] = useState([])
  const [examples, setExamples] = useState([])
  const [isFavorite, setIsFavorite] = useState(false)
  const [newKeyPoint, setNewKeyPoint] = useState('')
  const [newExample, setNewExample] = useState('')

  // AI Generator Modal state
  const [aiModalOpen, setAiModalOpen] = useState(false)
  const [aiPrompt, setAiPrompt] = useState('')
  const [aiTopic, setAiTopic] = useState('Data Structures')
  const [aiGenerating, setAiGenerating] = useState(false)

  const [saving, setSaving] = useState(false)
  const [materials, setMaterials] = useState([])

  // Load notes on mount
  useEffect(() => {
    loadNotes()
    getMaterials()
      .then((mats) => setMaterials(Array.isArray(mats) ? mats : []))
      .catch(() => {})
  }, [])

  // Check URL params for pre-filled source text (e.g. from AI Tutor or Summaries)
  useEffect(() => {
    const sourceText = searchParams.get('text')
    const sourceTopic = searchParams.get('topic')
    const sourceTitle = searchParams.get('title')

    if (sourceText) {
      setTitle(sourceTitle || 'Notes from AI Tutor')
      setTopic(sourceTopic || 'General Academic')
      setContent(sourceText)
      setActiveNoteId('new')
    }
  }, [searchParams])

  const loadNotes = async () => {
    setLoading(true)
    try {
      const data = await getNotes()
      setNotes(data)
      if (data.length > 0 && !activeNoteId) {
        selectNote(data[0])
      }
    } catch (err) {
      toast('Could not load notes.', 'error')
    } finally {
      setLoading(false)
    }
  }

  const selectNote = (note) => {
    setActiveNoteId(note.id)
    setTitle(note.title)
    setTopic(note.topic || 'General')
    setContent(note.content || '')
    setKeyPoints(Array.isArray(note.key_points) ? note.key_points : [])
    setExamples(Array.isArray(note.examples) ? note.examples : [])
    setIsFavorite(Boolean(note.is_favorite))
  }

  const startNewNote = () => {
    setActiveNoteId('new')
    setTitle('')
    setTopic('Data Structures')
    setContent('')
    setKeyPoints([])
    setExamples([])
    setIsFavorite(false)
  }

  const handleSave = async () => {
    if (!title.trim()) {
      return toast('Please enter a note title.', 'error')
    }
    if (!content.trim()) {
      return toast('Note content cannot be empty.', 'error')
    }

    setSaving(true)
    try {
      const payload = {
        title: title.trim(),
        topic: topic.trim() || 'General',
        content: content.trim(),
        key_points: keyPoints,
        examples: examples,
        is_favorite: isFavorite,
      }

      if (activeNoteId === 'new' || !activeNoteId) {
        const created = await createNote(payload)
        setNotes((prev) => [created, ...prev])
        setActiveNoteId(created.id)
        toast('Note created successfully!', 'success')
      } else {
        const updated = await updateNote(activeNoteId, payload)
        setNotes((prev) => prev.map((n) => (n.id === activeNoteId ? updated : n)))
        toast('Note saved successfully!', 'success')
      }
    } catch (err) {
      toast(err.message || 'Failed to save note.', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this note?')) return
    try {
      await deleteNote(id)
      const remaining = notes.filter((n) => n.id !== id)
      setNotes(remaining)
      toast('Note deleted.', 'info')
      if (activeNoteId === id) {
        if (remaining.length > 0) selectNote(remaining[0])
        else startNewNote()
      }
    } catch (err) {
      toast('Failed to delete note.', 'error')
    }
  }

  const handleToggleFavorite = async () => {
    const nextFav = !isFavorite
    setIsFavorite(nextFav)
    if (activeNoteId && activeNoteId !== 'new') {
      try {
        await updateNote(activeNoteId, { is_favorite: nextFav })
        setNotes((prev) => prev.map((n) => (n.id === activeNoteId ? { ...n, is_favorite: nextFav } : n)))
      } catch (err) {
        // revert on failure
        setIsFavorite(!nextFav)
      }
    }
  }

  const handleAddKeyPoint = () => {
    if (!newKeyPoint.trim()) return
    setKeyPoints((prev) => [...prev, newKeyPoint.trim()])
    setNewKeyPoint('')
  }

  const handleRemoveKeyPoint = (idx) => {
    setKeyPoints((prev) => prev.filter((_, i) => i !== idx))
  }

  const handleAddExample = () => {
    if (!newExample.trim()) return
    setExamples((prev) => [...prev, newExample.trim()])
    setNewExample('')
  }

  const handleRemoveExample = (idx) => {
    setExamples((prev) => prev.filter((_, i) => i !== idx))
  }

  const handleExportPDF = () => {
    if (!title.trim() && !content.trim()) {
      return toast('Cannot export an empty note.', 'error')
    }
    const currentNoteData = {
      title: title || 'Study Notes',
      topic: topic || 'General Academic',
      content: content || '',
      key_points: keyPoints,
      examples: examples,
      updated_at: new Date().toLocaleDateString('en-US', { dateStyle: 'medium' }),
    }
    exportNoteToPDF(currentNoteData)
    toast('PDF generated and download started!', 'success')
  }

  const handleAiGenerate = async () => {
    if (!aiPrompt.trim()) {
      return toast('Please enter a question, topic, or source explanation.', 'error')
    }
    setAiGenerating(true)
    try {
      const res = await generateStructuredNote({
        content_or_prompt: aiPrompt.trim(),
        topic: aiTopic,
      })
      setTitle(res.title)
      setTopic(res.topic)
      setContent(res.content)
      setKeyPoints(res.key_points || [])
      setExamples(res.examples || [])
      setActiveNoteId('new')
      setAiModalOpen(false)
      setAiPrompt('')
      toast('AI generated structured notes successfully!', 'success')
    } catch (err) {
      toast(err.message || 'AI generation failed. Please try again.', 'error')
    } finally {
      setAiGenerating(false)
    }
  }

  const handleAiEnhanceCurrent = async () => {
    if (!content.trim()) {
      return toast('Please write some content first to enhance.', 'error')
    }
    setSaving(true)
    try {
      const res = await generateStructuredNote({
        content_or_prompt: content,
        topic: topic,
      })
      if (!title.trim()) setTitle(res.title)
      if (res.key_points?.length) setKeyPoints(res.key_points)
      if (res.examples?.length) setExamples(res.examples)
      toast('AI enhanced key takeaways and examples!', 'success')
    } catch (err) {
      toast('AI enhancement unavailable. Please check your content.', 'error')
    } finally {
      setSaving(false)
    }
  }

  // Filter notes
  const filteredNotes = useMemo(() => {
    return notes.filter((n) => {
      const matchesSearch =
        !searchQuery.trim() ||
        n.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (n.content && n.content.toLowerCase().includes(searchQuery.toLowerCase()))
      const matchesTopic =
        selectedTopic === 'all' || (n.topic && n.topic.toLowerCase() === selectedTopic.toLowerCase())
      return matchesSearch && matchesTopic
    })
  }, [notes, searchQuery, selectedTopic])

  const availableTopics = useMemo(() => {
    const set = new Set(notes.map((n) => n.topic).filter(Boolean))
    return ['all', ...Array.from(set)]
  }, [notes])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Study Notes & PDF Studio"
        subtitle="Transform AI tutor answers and lectures into structured academic notes with instant PDF downloads."
        actions={
          <div className="flex items-center gap-2.5">
            <Button
              variant="outline"
              size="sm"
              icon={Sparkles}
              onClick={() => setAiModalOpen(true)}
              className="text-brand-600 dark:text-brand-400"
            >
              Generate with AI
            </Button>
            <Button variant="primary" size="sm" icon={Plus} onClick={startNewNote}>
              New Note
            </Button>
          </div>
        }
      />

      <div className="grid gap-5 lg:grid-cols-12">
        {/* Left Column: Notes List & Filter (4 cols) */}
        <div className="space-y-4 lg:col-span-4">
          <Card className="p-4 border border-ink-200/90 dark:border-ink-800/80">
            {/* Search */}
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
              <input
                type="text"
                placeholder="Search notes…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-xl border border-ink-200/90 bg-ink-50/60 py-2 pl-9 pr-3 text-xs text-ink-900 placeholder:text-ink-400 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-ink-800 dark:bg-ink-950/60 dark:text-ink-100 dark:focus:bg-ink-900"
              />
            </div>

            {/* Topic Filter Chips */}
            {availableTopics.length > 2 && (
              <div className="mt-3 flex flex-wrap gap-1.5 border-t border-ink-100 pt-3 dark:border-ink-800">
                {availableTopics.map((t) => (
                  <button
                    key={t}
                    onClick={() => setSelectedTopic(t)}
                    className={`rounded-lg px-2.5 py-1 text-[11px] font-medium capitalize transition-all ${
                      selectedTopic === t
                        ? 'bg-brand-600 text-white shadow-xs'
                        : 'bg-ink-100/70 text-ink-600 hover:bg-ink-200/70 dark:bg-ink-800/60 dark:text-ink-300'
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            )}
          </Card>

          {/* Notes Item Cards */}
          <div className="space-y-2.5 max-h-[68vh] overflow-y-auto pr-1">
            {loading ? (
              <div className="flex h-40 flex-col items-center justify-center gap-2">
                <LoadingSpinner size={24} label="Loading notes…" />
              </div>
            ) : filteredNotes.length === 0 ? (
              <Card className="p-6 text-center border-dashed">
                <FileText size={28} className="mx-auto text-ink-300 dark:text-ink-700 mb-2" />
                <p className="text-xs font-semibold text-ink-800 dark:text-ink-200">No notes found</p>
                <p className="mt-1 text-[11px] text-ink-500">
                  {searchQuery ? 'Try a different search keyword.' : 'Click "New Note" or "Generate with AI" to begin.'}
                </p>
              </Card>
            ) : (
              filteredNotes.map((n) => {
                const isSelected = activeNoteId === n.id
                return (
                  <div
                    key={n.id}
                    onClick={() => selectNote(n)}
                    className={`group relative cursor-pointer rounded-2xl border p-4 transition-all duration-150 ${
                      isSelected
                        ? 'border-brand-500 bg-brand-50/40 shadow-xs dark:border-brand-500/80 dark:bg-brand-950/30'
                        : 'border-ink-200/80 bg-white hover:border-brand-300 hover:shadow-xs dark:border-ink-800/80 dark:bg-ink-900/90'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="truncate text-sm font-semibold text-ink-900 dark:text-white">
                            {n.title || 'Untitled Note'}
                          </h3>
                          {n.is_favorite && (
                            <Star size={12} className="shrink-0 fill-amber-400 text-amber-400" />
                          )}
                        </div>
                        <p className="mt-1 line-clamp-2 text-xs text-ink-600 dark:text-ink-400 leading-relaxed">
                          {n.content?.slice(0, 100) || 'No content'}
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDelete(n.id)
                        }}
                        title="Delete note"
                        className="rounded-lg p-1 text-ink-400 opacity-0 transition-opacity hover:bg-rose-50 hover:text-rose-600 group-hover:opacity-100 dark:hover:bg-rose-950/50 dark:hover:text-rose-400"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>

                    <div className="mt-3 flex items-center justify-between border-t border-ink-100/80 pt-2 text-[10px] text-ink-400 dark:border-ink-800/80 dark:text-ink-500">
                      <span className="font-semibold uppercase tracking-wider text-brand-600 dark:text-brand-400">
                        {n.topic || 'General'}
                      </span>
                      <span>{n.updated_at || 'Recent'}</span>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* Right Column: Note Editor & PDF Actions (8 cols) */}
        <div className="lg:col-span-8">
          <Card className="space-y-5 p-6 border border-ink-200/90 dark:border-ink-800/80">
            {/* Editor Action Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-ink-100 pb-4 dark:border-ink-800">
              <div className="flex items-center gap-2">
                <button
                  onClick={handleToggleFavorite}
                  className={`flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-xs font-semibold transition ${
                    isFavorite
                      ? 'border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300'
                      : 'border-ink-200 text-ink-600 hover:bg-ink-100 dark:border-ink-800 dark:text-ink-300'
                  }`}
                >
                  <Star size={13} className={isFavorite ? 'fill-amber-500 text-amber-500' : ''} />
                  {isFavorite ? 'Favorited' : 'Favorite'}
                </button>

                <Button
                  variant="outline"
                  size="sm"
                  icon={Sparkles}
                  onClick={handleAiEnhanceCurrent}
                  loading={saving}
                  title="Auto-extract key points and examples from note content"
                >
                  AI Enhance
                </Button>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  icon={Download}
                  onClick={handleExportPDF}
                  className="text-brand-600 dark:text-brand-400"
                >
                  Download PDF
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  icon={Printer}
                  onClick={() => window.print()}
                >
                  Print
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  icon={Save}
                  onClick={handleSave}
                  loading={saving}
                >
                  Save Note
                </Button>
              </div>
            </div>

            {/* Note Metadata Inputs */}
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="sm:col-span-2">
                <label className="label">Note Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Binary Search Trees & Traversal Properties"
                  className="field font-semibold text-base sm:text-lg"
                />
              </div>
              <div>
                <label className="label">Subject / Topic</label>
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g. Data Structures"
                  className="field"
                />
              </div>
            </div>

            {/* Note Content Textarea */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="label mb-0">Detailed Content & Explanations (Markdown Supported)</label>
                <span className="text-[11px] text-ink-400">Use ## for Section Headings, - for bullets</span>
              </div>
              <textarea
                rows={10}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Write your study notes or paste explanations from your AI Tutor sessions..."
                className="field font-mono text-xs sm:text-sm leading-relaxed resize-y"
              />
            </div>

            {/* Key Takeaways & Exam Points Box */}
            <div className="rounded-2xl border border-brand-100 bg-brand-50/30 p-4 dark:border-brand-900/40 dark:bg-brand-950/20">
              <div className="flex items-center justify-between mb-2.5">
                <h4 className="text-xs font-bold uppercase tracking-wider text-brand-800 dark:text-brand-300 flex items-center gap-1.5">
                  <Check size={14} className="text-brand-600" />
                  Key Takeaways & Core Concepts
                </h4>
                <span className="text-[11px] text-brand-700 dark:text-brand-400">
                  {keyPoints.length} point{keyPoints.length === 1 ? '' : 's'}
                </span>
              </div>

              {keyPoints.length > 0 && (
                <div className="space-y-1.5 mb-3">
                  {keyPoints.map((pt, idx) => (
                    <div
                      key={idx}
                      className="flex items-start justify-between gap-2 rounded-xl bg-white p-2.5 text-xs text-ink-800 shadow-2xs dark:bg-ink-900 dark:text-ink-200 border border-brand-100/60 dark:border-brand-900/30"
                    >
                      <span className="flex items-start gap-2 min-w-0">
                        <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-600" />
                        <span className="leading-relaxed">{pt}</span>
                      </span>
                      <button
                        onClick={() => handleRemoveKeyPoint(idx)}
                        className="text-ink-400 hover:text-rose-600 dark:hover:text-rose-400"
                        title="Remove point"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Add a high-yield exam bullet point…"
                  value={newKeyPoint}
                  onChange={(e) => setNewKeyPoint(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      handleAddKeyPoint()
                    }
                  }}
                  className="field py-1.5 text-xs bg-white dark:bg-ink-950"
                />
                <Button size="sm" variant="secondary" onClick={handleAddKeyPoint}>
                  Add
                </Button>
              </div>
            </div>

            {/* Practical Examples Section */}
            <div className="rounded-2xl border border-indigo-100 bg-indigo-50/30 p-4 dark:border-indigo-900/40 dark:bg-indigo-950/20">
              <div className="flex items-center justify-between mb-2.5">
                <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-800 dark:text-indigo-300 flex items-center gap-1.5">
                  <Code size={14} className="text-indigo-600" />
                  Practical Examples & Code Snippets
                </h4>
                <span className="text-[11px] text-indigo-700 dark:text-indigo-400">
                  {examples.length} example{examples.length === 1 ? '' : 's'}
                </span>
              </div>

              {examples.length > 0 && (
                <div className="space-y-2 mb-3">
                  {examples.map((ex, idx) => (
                    <div
                      key={idx}
                      className="rounded-xl border border-indigo-100 bg-white p-3 font-mono text-xs text-ink-800 shadow-2xs dark:border-indigo-900/40 dark:bg-ink-900 dark:text-ink-200"
                    >
                      <div className="flex items-center justify-between mb-1.5 text-[10px] text-indigo-600 font-sans font-semibold">
                        <span>Example {idx + 1}</span>
                        <button
                          onClick={() => handleRemoveExample(idx)}
                          className="text-ink-400 hover:text-rose-600"
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                      <pre className="whitespace-pre-wrap leading-relaxed">{ex}</pre>
                    </div>
                  ))}
                </div>
              )}

              <div className="space-y-2">
                <textarea
                  rows={2}
                  placeholder="Paste an illustrative example, code block, or calculation…"
                  value={newExample}
                  onChange={(e) => setNewExample(e.target.value)}
                  className="field py-1.5 font-mono text-xs bg-white dark:bg-ink-950 resize-y"
                />
                <Button size="sm" variant="secondary" onClick={handleAddExample}>
                  Add Example
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* AI Generate Notes Modal */}
      <Modal
        open={aiModalOpen}
        onClose={() => setAiModalOpen(false)}
        title="AI Structured Note Generator"
        description="Provide a topic, lecture concept, or paste an AI explanation to generate university-standard structured study notes."
        footer={
          <>
            <Button variant="secondary" onClick={() => setAiModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAiGenerate} loading={aiGenerating} icon={Sparkles}>
              Generate Notes
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="label">Topic Context</label>
            <input
              type="text"
              value={aiTopic}
              onChange={(e) => setAiTopic(e.target.value)}
              placeholder="e.g. Operating Systems / Page Replacement Algorithms"
              className="field"
            />
          </div>
          <div>
            <label className="label">Prompt, Topic, or Raw Explanation</label>
            <textarea
              rows={6}
              value={aiPrompt}
              onChange={(e) => setAiPrompt(e.target.value)}
              placeholder="e.g. Explain LRU page replacement algorithm with an example frame sequence and time complexity..."
              className="field resize-none text-xs leading-relaxed"
            />
          </div>
        </div>
      </Modal>
    </div>
  )
}

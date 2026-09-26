import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ChevronDown, Search, Bookmark, BookmarkCheck, FileText } from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import Card, { CardHeader } from '../components/Card.jsx'
import Select from '../components/Select.jsx'
import Input from '../components/Input.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import ErrorState from '../components/ErrorState.jsx'
import EmptyState from '../components/EmptyState.jsx'
import { generateSummary, getMaterials } from '../services/api.js'
import { useToast } from '../context/ToastContext.jsx'
import { readStorage, writeStorage } from '../utils/storage.js'

export default function Summaries() {
  const [searchParams] = useSearchParams()
  const toast = useToast()

  const [materials, setMaterials] = useState([])
  const [materialId, setMaterialId] = useState(searchParams.get('material') || 'data-structures')
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [openSections, setOpenSections] = useState(['s1'])
  const [query, setQuery] = useState('')
  const [saved, setSaved] = useState(() => readStorage('savedSummaries', []))

  useEffect(() => {
    getMaterials().then(setMaterials).catch(() => setMaterials([]))
  }, [])

  const load = async (id) => {
    setLoading(true)
    setError(null)
    try {
      const data = await generateSummary(id)
      setSummary(data)
      setOpenSections(data.sections.length ? [data.sections[0].id] : [])
    } catch (err) {
      setError(err.message)
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

  const materialOptions = materials.length
    ? materials.map((m) => ({ value: m.id, label: m.title }))
    : [{ value: 'data-structures', label: 'Data Structures' }]

  const sections =
    summary?.sections.filter(
      (s) =>
        !query.trim() ||
        s.title.toLowerCase().includes(query.toLowerCase()) ||
        s.body.toLowerCase().includes(query.toLowerCase())
    ) || []

  return (
    <>
      <PageHeader title="Summaries" subtitle="AI-generated section notes from your material." />

      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <Select
          className="sm:w-72"
          options={materialOptions}
          value={materialId}
          onChange={(e) => setMaterialId(e.target.value)}
          aria-label="Choose material"
        />
        <Input
          className="flex-1"
          icon={Search}
          placeholder="Search inside this summary"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search summary"
        />
      </div>

      {loading ? (
        <LoadingSpinner label="Generating the summary…" />
      ) : error ? (
        <ErrorState message={error} onRetry={() => load(materialId)} />
      ) : (
        <div className="grid gap-5 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader title="AI summary" subtitle={`Generated ${summary.generatedAt}`} />
            {sections.length === 0 ? (
              <EmptyState icon={FileText} title="No section matches that search" description="Try another word from the material." />
            ) : (
              <div className="space-y-3">
                {sections.map((section, index) => {
                  const open = openSections.includes(section.id)
                  const isSaved = saved.includes(`${materialId}:${section.id}`)
                  return (
                    <div key={section.id} className="rounded-xl border border-ink-200 dark:border-ink-800">
                      <div className="flex items-center gap-2 p-4">
                        <button
                          onClick={() => toggleSection(section.id)}
                          aria-expanded={open}
                          className="flex flex-1 items-center gap-3 text-left"
                        >
                          <span className="font-display text-sm font-semibold text-brand-600">{index + 1}</span>
                          <span className="flex-1 text-sm font-semibold">{section.title}</span>
                          <ChevronDown size={16} className={`text-ink-400 transition-transform ${open ? 'rotate-180' : ''}`} />
                        </button>
                        <button
                          onClick={() => toggleSave(section.id)}
                          aria-label={isSaved ? 'Remove from saved' : 'Save section'}
                          className="rounded-lg p-1.5 text-ink-400 hover:bg-ink-100 hover:text-brand-600 dark:hover:bg-ink-800"
                        >
                          {isSaved ? <BookmarkCheck size={16} className="text-brand-600" /> : <Bookmark size={16} />}
                        </button>
                      </div>

                      {open && (
                        <div className="animate-fade-in border-t border-ink-200 px-4 py-4 dark:border-ink-800">
                          <p className="text-sm leading-relaxed text-ink-700 dark:text-ink-300">{section.body}</p>
                          <ul className="mt-4 space-y-2">
                            {section.points.map((point) => (
                              <li key={point} className="flex items-start gap-2.5 text-sm text-ink-700 dark:text-ink-300">
                                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-600" />
                                {point}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </Card>

          <Card className="h-fit">
            <CardHeader title="Key concepts" subtitle="What to be able to define" />
            <div className="flex flex-wrap gap-2">
              {summary.keyConcepts.map((concept) => (
                <span key={concept} className="chip bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300">
                  {concept}
                </span>
              ))}
            </div>
            <p className="muted mt-5">
              {saved.filter((s) => s.startsWith(`${materialId}:`)).length} section(s) saved from this material.
            </p>
          </Card>
        </div>
      )}
    </>
  )
}

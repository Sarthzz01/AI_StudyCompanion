import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { Play, History, Sparkles, X } from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import Card, { CardHeader } from '../components/Card.jsx'
import Select from '../components/Select.jsx'
import Button from '../components/Button.jsx'
import EmptyState from '../components/EmptyState.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import { getMaterials, getQuizAttempts } from '../services/api.js'
import { useStudyData } from '../context/StudyDataContext.jsx'

export default function Quizzes() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const { attempts } = useStudyData()

  const [materials, setMaterials] = useState([])
  const [loading, setLoading] = useState(true)
  const [backendAttempts, setBackendAttempts] = useState([])
  const [config, setConfig] = useState({
    materialId: searchParams.get('material') || 'data-structures',
    topic: searchParams.get('topic') || 'All topics',
    difficulty: searchParams.get('difficulty') || 'mixed',
    count: Number(searchParams.get('count')) || 5,
  })

  useEffect(() => {
    getMaterials()
      .then((mats) => {
        setMaterials(mats || [])
        const targetTopic = searchParams.get('topic')
        const targetMaterial = searchParams.get('material')
        const targetDifficulty = searchParams.get('difficulty')
        const targetCount = searchParams.get('count')

        if (targetTopic) {
          // Find matching material
          let matchedMat = null
          let matchedTopicName = targetTopic

          if (targetMaterial) {
            matchedMat = (mats || []).find((m) => m.id === targetMaterial)
          }

          if (!matchedMat) {
            // Find material containing this topic (exact or case-insensitive)
            matchedMat = (mats || []).find((m) =>
              (m.topics || []).some((t) => {
                const tName = typeof t === 'string' ? t : t.name
                return (
                  tName &&
                  (tName.toLowerCase() === targetTopic.toLowerCase() ||
                    tName.toLowerCase().includes(targetTopic.toLowerCase()) ||
                    targetTopic.toLowerCase().includes(tName.toLowerCase()))
                )
              })
            )
          }

          if (matchedMat) {
            const foundTopic = (matchedMat.topics || []).find((t) => {
              const tName = typeof t === 'string' ? t : t.name
              return (
                tName &&
                (tName.toLowerCase() === targetTopic.toLowerCase() ||
                  tName.toLowerCase().includes(targetTopic.toLowerCase()) ||
                  targetTopic.toLowerCase().includes(tName.toLowerCase()))
              )
            })
            if (foundTopic) {
              matchedTopicName = typeof foundTopic === 'string' ? foundTopic : foundTopic.name
            }
          }

          setConfig((prev) => ({
            ...prev,
            materialId: matchedMat ? matchedMat.id : targetMaterial || prev.materialId,
            topic: matchedTopicName || targetTopic,
            difficulty: targetDifficulty || prev.difficulty || 'medium',
            count: targetCount ? Number(targetCount) : prev.count,
          }))
        } else if (targetMaterial) {
          setConfig((prev) => ({
            ...prev,
            materialId: targetMaterial,
            difficulty: targetDifficulty || prev.difficulty || 'mixed',
            count: targetCount ? Number(targetCount) : prev.count,
          }))
        }
      })
      .finally(() => setLoading(false))
  }, [searchParams])

  useEffect(() => {
    getQuizAttempts(config.materialId)
      .then((data) => {
        if (data && Array.isArray(data)) setBackendAttempts(data)
      })
      .catch(() => {})
  }, [config.materialId])

  const selected = materials.find((m) => m.id === config.materialId)

  const topicOptions = useMemo(() => {
    const rawTopics = selected?.topics?.map((t) => (typeof t === 'string' ? t : t.name)) || []
    const list = ['All topics', ...rawTopics]
    if (config.topic && config.topic !== 'All topics' && !list.includes(config.topic)) {
      list.push(config.topic)
    }
    return list
  }, [selected, config.topic])

  const start = () => {
    const params = new URLSearchParams({
      material: config.materialId,
      topic: config.topic,
      difficulty: config.difficulty,
      count: String(config.count),
    })
    navigate(`/quizzes/new?${params.toString()}`)
  }

  const clearTopicFilter = () => {
    setConfig((c) => ({ ...c, topic: 'All topics' }))
    setSearchParams({})
  }

  if (loading) return <LoadingSpinner label="Loading quiz options…" />

  const displayAttempts = backendAttempts.length > 0 ? backendAttempts : attempts
  const isTopicFiltered = config.topic && config.topic !== 'All topics'

  return (
    <>
      <PageHeader title="Quizzes" subtitle="Pick what to practise, then start whenever you are ready." />

      <div className="grid gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader
            title="New quiz"
            subtitle={
              isTopicFiltered
                ? `Topic-specific practice mode: ${config.topic}`
                : 'Questions are generated from the selected material.'
            }
            action={
              isTopicFiltered && (
                <span className="flex items-center gap-1.5 rounded-full bg-brand-50 px-2.5 py-1 text-xs font-semibold text-brand-700 dark:bg-brand-900/50 dark:text-brand-300">
                  <Sparkles size={13} />
                  Topic: {config.topic}
                  <button
                    onClick={clearTopicFilter}
                    className="ml-1 rounded p-0.5 hover:bg-brand-200/50 dark:hover:bg-brand-800"
                    title="Clear topic filter"
                  >
                    <X size={12} />
                  </button>
                </span>
              )
            }
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <Select
              label="Material"
              options={materials.map((m) => ({ value: m.id, label: m.title }))}
              value={config.materialId}
              onChange={(e) => setConfig((c) => ({ ...c, materialId: e.target.value, topic: 'All topics' }))}
            />
            <Select
              label="Topic"
              options={topicOptions}
              value={config.topic}
              onChange={(e) => setConfig((c) => ({ ...c, topic: e.target.value }))}
            />
            <Select
              label="Difficulty"
              options={[
                { value: 'mixed', label: 'Mixed' },
                { value: 'easy', label: 'Easy' },
                { value: 'medium', label: 'Medium' },
                { value: 'hard', label: 'Hard' },
              ]}
              value={config.difficulty}
              onChange={(e) => setConfig((c) => ({ ...c, difficulty: e.target.value }))}
            />
            <Select
              label="Number of questions"
              options={[
                { value: '5', label: '5 questions' },
                { value: '8', label: '8 questions' },
                { value: '10', label: '10 questions' },
              ]}
              value={String(config.count)}
              onChange={(e) => setConfig((c) => ({ ...c, count: Number(e.target.value) }))}
            />
          </div>

          <Button className="mt-6" icon={Play} onClick={start}>
            {isTopicFiltered ? `Start ${config.topic} Quiz` : 'Start quiz'}
          </Button>
          <p className="muted mt-3">
            {isTopicFiltered
              ? `Questions will be specifically generated for "${config.topic}" at ${config.difficulty} difficulty.`
              : 'If a topic has fewer questions than you asked for, you will get everything available for it.'}
          </p>
        </Card>

        <Card>
          <CardHeader title="Previous attempts" action={<History size={18} className="text-ink-400" />} />
          {displayAttempts.length === 0 ? (
            <EmptyState icon={History} title="No attempts yet" description="Your scores will appear here after your first quiz." />
          ) : (
            <ul className="space-y-3">
              {displayAttempts.slice(0, 6).map((a) => (
                <li key={a.id} className="rounded-xl border border-ink-200 p-3 dark:border-ink-800">
                  <div className="flex items-center justify-between gap-3">
                    <p className="truncate text-sm font-semibold">{a.materialTitle}</p>
                    <span
                      className={`chip ${
                        a.accuracy >= 70
                          ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300'
                          : 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300'
                      }`}
                    >
                      {a.accuracy}%
                    </span>
                  </div>
                  <p className="muted mt-1">
                    {a.topic} · {a.score}/{a.total} · {a.date}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </>
  )
}

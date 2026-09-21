import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Play, History } from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import Card, { CardHeader } from '../components/Card.jsx'
import Select from '../components/Select.jsx'
import Button from '../components/Button.jsx'
import EmptyState from '../components/EmptyState.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import { getMaterials, getQuizAttempts } from '../services/api.js'
import { useStudyData } from '../context/StudyDataContext.jsx'

export default function Quizzes() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { attempts } = useStudyData()

  const [materials, setMaterials] = useState([])
  const [loading, setLoading] = useState(true)
  const [backendAttempts, setBackendAttempts] = useState([])
  const [config, setConfig] = useState({
    materialId: searchParams.get('material') || 'data-structures',
    topic: 'All topics',
    difficulty: 'mixed',
    count: 5,
  })

  useEffect(() => {
    getMaterials()
      .then(setMaterials)
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    getQuizAttempts(config.materialId)
      .then((data) => {
        if (data && Array.isArray(data)) setBackendAttempts(data)
      })
      .catch(() => {})
  }, [config.materialId])

  const selected = materials.find((m) => m.id === config.materialId)

  const topicOptions = useMemo(
    () => ['All topics', ...(selected?.topics.map((t) => t.name) || [])],
    [selected]
  )

  const start = () => {
    const params = new URLSearchParams({
      material: config.materialId,
      topic: config.topic,
      difficulty: config.difficulty,
      count: String(config.count),
    })
    navigate(`/quizzes/new?${params.toString()}`)
  }

  if (loading) return <LoadingSpinner label="Loading quiz options…" />

  const displayAttempts = backendAttempts.length > 0 ? backendAttempts : attempts

  return (
    <>
      <PageHeader title="Quizzes" subtitle="Pick what to practise, then start whenever you are ready." />

      <div className="grid gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader title="New quiz" subtitle="Questions are generated from the selected material." />
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
            Start quiz
          </Button>
          <p className="muted mt-3">
            If a topic has fewer questions than you asked for, you will get everything available for it.
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

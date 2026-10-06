import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import {
  Play,
  History,
  Sparkles,
  X,
  BookOpenCheck,
  Clock,
  CheckCircle2,
  AlertCircle,
  Calendar,
  Layers,
  Award,
  ArrowRight,
} from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import Card, { CardHeader } from '../components/Card.jsx'
import Select from '../components/Select.jsx'
import Button from '../components/Button.jsx'
import EmptyState from '../components/EmptyState.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import { getMaterials, getQuizAttempts, getStudentAssignedAssessments } from '../services/api.js'
import { useStudyData } from '../context/StudyDataContext.jsx'

export default function Quizzes() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const { attempts } = useStudyData()

  // Tab State: 'assigned' (Instructor Assessments) vs 'practice' (Self-Study Quizzes)
  const initialTab = searchParams.get('tab') || (searchParams.get('material') || searchParams.get('topic') ? 'practice' : 'assigned')
  const [activeTab, setActiveTab] = useState(initialTab)

  // Assigned Assessments State
  const [assignedAssessments, setAssignedAssessments] = useState([])
  const [assignedLoading, setAssignedLoading] = useState(true)

  // Practice Quizzes State
  const [materials, setMaterials] = useState([])
  const [practiceLoading, setPracticeLoading] = useState(true)
  const [backendAttempts, setBackendAttempts] = useState([])
  const [config, setConfig] = useState({
    materialId: searchParams.get('material') || 'data-structures',
    topic: searchParams.get('topic') || 'All topics',
    difficulty: searchParams.get('difficulty') || 'mixed',
    count: Number(searchParams.get('count')) || 5,
  })

  // Load Assigned Assessments
  const loadAssigned = async () => {
    setAssignedLoading(true)
    try {
      const data = await getStudentAssignedAssessments()
      setAssignedAssessments(Array.isArray(data) ? data : [])
    } catch (err) {
      console.warn('Failed to fetch assigned assessments:', err)
      setAssignedAssessments([])
    } finally {
      setAssignedLoading(false)
    }
  }

  useEffect(() => {
    loadAssigned()
  }, [])

  // Load Materials & Setup Practice Mode
  useEffect(() => {
    getMaterials()
      .then((mats) => {
        setMaterials(mats || [])
        const targetTopic = searchParams.get('topic')
        const targetMaterial = searchParams.get('material')
        const targetDifficulty = searchParams.get('difficulty')
        const targetCount = searchParams.get('count')

        if (targetTopic) {
          let matchedMat = null
          let matchedTopicName = targetTopic

          if (targetMaterial) {
            matchedMat = (mats || []).find((m) => m.id === targetMaterial)
          }

          if (!matchedMat) {
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
      .finally(() => setPracticeLoading(false))
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

  const startPractice = () => {
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

  const handleTakeAssessment = (asgn) => {
    navigate(`/quizzes/attempt?assessment=${asgn.assessment_id}&assignment=${asgn.assignment_id}`)
  }

  const pendingAssignedCount = assignedAssessments.filter((a) => !a.is_submitted).length
  const displayAttempts = backendAttempts.length > 0 ? backendAttempts : attempts
  const isTopicFiltered = config.topic && config.topic !== 'All topics'

  return (
    <>
      <PageHeader
        title="Quizzes & Assessments"
        subtitle="Complete instructor-assigned evaluations or practice self-study quizzes on any syllabus topic."
      />

      {/* Primary Tab Navigation */}
      <div className="mb-6 flex border-b border-ink-200 dark:border-ink-800">
        <button
          onClick={() => setActiveTab('assigned')}
          className={`flex items-center gap-2 border-b-2 px-5 py-3 text-sm font-semibold transition-colors ${
            activeTab === 'assigned'
              ? 'border-brand-600 text-brand-600 dark:border-brand-400 dark:text-brand-400'
              : 'border-transparent text-ink-500 hover:text-ink-800 dark:text-ink-400 dark:hover:text-ink-200'
          }`}
        >
          <BookOpenCheck size={17} />
          <span>Assigned Assessments</span>
          {pendingAssignedCount > 0 ? (
            <span className="rounded-full bg-brand-100 px-2 py-0.5 text-xs font-bold text-brand-700 dark:bg-brand-950/80 dark:text-brand-300">
              {pendingAssignedCount} pending
            </span>
          ) : (
            <span className="rounded-full bg-ink-100 px-2 py-0.5 text-xs font-medium text-ink-500 dark:bg-ink-800 dark:text-ink-400">
              {assignedAssessments.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('practice')}
          className={`flex items-center gap-2 border-b-2 px-5 py-3 text-sm font-semibold transition-colors ${
            activeTab === 'practice'
              ? 'border-brand-600 text-brand-600 dark:border-brand-400 dark:text-brand-400'
              : 'border-transparent text-ink-500 hover:text-ink-800 dark:text-ink-400 dark:hover:text-ink-200'
          }`}
        >
          <Sparkles size={17} />
          <span>Self-Study Quizzes</span>
        </button>
      </div>

      {/* ============================================================ */}
      {/* TAB 1: Assigned Assessments                                  */}
      {/* ============================================================ */}
      {activeTab === 'assigned' && (
        <div>
          {assignedLoading ? (
            <div className="py-16">
              <LoadingSpinner label="Fetching your assigned evaluations…" />
            </div>
          ) : assignedAssessments.length === 0 ? (
            <EmptyState
              icon={BookOpenCheck}
              title="No assigned assessments"
              description="Your instructor has not assigned any pending assessments to your class. You can sharpen your skills using our AI practice mode anytime."
              actionLabel="Practice a topic quiz"
              onAction={() => setActiveTab('practice')}
            />
          ) : (
            <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
              {assignedAssessments.map((asgn) => {
                const isPassed = asgn.is_submitted && asgn.passed
                const isFailed = asgn.is_submitted && !asgn.passed

                return (
                  <Card
                    key={asgn.assignment_id || asgn.assessment_id}
                    className="flex flex-col justify-between hover:shadow-md transition-shadow border-ink-200/90 dark:border-ink-800/90"
                  >
                    <div className="space-y-3">
                      <div className="flex items-start justify-between gap-2">
                        <span className="rounded-lg bg-brand-50 px-2.5 py-1 text-xs font-semibold text-brand-700 dark:bg-brand-950/60 dark:text-brand-300">
                          {asgn.topic}
                        </span>
                        <div className="flex items-center gap-1.5">
                          <span className="rounded-full bg-ink-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-ink-600 dark:bg-ink-800 dark:text-ink-400">
                            {asgn.difficulty}
                          </span>
                          {asgn.is_submitted ? (
                            isPassed ? (
                              <span className="chip bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300">
                                Passed
                              </span>
                            ) : (
                              <span className="chip bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300">
                                Needs Review
                              </span>
                            )
                          ) : (
                            <span className="chip bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300 font-semibold animate-pulse">
                              Pending
                            </span>
                          )}
                        </div>
                      </div>

                      <div>
                        <h3 className="font-bold text-ink-900 dark:text-ink-100 line-clamp-1 leading-snug">
                          {asgn.title}
                        </h3>
                        {asgn.instructions ? (
                          <p className="mt-1 text-xs text-ink-600 dark:text-ink-300 line-clamp-2 italic">
                            &ldquo;{asgn.instructions}&rdquo;
                          </p>
                        ) : (
                          <p className="mt-1 text-xs text-ink-500 dark:text-ink-400">
                            Official course evaluation assigned by faculty.
                          </p>
                        )}
                      </div>

                      <div className="grid grid-cols-3 gap-2 rounded-xl bg-ink-50/70 p-2.5 text-center text-xs dark:bg-ink-800/40">
                        <div>
                          <span className="block text-[10px] font-semibold text-ink-400">Questions</span>
                          <span className="font-bold text-ink-800 dark:text-ink-200">{asgn.question_count}</span>
                        </div>
                        <div>
                          <span className="block text-[10px] font-semibold text-ink-400">Time</span>
                          <span className="font-bold text-ink-800 dark:text-ink-200">{asgn.time_limit_minutes}m</span>
                        </div>
                        <div>
                          <span className="block text-[10px] font-semibold text-ink-400">Points</span>
                          <span className="font-bold text-ink-800 dark:text-ink-200">{asgn.total_points}</span>
                        </div>
                      </div>

                      {asgn.due_date && (
                        <div className="flex items-center gap-1.5 text-xs text-amber-700 dark:text-amber-300 font-medium bg-amber-50/60 dark:bg-amber-950/30 px-2.5 py-1 rounded-lg">
                          <Clock size={13} className="shrink-0" />
                          <span>
                            Due:{' '}
                            {new Date(asgn.due_date).toLocaleDateString(undefined, {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="mt-5 pt-3.5 border-t border-ink-100 dark:border-ink-800">
                      {asgn.is_submitted ? (
                        <div className="flex items-center justify-between gap-2">
                          <div className="text-xs">
                            <span className="text-ink-500 dark:text-ink-400 block">Your Score:</span>
                            <span className="font-bold text-ink-900 dark:text-ink-100 text-sm">
                              {asgn.submission_score}/{asgn.total_points}{' '}
                              <span className="text-xs font-semibold text-brand-600 dark:text-brand-400">
                                ({asgn.submission_percentage}%)
                              </span>
                            </span>
                          </div>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleTakeAssessment(asgn)}
                          >
                            Retake
                          </Button>
                        </div>
                      ) : (
                        <Button
                          variant="primary"
                          size="sm"
                          className="w-full justify-center shadow-sm"
                          icon={Play}
                          onClick={() => handleTakeAssessment(asgn)}
                        >
                          Take Assessment
                        </Button>
                      )}
                    </div>
                  </Card>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* ============================================================ */}
      {/* TAB 2: Self-Study Quizzes (Practice mode on any material)    */}
      {/* ============================================================ */}
      {activeTab === 'practice' && (
        <div className="grid gap-5 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader
              title="Custom Practice Quiz"
              subtitle={
                isTopicFiltered
                  ? `Topic-specific practice mode: ${config.topic}`
                  : 'Choose any study material or topic to generate practice questions.'
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

            {practiceLoading ? (
              <LoadingSpinner label="Loading materials catalogue…" />
            ) : (
              <>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Select
                    label="Study Material"
                    options={materials.map((m) => ({ value: m.id, label: m.title }))}
                    value={config.materialId}
                    onChange={(e) =>
                      setConfig((c) => ({ ...c, materialId: e.target.value, topic: 'All topics' }))
                    }
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
                      { value: 'mixed', label: 'Mixed Difficulty' },
                      { value: 'easy', label: 'Easy' },
                      { value: 'medium', label: 'Medium' },
                      { value: 'hard', label: 'Hard' },
                    ]}
                    value={config.difficulty}
                    onChange={(e) => setConfig((c) => ({ ...c, difficulty: e.target.value }))}
                  />
                  <Select
                    label="Number of Questions"
                    options={[
                      { value: '5', label: '5 questions' },
                      { value: '8', label: '8 questions' },
                      { value: '10', label: '10 questions' },
                    ]}
                    value={String(config.count)}
                    onChange={(e) => setConfig((c) => ({ ...c, count: Number(e.target.value) }))}
                  />
                </div>

                <Button className="mt-6" icon={Play} onClick={startPractice}>
                  {isTopicFiltered ? `Start ${config.topic} Practice` : 'Start Practice Quiz'}
                </Button>
                <p className="muted mt-3 text-xs leading-relaxed">
                  {isTopicFiltered
                    ? `Questions will be generated specifically for "${config.topic}" at ${config.difficulty} difficulty.`
                    : 'Questions will be generated from your material notes and slides. Review weak concepts after finishing.'}
                </p>
              </>
            )}
          </Card>

          <Card>
            <CardHeader
              title="Previous Attempts"
              action={<History size={18} className="text-ink-400" />}
            />
            {displayAttempts.length === 0 ? (
              <EmptyState
                icon={History}
                title="No attempts yet"
                description="Your quiz scores and accuracy will appear here after your first quiz session."
              />
            ) : (
              <ul className="space-y-3">
                {displayAttempts.slice(0, 6).map((a) => (
                  <li
                    key={a.id}
                    className="rounded-xl border border-ink-200 p-3 dark:border-ink-800 transition-colors hover:border-brand-300 dark:hover:border-brand-800"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <p className="truncate text-sm font-semibold text-ink-900 dark:text-ink-100">
                        {a.materialTitle || a.topic}
                      </p>
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
                    <p className="muted mt-1 text-xs">
                      {a.topic} &middot; {a.score}/{a.total} &middot; {a.date}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      )}
    </>
  )
}

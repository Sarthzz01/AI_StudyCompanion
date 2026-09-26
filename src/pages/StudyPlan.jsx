import { useEffect, useState, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  CalendarClock,
  CheckCircle2,
  Clock,
  Sparkles,
  Layers,
  ClipboardCheck,
  Bot,
  FileText,
  RotateCw,
  AlertCircle,
  Brain,
  ArrowRight,
  TrendingUp,
  Calendar,
  Check,
} from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import Card, { CardHeader } from '../components/Card.jsx'
import StatCard from '../components/StatCard.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import Button from '../components/Button.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import ErrorState from '../components/ErrorState.jsx'
import EmptyState from '../components/EmptyState.jsx'
import { getStudyPlan, completeStudyPlanTask, getRevisions, getDueRevisions } from '../services/api.js'
import { useStudyData } from '../context/StudyDataContext.jsx'
import { formatMinutes } from '../utils/format.js'

const TIME_PRESETS = [30, 45, 60, 90, 120]

const activityConfig = {
  flashcards: { label: 'Flashcards', icon: Layers, tone: 'emerald', defaultUrl: '/flashcards' },
  quiz: { label: 'Quiz Practice', icon: ClipboardCheck, tone: 'brand', defaultUrl: '/quizzes' },
  tutor: { label: 'AI Tutor', icon: Bot, tone: 'purple', defaultUrl: '/tutor' },
  summary: { label: 'Summary Review', icon: FileText, tone: 'amber', defaultUrl: '/summaries' },
  reading: { label: 'Reading', icon: FileText, tone: 'sky', defaultUrl: '/materials' },
}

const priorityTones = {
  CRITICAL: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300 border-rose-200 dark:border-rose-800',
  HIGH: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300 border-amber-200 dark:border-amber-800',
  MEDIUM: 'bg-brand-100 text-brand-800 dark:bg-brand-900/40 dark:text-brand-300 border-brand-200 dark:border-brand-800',
  LOW: 'bg-ink-100 text-ink-700 dark:bg-ink-800 dark:text-ink-300 border-ink-200 dark:border-ink-700',
}

export default function StudyPlan() {
  const navigate = useNavigate()
  const { refreshProgress } = useStudyData()

  const [activeTab, setActiveTab] = useState('plan') // 'plan' | 'revisions'
  const [targetMinutes, setTargetMinutes] = useState(60)
  const [studyPlan, setStudyPlan] = useState(null)
  const [revisions, setRevisions] = useState([])
  const [dueRevisions, setDueRevisions] = useState([])
  const [loading, setLoading] = useState(true)
  const [completingTaskId, setCompletingTaskId] = useState(null)
  const [error, setError] = useState(null)

  const loadData = useCallback(async (minutes = targetMinutes, force = false) => {
    setLoading(true)
    setError(null)
    try {
      const [planData, revsData, dueData] = await Promise.all([
        getStudyPlan(minutes, force),
        getRevisions(),
        getDueRevisions(),
      ])
      setStudyPlan(planData)
      setRevisions(revsData || [])
      setDueRevisions(dueData?.revisions || [])
    } catch (err) {
      setError(err.message || 'Failed to load study plan.')
    } finally {
      setLoading(false)
    }
  }, [targetMinutes])

  useEffect(() => {
    loadData(targetMinutes)
  }, [loadData, targetMinutes])

  const handleBudgetChange = (mins) => {
    setTargetMinutes(mins)
    loadData(mins, true)
  }

  const handleToggleComplete = async (task) => {
    if (task.completed) return // Already completed
    setCompletingTaskId(task.id)
    try {
      await completeStudyPlanTask(task.id)
      // Optimistically update locally
      setStudyPlan((prev) => {
        if (!prev) return prev
        const updatedTasks = prev.tasks.map((t) =>
          t.id === task.id ? { ...t, completed: true, completed_at: new Date().toISOString() } : t
        )
        const completedMinutes = updatedTasks
          .filter((t) => t.completed)
          .reduce((sum, t) => sum + t.duration_minutes, 0)
        const completedTasks = updatedTasks.filter((t) => t.completed).length
        const completionRate =
          updatedTasks.length > 0 ? Math.round((completedTasks / updatedTasks.length) * 100) : 0

        return {
          ...prev,
          tasks: updatedTasks,
          completed_minutes: completedMinutes,
          completed_tasks: completedTasks,
          completion_rate: completionRate,
        }
      })
      refreshProgress?.()
    } catch (err) {
      console.error('Failed to complete task:', err)
    } finally {
      setCompletingTaskId(null)
    }
  }

  const tasks = studyPlan?.tasks || []
  const completedTasksCount = studyPlan?.completed_tasks || tasks.filter((t) => t.completed).length
  const totalTasksCount = studyPlan?.total_tasks || tasks.length
  const allocatedMinutes = studyPlan?.allocated_minutes || tasks.reduce((acc, t) => acc + t.duration_minutes, 0)
  const completedMinutes = studyPlan?.completed_minutes || tasks.filter((t) => t.completed).reduce((acc, t) => acc + t.duration_minutes, 0)
  const completionRate = studyPlan?.completion_rate || (totalTasksCount > 0 ? Math.round((completedTasksCount / totalTasksCount) * 100) : 0)

  return (
    <>
      <PageHeader
        title="Study Plan & Revision"
        subtitle="Spaced repetition and time-budgeted daily curriculum tailored to your retention."
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              icon={RotateCw}
              onClick={() => loadData(targetMinutes, true)}
              disabled={loading}
            >
              Regenerate Plan
            </Button>
          </div>
        }
      />

      {/* Tabs */}
      <div className="mb-6 flex border-b border-ink-200 dark:border-ink-800">
        <button
          onClick={() => setActiveTab('plan')}
          className={`flex items-center gap-2 border-b-2 px-5 py-3 text-sm font-semibold transition-colors ${
            activeTab === 'plan'
              ? 'border-brand-600 text-brand-600 dark:border-brand-400 dark:text-brand-300'
              : 'border-transparent text-ink-500 hover:text-ink-800 dark:hover:text-ink-200'
          }`}
        >
          <CalendarClock size={18} />
          Today’s Study Plan
          {tasks.length > 0 && (
            <span className="rounded-full bg-brand-100 px-2 py-0.5 text-xs text-brand-700 dark:bg-brand-900/60 dark:text-brand-300">
              {completedTasksCount}/{totalTasksCount}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('revisions')}
          className={`flex items-center gap-2 border-b-2 px-5 py-3 text-sm font-semibold transition-colors ${
            activeTab === 'revisions'
              ? 'border-brand-600 text-brand-600 dark:border-brand-400 dark:text-brand-300'
              : 'border-transparent text-ink-500 hover:text-ink-800 dark:hover:text-ink-200'
          }`}
        >
          <Brain size={18} />
          Spaced Revision Schedule (SM-2)
          {dueRevisions.length > 0 && (
            <span className="rounded-full bg-rose-100 px-2 py-0.5 text-xs font-semibold text-rose-700 dark:bg-rose-900/60 dark:text-rose-300">
              {dueRevisions.length} Due
            </span>
          )}
        </button>
      </div>

      {error ? (
        <ErrorState message={error} onRetry={() => loadData(targetMinutes)} />
      ) : loading ? (
        <LoadingSpinner label="Calculating optimal SM-2 study schedule..." />
      ) : activeTab === 'plan' ? (
        <div className="space-y-6">
          {/* Time Budget Selector & Summary Bar */}
          <Card>
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="text-sm font-semibold text-ink-900 dark:text-white">Daily Available Study Time</p>
                <p className="text-xs text-ink-500">Pick your available time budget today; the engine auto-allocates high-impact topics.</p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {TIME_PRESETS.map((mins) => (
                  <button
                    key={mins}
                    onClick={() => handleBudgetChange(mins)}
                    className={`rounded-xl px-3.5 py-1.5 text-sm font-semibold transition-all ${
                      targetMinutes === mins
                        ? 'bg-brand-600 text-white shadow-sm'
                        : 'border border-ink-200 bg-ink-50 text-ink-700 hover:bg-ink-100 dark:border-ink-700 dark:bg-ink-800 dark:text-ink-300 dark:hover:bg-ink-700'
                    }`}
                  >
                    {mins} min
                  </button>
                ))}
              </div>
            </div>
          </Card>

          {/* Stats Bar */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              icon={Clock}
              label="Allocated Study Time"
              value={`${allocatedMinutes} / ${targetMinutes} min`}
              tone="brand"
            />
            <StatCard
              icon={CheckCircle2}
              label="Completed Time"
              value={`${completedMinutes} min`}
              sublabel={`${completionRate}% of today’s plan`}
              tone="emerald"
            />
            <StatCard
              icon={CalendarClock}
              label="Tasks Completed"
              value={`${completedTasksCount} / ${totalTasksCount}`}
              tone="amber"
            />
            <StatCard
              icon={Brain}
              label="Due Spaced Revisions"
              value={`${studyPlan?.due_revisions_count || dueRevisions.length}`}
              sublabel={dueRevisions.length > 0 ? 'Prioritized in today’s plan' : 'All caught up!'}
              tone="sky"
            />
          </div>

          {/* AI Pedagogical Guidance */}
          {studyPlan?.ai_guidance && (
            <div className="flex items-start gap-3.5 rounded-2xl border border-brand-200 bg-brand-50/70 p-4.5 dark:border-brand-900/60 dark:bg-brand-950/40">
              <span className="rounded-xl bg-brand-600 p-2 text-white">
                <Sparkles size={18} />
              </span>
              <div className="flex-1">
                <p className="text-sm font-semibold text-brand-900 dark:text-brand-200">
                  AI Study Coach Insights
                </p>
                <p className="mt-1 text-sm text-brand-800 dark:text-brand-300 leading-relaxed">
                  {studyPlan.ai_guidance}
                </p>
              </div>
            </div>
          )}

          {/* Today's Tasks Checklist */}
          <Card>
            <CardHeader
              title="Today’s Structured Checklist"
              subtitle="Ordered by pedagogical urgency: Due spaced repetition → Weak topics → High-yield practice."
              action={
                <div className="flex items-center gap-3">
                  <div className="w-32 sm:w-44">
                    <ProgressBar value={completionRate} size="sm" />
                  </div>
                  <span className="text-xs font-semibold text-ink-600 dark:text-ink-400">{completionRate}%</span>
                </div>
              }
            />

            {tasks.length === 0 ? (
              <EmptyState
                icon={CalendarClock}
                title="No tasks scheduled"
                description="You're completely up to date! Generate practice quizzes or flashcards to populate your study queue."
                action={
                  <Button icon={ClipboardCheck} onClick={() => navigate('/quizzes')}>
                    Take a Quiz
                  </Button>
                }
              />
            ) : (
              <div className="space-y-3.5 divide-y divide-ink-100 dark:divide-ink-800/60">
                {tasks.map((task, idx) => {
                  const actInfo = activityConfig[task.activity] || {
                    label: task.activity,
                    icon: ClipboardCheck,
                    tone: 'brand',
                    defaultUrl: '/dashboard',
                  }
                  const ActIcon = actInfo.icon
                  const actionTarget = task.action_url || actInfo.defaultUrl

                  return (
                    <div
                      key={task.id || idx}
                      className={`flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-3.5 first:pt-0 transition-opacity ${
                        task.completed ? 'opacity-70' : 'opacity-100'
                      }`}
                    >
                      <div className="flex items-start gap-3.5">
                        {/* Checkbox */}
                        <button
                          onClick={() => handleToggleComplete(task)}
                          disabled={task.completed || completingTaskId === task.id}
                          className={`mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border transition-all ${
                            task.completed
                              ? 'border-emerald-600 bg-emerald-600 text-white'
                              : 'border-ink-300 hover:border-brand-500 hover:bg-brand-50 dark:border-ink-600 dark:hover:border-brand-400'
                          }`}
                          aria-label={task.completed ? 'Task completed' : 'Mark task completed'}
                        >
                          {task.completed ? <Check size={15} strokeWidth={3} /> : null}
                        </button>

                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span
                              className={`rounded-md border px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider ${
                                priorityTones[task.priority] || priorityTones.LOW
                              }`}
                            >
                              {task.priority}
                            </span>
                            <span className="flex items-center gap-1 text-xs font-semibold text-ink-500 dark:text-ink-400">
                              <ActIcon size={13} className="text-brand-600 dark:text-brand-400" />
                              {actInfo.label}
                            </span>
                            <span className="rounded bg-ink-100 px-1.5 py-0.5 text-[11px] font-medium text-ink-600 dark:bg-ink-800 dark:text-ink-400">
                              {task.duration_minutes} min
                            </span>
                          </div>

                          <p
                            className={`mt-1 text-sm font-semibold text-ink-900 dark:text-white ${
                              task.completed ? 'line-through text-ink-500 dark:text-ink-400' : ''
                            }`}
                          >
                            {task.task_title}
                          </p>
                          <p className="mt-0.5 text-xs text-ink-500 dark:text-ink-400">
                            {task.reason}
                          </p>
                        </div>
                      </div>

                      {/* Action Button */}
                      <div className="flex items-center gap-2 sm:self-center pl-9 sm:pl-0">
                        {task.completed ? (
                          <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                            <CheckCircle2 size={16} /> Completed
                          </span>
                        ) : (
                          <Link to={actionTarget}>
                            <Button size="sm" icon={ArrowRight}>
                              Start
                            </Button>
                          </Link>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </Card>
        </div>
      ) : (
        /* Spaced Revision Schedule (SM-2) */
        <div className="space-y-6">
          {/* Due Revisions Banner */}
          {dueRevisions.length > 0 ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50/80 p-5 dark:border-rose-900/60 dark:bg-rose-950/40">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <span className="rounded-xl bg-rose-600 p-2 text-white">
                    <AlertCircle size={20} />
                  </span>
                  <div>
                    <h3 className="text-base font-semibold text-rose-900 dark:text-rose-200">
                      {dueRevisions.length} Spaced {dueRevisions.length === 1 ? 'Revision is' : 'Revisions are'} Due Today
                    </h3>
                    <p className="text-xs text-rose-700 dark:text-rose-300">
                      Reviewing on schedule stabilizes your memory retention and prevents forgetting curve decay.
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    icon={Layers}
                    onClick={() => {
                      const firstDue = dueRevisions[0]
                      if (firstDue) {
                        navigate(
                          `/flashcards?${new URLSearchParams({
                            topic: firstDue.topic,
                            ...(firstDue.material_id ? { material: firstDue.material_id } : {}),
                          }).toString()}`
                        )
                      } else {
                        navigate('/flashcards')
                      }
                    }}
                  >
                    Review Due Flashcards
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50/80 p-4 text-sm text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-300 flex items-center gap-3">
              <CheckCircle2 size={18} className="text-emerald-600 dark:text-emerald-400" />
              <span>Great job! No spaced revisions are currently overdue. Keep learning new topics or practice anytime!</span>
            </div>
          )}

          {/* Full Schedule Table */}
          <Card>
            <CardHeader
              title="Spaced Repetition Mastery Matrix (SM-2)"
              subtitle="Calculates your topic interval multiplier, ease factor, and estimated recall retention."
            />

            {revisions.length === 0 ? (
              <EmptyState
                icon={Brain}
                title="No revision records yet"
                description="Complete quizzes or flashcard sets to generate spaced repetition intervals for your topics."
                action={
                  <Button icon={ClipboardCheck} onClick={() => navigate('/quizzes')}>
                    Take First Quiz
                  </Button>
                }
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-ink-200 text-xs font-semibold uppercase text-ink-500 dark:border-ink-800">
                      <th className="pb-3 pr-4">Topic</th>
                      <th className="pb-3 px-4">Stage</th>
                      <th className="pb-3 px-4">Interval</th>
                      <th className="pb-3 px-4">Ease Factor (EF)</th>
                      <th className="pb-3 px-4">Retention</th>
                      <th className="pb-3 px-4">Next Review</th>
                      <th className="pb-3 px-4">Status</th>
                      <th className="pb-3 pl-4 text-right">Practice</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-ink-100 dark:divide-ink-800/60">
                    {revisions.map((rev) => {
                      const nextDate = rev.next_review ? new Date(rev.next_review) : null
                      const isDue = rev.is_due
                      const formattedNext = nextDate
                        ? nextDate.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
                        : '—'

                      return (
                        <tr key={rev.id || rev.topic} className="hover:bg-ink-50/50 dark:hover:bg-ink-800/30 transition-colors">
                          <td className="py-3.5 pr-4 font-semibold text-ink-900 dark:text-white">
                            {rev.topic}
                          </td>
                          <td className="py-3.5 px-4 text-ink-600 dark:text-ink-400">
                            Rep {rev.repetition_count}
                          </td>
                          <td className="py-3.5 px-4 font-medium text-ink-700 dark:text-ink-300">
                            {rev.interval_days} {rev.interval_days === 1 ? 'day' : 'days'}
                          </td>
                          <td className="py-3.5 px-4 font-mono text-xs text-ink-600 dark:text-ink-400">
                            {rev.ease_factor.toFixed(2)}
                          </td>
                          <td className="py-3.5 px-4">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-semibold">{rev.retention_estimate}%</span>
                              <div className="w-16">
                                <ProgressBar value={rev.retention_estimate} size="sm" />
                              </div>
                            </div>
                          </td>
                          <td className="py-3.5 px-4 text-xs font-medium text-ink-600 dark:text-ink-400">
                            {formattedNext}
                          </td>
                          <td className="py-3.5 px-4">
                            {isDue ? (
                              <span className="rounded-full bg-rose-100 px-2 py-0.5 text-xs font-semibold text-rose-700 dark:bg-rose-900/40 dark:text-rose-300">
                                Due Now
                              </span>
                            ) : (
                              <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
                                Scheduled
                              </span>
                            )}
                          </td>
                          <td className="py-3.5 pl-4 text-right">
                            <div className="flex items-center justify-end gap-1.5">
                              <Link
                                to={`/flashcards?${new URLSearchParams({
                                  topic: rev.topic,
                                  ...(rev.material_id ? { material: rev.material_id } : {}),
                                }).toString()}`}
                                className="rounded-lg p-1.5 text-ink-500 hover:bg-ink-100 hover:text-brand-600 dark:hover:bg-ink-800"
                                title={`Practice Flashcards for ${rev.topic}`}
                              >
                                <Layers size={16} />
                              </Link>
                              <Link
                                to={`/quizzes?${new URLSearchParams({
                                  topic: rev.topic,
                                  ...(rev.material_id ? { material: rev.material_id } : {}),
                                  ...(rev.difficulty ? { difficulty: rev.difficulty } : {}),
                                }).toString()}`}
                                className="rounded-lg p-1.5 text-ink-500 hover:bg-ink-100 hover:text-brand-600 dark:hover:bg-ink-800"
                                title={`Take Quiz on ${rev.topic}`}
                              >
                                <ClipboardCheck size={16} />
                              </Link>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>
      )}
    </>
  )
}

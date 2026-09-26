import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Bot,
  FileText,
  Layers,
  ClipboardCheck,
  Target,
  Percent,
  ListChecks,
  Clock,
  CheckCircle2,
  CalendarClock,
  Mic,
  ArrowRight,
  Check,
  Flame,
  Sparkles,
  BookOpen,
} from 'lucide-react'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'
import Card, { CardHeader } from '../components/Card.jsx'
import StatCard from '../components/StatCard.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import RecommendationCard from '../components/RecommendationCard.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import ErrorState from '../components/ErrorState.jsx'
import Button from '../components/Button.jsx'
import { getMaterials, getTodayRecommendations, getStudyPlan, completeStudyPlanTask } from '../services/api.js'
import { useAuth } from '../context/AuthContext.jsx'
import { useStudyData } from '../context/StudyDataContext.jsx'
import { formatMinutes } from '../utils/format.js'

const interactiveTools = [
  {
    label: 'AI Tutor',
    desc: 'Ask any question with ChatGPT-level depth & citations',
    icon: Bot,
    to: '/tutor',
    badge: 'Popular',
    iconBg: 'bg-brand-50 text-brand-600 dark:bg-brand-950 dark:text-brand-300',
  },
  {
    label: 'AI Viva / Interview',
    desc: 'Interactive oral examination & concept defense',
    icon: Mic,
    to: '/viva',
    badge: 'Voice AI',
    iconBg: 'bg-purple-50 text-purple-600 dark:bg-purple-950 dark:text-purple-300',
  },
  {
    label: 'Spaced Flashcards',
    desc: 'Master key concepts with Leitner repetition',
    icon: Layers,
    to: '/flashcards',
    iconBg: 'bg-amber-50 text-amber-600 dark:bg-amber-950 dark:text-amber-300',
  },
  {
    label: 'Adaptive Quizzes',
    desc: 'AI-generated test questions with instant feedback',
    icon: ClipboardCheck,
    to: '/quizzes',
    iconBg: 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950 dark:text-emerald-300',
  },
  {
    label: 'Daily Study Plan',
    desc: 'Time-budgeted spaced repetition queue',
    icon: CalendarClock,
    to: '/study-plan',
    iconBg: 'bg-sky-50 text-sky-600 dark:bg-sky-950 dark:text-sky-300',
  },
  {
    label: 'Study Notes & PDF',
    desc: 'Structured revision notes with instant PDF export',
    icon: BookOpen,
    to: '/notes',
    badge: 'Export',
    iconBg: 'bg-rose-50 text-rose-600 dark:bg-rose-950 dark:text-rose-300',
  },
  {
    label: 'Document Summaries',
    desc: 'Instant structured notes & key takeaways',
    icon: FileText,
    to: '/summaries',
    iconBg: 'bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300',
  },
]

export default function Dashboard() {
  const { user } = useAuth()
  const { progress, goals, refreshProgress } = useStudyData()
  const navigate = useNavigate()

  const [materials, setMaterials] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [studyPlan, setStudyPlan] = useState(null)
  const [dailyTip, setDailyTip] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const [m, todayData, planData] = await Promise.all([
        getMaterials(),
        getTodayRecommendations(),
        getStudyPlan(60),
      ])
      setMaterials(m.slice(0, 3))
      setStudyPlan(planData)
      if (todayData && todayData.recommendations) {
        setRecommendations(todayData.recommendations.slice(0, 3))
        setDailyTip(todayData.ai_study_tip || null)
      } else if (Array.isArray(todayData)) {
        setRecommendations(todayData.slice(0, 3))
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const handleTaskToggle = async (task) => {
    if (task.completed) return
    try {
      await completeStudyPlanTask(task.id)
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
    }
  }

  const dailyGoal = (goals || []).find((g) => g.type === 'daily') || (goals || [])[0]
  const stats = progress?.stats || {
    accuracy: 85,
    questionsAttempted: 42,
    studyMinutes: 120,
    topicsCompleted: 6,
    totalTopics: 10,
    overallProgress: 60,
  }

  return (
    <div className="space-y-5">
      {/* Balanced, well-proportioned Hero Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-brand-700 via-indigo-600 to-purple-700 p-5 text-white shadow-md">
        <div className="relative z-10 flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
          <div className="max-w-xl">
            <div className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-2.5 py-0.5 text-[11px] font-semibold backdrop-blur-md">
              <Sparkles size={12} className="text-amber-300" />
              <span>Smart Study Assistant Active</span>
            </div>
            <h1 className="mt-2 font-display text-xl sm:text-2xl font-bold tracking-tight text-white">
              Welcome back, {user?.name?.split(' ')[0] || 'Scholar'}!
            </h1>
            <p className="mt-1 text-xs sm:text-sm text-indigo-100/90 leading-relaxed">
              Your personalized learning companion is ready. Practice with your AI Tutor, test your knowledge with quizzes, or review your study plan.
            </p>

            <div className="mt-4 flex flex-wrap items-center gap-2.5">
              <Button
                variant="gradient"
                size="sm"
                icon={Bot}
                onClick={() => navigate('/tutor')}
                className="bg-white text-brand-900 hover:bg-white/90 shadow-sm"
              >
                Ask AI Tutor
              </Button>
              <Button
                variant="secondary"
                size="sm"
                icon={ClipboardCheck}
                onClick={() => navigate('/quizzes')}
                className="bg-white/10 text-white border-white/20 hover:bg-white/20"
              >
                Quick Quiz
              </Button>
            </div>
          </div>

          {/* Quick Stats Badges: Compact & Balanced */}
          <div className="flex flex-row sm:flex-col gap-2.5 shrink-0">
            <div className="flex items-center gap-2.5 rounded-xl bg-white/10 p-2.5 px-3 backdrop-blur-md border border-white/15 min-w-[140px]">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-400 text-amber-950 shadow-xs">
                <Flame size={16} />
              </span>
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-indigo-200">Streak</p>
                <p className="font-display text-sm font-bold">5 Days Active</p>
              </div>
            </div>

            <div className="flex items-center gap-2.5 rounded-xl bg-white/10 p-2.5 px-3 backdrop-blur-md border border-white/15 min-w-[140px]">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-400 text-emerald-950 shadow-xs">
                <CheckCircle2 size={16} />
              </span>
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-indigo-200">Daily Mastery</p>
                <p className="font-display text-sm font-bold">{stats.accuracy}% Avg</p>
              </div>
            </div>
          </div>
        </div>

        {/* Ambient background decoration */}
        <div className="pointer-events-none absolute -right-6 -top-6 h-48 w-48 rounded-full bg-white/5 blur-2xl" />
      </div>

      {error ? (
        <ErrorState message={error} onRetry={load} />
      ) : (
        <div className="grid gap-5 lg:grid-cols-3">
          {/* Interactive Learning Hub: Proportioned & Aligned Grid */}
          <div className="lg:col-span-3">
            <div className="mb-2.5 flex items-center justify-between">
              <div>
                <h2 className="font-display text-base font-bold tracking-tight text-ink-900 dark:text-white flex items-center gap-2">
                  <Sparkles size={16} className="text-brand-600" />
                  Interactive Learning Hub
                </h2>
                <p className="text-xs text-ink-500 dark:text-ink-400">
                  Select a study tool to start your session
                </p>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {interactiveTools.map((tool) => {
                const Icon = tool.icon
                return (
                  <Link
                    key={tool.label}
                    to={tool.to}
                    className="group relative flex flex-col justify-between rounded-xl border border-ink-200/90 bg-white p-3.5 shadow-xs transition-all duration-150 hover:-translate-y-0.5 hover:border-brand-400/80 hover:shadow-sm dark:border-ink-800/80 dark:bg-ink-900/90"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span
                          className={`flex h-8 w-8 items-center justify-center rounded-lg transition-transform duration-150 group-hover:scale-105 ${tool.iconBg}`}
                        >
                          <Icon size={16} />
                        </span>
                        {tool.badge && (
                          <span className="rounded-full bg-brand-50 px-2 py-0.5 text-[9px] font-bold text-brand-700 dark:bg-brand-950 dark:text-brand-300 border border-brand-200/50">
                            {tool.badge}
                          </span>
                        )}
                      </div>

                      <h3 className="mt-2.5 font-display text-sm font-bold text-ink-900 group-hover:text-brand-600 transition-colors dark:text-white dark:group-hover:text-brand-400">
                        {tool.label}
                      </h3>
                      <p className="mt-0.5 text-xs text-ink-500 line-clamp-1 dark:text-ink-400">
                        {tool.desc}
                      </p>
                    </div>

                    <div className="mt-3 flex items-center gap-1 border-t border-ink-100/80 pt-2 text-xs font-semibold text-brand-600 dark:border-ink-800/60 dark:text-brand-400">
                      <span>Launch</span>
                      <ArrowRight size={12} className="transition-transform group-hover:translate-x-0.5" />
                    </div>
                  </Link>
                )
              })}
            </div>
          </div>

          {/* Today's Adaptive Schedule */}
          <Card className="lg:col-span-3 p-4 sm:p-5">
            <CardHeader
              title="Today’s Adaptive Schedule"
              subtitle="Personalized, time-budgeted tasks based on spaced repetition & mastery"
              action={
                <Link to="/study-plan" className="text-xs font-semibold text-brand-600 hover:underline dark:text-brand-400 flex items-center gap-1">
                  Full schedule <ArrowRight size={12} />
                </Link>
              }
            />
            {loading ? (
              <LoadingSpinner label="Loading daily schedule…" />
            ) : !studyPlan || !studyPlan.tasks || studyPlan.tasks.length === 0 ? (
              <p className="muted text-xs py-3">No tasks scheduled for today. Complete quizzes or flashcards to populate your study queue.</p>
            ) : (
              <div className="space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-ink-50/70 p-3 dark:bg-ink-950/60">
                  <div className="flex items-center gap-2.5 text-xs text-ink-600 dark:text-ink-400">
                    <span>
                      <strong className="text-ink-900 dark:text-white">Budget:</strong> {studyPlan.allocated_minutes} / {studyPlan.target_minutes} min
                    </span>
                    <span>•</span>
                    <span>
                      <strong className="text-ink-900 dark:text-white">Completed:</strong> {studyPlan.completed_minutes} min ({studyPlan.completion_rate}%)
                    </span>
                  </div>
                  <div className="w-32">
                    <ProgressBar value={studyPlan.completion_rate} size="sm" />
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {studyPlan.tasks.slice(0, 3).map((task) => (
                    <div
                      key={task.id}
                      className={`flex flex-col justify-between rounded-xl border p-3.5 transition-all ${
                        task.completed
                          ? 'border-emerald-200 bg-emerald-50/40 dark:border-emerald-900/40 dark:bg-emerald-950/20 opacity-80'
                          : 'border-ink-200 bg-white hover:border-brand-300 dark:border-ink-800 dark:bg-ink-900'
                      }`}
                    >
                      <div>
                        <div className="flex items-center justify-between gap-2">
                          <span className="rounded-md bg-brand-50 px-2 py-0.5 text-[10px] font-bold uppercase text-brand-700 dark:bg-brand-950 dark:text-brand-300">
                            {task.activity}
                          </span>
                          <span className="text-xs font-semibold text-ink-500">{task.duration_minutes} min</span>
                        </div>
                        <p className={`mt-2 text-xs sm:text-sm font-bold text-ink-900 dark:text-white ${task.completed ? 'line-through text-ink-400' : ''}`}>
                          {task.task_title}
                        </p>
                        <p className="mt-1 text-xs text-ink-500 line-clamp-2 leading-relaxed">{task.reason}</p>
                      </div>

                      <div className="mt-3 flex items-center justify-between border-t border-ink-100 pt-2.5 dark:border-ink-800/60">
                        <button
                          onClick={() => handleTaskToggle(task)}
                          disabled={task.completed}
                          className={`flex items-center gap-1.5 text-xs font-bold transition ${
                            task.completed
                              ? 'text-emerald-600 dark:text-emerald-400'
                              : 'text-ink-600 hover:text-brand-600 dark:text-ink-400'
                          }`}
                        >
                          {task.completed ? (
                            <>
                              <Check size={13} className="text-emerald-500" /> Done
                            </>
                          ) : (
                            'Mark Done'
                          )}
                        </button>

                        {!task.completed && (
                          <Link
                            to={task.action_url || '/dashboard'}
                            className="flex items-center gap-1 text-xs font-semibold text-brand-600 hover:underline dark:text-brand-400"
                          >
                            Start <ArrowRight size={12} />
                          </Link>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>

          {/* Performance Area Chart */}
          <Card className="lg:col-span-2 p-4 sm:p-5">
            <CardHeader
              title="Accuracy & Mastery Trend"
              subtitle="Performance trajectory across quiz attempts and viva evaluations"
            />
            <div className="flex items-baseline gap-2">
              <p className="font-display text-2xl sm:text-3xl font-extrabold text-ink-900 dark:text-white">
                {stats.overallProgress}%
              </p>
              <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                +8% this week
              </span>
            </div>
            <div className="mt-2.5">
              <ProgressBar value={stats.overallProgress} />
            </div>
            <p className="muted mt-1.5 text-xs">
              {stats.topicsCompleted} of {stats.totalTopics} curriculum topics mastered.
            </p>

            <div className="mt-4 h-48">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={progress?.performanceOverTime || [
                    { date: 'Mon', accuracy: 70 },
                    { date: 'Tue', accuracy: 75 },
                    { date: 'Wed', accuracy: 82 },
                    { date: 'Thu', accuracy: 80 },
                    { date: 'Fri', accuracy: 88 },
                    { date: 'Sat', accuracy: 85 },
                  ]}
                  margin={{ top: 5, right: 8, left: -20, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="accuracyGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#94a3b8" tickLine={false} axisLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} stroke="#94a3b8" tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderRadius: '0.5rem',
                      border: 'none',
                      color: '#fff',
                      fontSize: '11px',
                    }}
                    formatter={(v) => [`${v}%`, 'Accuracy']}
                  />
                  <Area
                    type="monotone"
                    dataKey="accuracy"
                    stroke="#4f46e5"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#accuracyGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Today's Goal Card */}
          <Card className="p-4 sm:p-5">
            <CardHeader
              title="Daily Goal"
              action={
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-950 dark:text-brand-400">
                  <Target size={16} />
                </span>
              }
            />
            {dailyGoal ? (
              <div className="space-y-3">
                <div>
                  <p className="text-sm font-bold text-ink-900 dark:text-white">{dailyGoal.title}</p>
                  <p className="muted mt-1 text-xs">
                    {dailyGoal.current} of {dailyGoal.target} {dailyGoal.unit} completed
                  </p>
                </div>
                <div className="mt-2">
                  <ProgressBar value={(dailyGoal.current / dailyGoal.target) * 100} showValue />
                </div>
              </div>
            ) : (
              <p className="muted text-xs">No specific goal set for today.</p>
            )}
            <Link to="/goals" className="mt-4 block">
              <Button variant="secondary" size="sm" className="w-full">
                Manage Study Goals
              </Button>
            </Link>
          </Card>

          {/* Continue Learning Materials */}
          <Card className="lg:col-span-2 p-4 sm:p-5">
            <CardHeader
              title="Continue Learning"
              action={
                <Link to="/materials" className="text-xs font-semibold text-brand-600 hover:underline dark:text-brand-400">
                  View library →
                </Link>
              }
            />
            {loading ? (
              <LoadingSpinner label="Loading your materials…" />
            ) : materials.length === 0 ? (
              <p className="muted text-xs py-3">No materials uploaded yet.</p>
            ) : (
              <div className="space-y-2.5">
                {materials.map((m) => (
                  <Link
                    key={m.id}
                    to={`/materials/${m.id}`}
                    className="group flex items-center gap-3.5 rounded-xl border border-ink-200/90 p-3 transition-all hover:border-brand-300 hover:bg-brand-50/20 dark:border-ink-800/80 dark:hover:bg-ink-800/50"
                  >
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600 transition-transform group-hover:scale-105 dark:bg-brand-950 dark:text-brand-300">
                      <FileText size={16} />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-xs sm:text-sm font-bold text-ink-900 group-hover:text-brand-600 dark:text-white dark:group-hover:text-brand-300">
                        {m.title}
                      </p>
                      <p className="muted text-[11px]">Last studied {m.lastStudied?.toLowerCase() || 'recently'}</p>
                      <div className="mt-1.5">
                        <ProgressBar value={m.progress || 0} size="sm" />
                      </div>
                    </div>
                    <span className="text-xs font-bold text-ink-600 dark:text-ink-400">
                      {m.progress || 0}%
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </Card>

          {/* AI Focus Coach */}
          <Card className="p-4 sm:p-5">
            <CardHeader title="AI Focus Coach" subtitle="Smart personalized priorities" />
            {loading ? (
              <LoadingSpinner label="Analyzing learner model…" />
            ) : (
              <div className="space-y-2.5">
                {dailyTip && (
                  <div className="rounded-xl border border-brand-200/80 bg-gradient-to-br from-brand-50/80 to-indigo-50/50 p-3 text-xs text-brand-900 shadow-2xs dark:border-brand-900/60 dark:bg-brand-950/40 dark:text-brand-200">
                    <p className="font-bold flex items-center gap-1.5">
                      <Sparkles size={12} className="text-brand-600" />
                      Daily Insight
                    </p>
                    <p className="mt-1 leading-relaxed text-ink-700 dark:text-brand-200">{dailyTip}</p>
                  </div>
                )}
                {recommendations.length === 0 ? (
                  <p className="muted text-xs">Practice quizzes or flashcards to generate adaptive recommendations.</p>
                ) : (
                  recommendations.map((r) => (
                    <RecommendationCard key={r.id || r.topic} recommendation={r} />
                  ))
                )}
              </div>
            )}
          </Card>

          {/* Key Metrics Overview */}
          <div className="grid gap-3.5 sm:grid-cols-2 lg:col-span-3 lg:grid-cols-4">
            <StatCard
              icon={Percent}
              label="Accuracy"
              value={`${stats.accuracy}%`}
              tone="brand"
              trend="+4% this week"
            />
            <StatCard
              icon={ListChecks}
              label="Questions Done"
              value={stats.questionsAttempted}
              tone="emerald"
              trend="Target on track"
            />
            <StatCard
              icon={Clock}
              label="Study Time"
              value={formatMinutes(stats.studyMinutes)}
              tone="amber"
              sublabel="Active learning sessions"
            />
            <StatCard
              icon={CheckCircle2}
              label="Topics Mastered"
              value={`${stats.topicsCompleted}/${stats.totalTopics}`}
              tone="purple"
              sublabel="Curriculum coverage"
            />
          </div>
        </div>
      )}
    </div>
  )
}

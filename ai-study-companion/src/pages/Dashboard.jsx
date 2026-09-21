import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Bot,
  Upload,
  FileText,
  Layers,
  ClipboardCheck,
  Target,
  Percent,
  ListChecks,
  Clock,
  CheckCircle2,
} from 'lucide-react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'
import PageHeader from '../components/PageHeader.jsx'
import Card, { CardHeader } from '../components/Card.jsx'
import StatCard from '../components/StatCard.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import RecommendationCard from '../components/RecommendationCard.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import ErrorState from '../components/ErrorState.jsx'
import Button from '../components/Button.jsx'
import { getMaterials, getTodayRecommendations } from '../services/api.js'
import { useAuth } from '../context/AuthContext.jsx'
import { useStudyData } from '../context/StudyDataContext.jsx'
import { formatMinutes } from '../utils/format.js'

const quickActions = [
  { label: 'Ask AI Tutor', icon: Bot, to: '/tutor' },
  { label: 'Upload material', icon: Upload, to: '/materials?upload=1' },
  { label: 'Generate summary', icon: FileText, to: '/summaries' },
  { label: 'Flashcards', icon: Layers, to: '/flashcards' },
  { label: 'Take a quiz', icon: ClipboardCheck, to: '/quizzes' },
]

export default function Dashboard() {
  const { user } = useAuth()
  const { progress, goals } = useStudyData()
  const navigate = useNavigate()

  const [materials, setMaterials] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [dailyTip, setDailyTip] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const [m, todayData] = await Promise.all([getMaterials(), getTodayRecommendations()])
      setMaterials(m.slice(0, 3))
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

  const dailyGoal = (goals || []).find((g) => g.type === 'daily') || (goals || [])[0]
  const stats = progress?.stats || {
    accuracy: 0,
    questionsAttempted: 0,
    studyMinutes: 0,
    topicsCompleted: 0,
    totalTopics: 0,
    overallProgress: 0,
  }

  return (
    <>
      <PageHeader
        title={`Welcome back, ${user?.name?.split(' ')[0] || 'student'}`}
        subtitle="Here is where your studying stands today."
        actions={
          <Button icon={ClipboardCheck} onClick={() => navigate('/quizzes')}>
            Take a quiz
          </Button>
        }
      />

      {error ? (
        <ErrorState message={error} onRetry={load} />
      ) : (
        <div className="grid gap-5 lg:grid-cols-3">
          {/* Overall progress */}
          <Card className="lg:col-span-2">
            <CardHeader title="Overall progress" subtitle="Across every material in your library" />
            <p className="font-display text-4xl font-semibold">{stats.overallProgress}%</p>
            <div className="mt-4">
              <ProgressBar value={stats.overallProgress} />
            </div>
            <p className="muted mt-3">
              {stats.topicsCompleted} of {stats.totalTopics} topics completed.
            </p>

            <div className="mt-6 h-56">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={progress?.performanceOverTime || []} margin={{ top: 5, right: 8, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#94a3b8" tickLine={false} axisLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} stroke="#94a3b8" tickLine={false} axisLine={false} />
                  <Tooltip formatter={(v) => [`${v}%`, 'Accuracy']} />
                  <Line type="monotone" dataKey="accuracy" stroke="#4f46e5" strokeWidth={2.5} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Today's goal */}
          <Card>
            <CardHeader title="Today’s goal" action={<Target size={18} className="text-brand-600" />} />
            {dailyGoal ? (
              <>
                <p className="text-base font-semibold">{dailyGoal.title}</p>
                <p className="muted mt-1">
                  {dailyGoal.current} of {dailyGoal.target} {dailyGoal.unit}
                </p>
                <div className="mt-4">
                  <ProgressBar value={(dailyGoal.current / dailyGoal.target) * 100} showValue />
                </div>
              </>
            ) : (
              <p className="muted">No goal set for today.</p>
            )}
            <Link to="/goals" className="mt-5 block">
              <Button variant="secondary" className="w-full">
                Manage goals
              </Button>
            </Link>
          </Card>

          {/* Quick actions */}
          <Card className="lg:col-span-3">
            <CardHeader title="Quick actions" />
            <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-5">
              {quickActions.map(({ label, icon: Icon, to }) => (
                <Link
                  key={label}
                  to={to}
                  className="flex flex-col items-center gap-2 rounded-xl border border-ink-200 px-3 py-5 text-center text-sm font-medium transition-colors hover:border-brand-300 hover:bg-brand-50 dark:border-ink-800 dark:hover:bg-brand-950/40"
                >
                  <Icon size={20} className="text-brand-600 dark:text-brand-300" />
                  {label}
                </Link>
              ))}
            </div>
          </Card>

          {/* Continue learning */}
          <Card className="lg:col-span-2">
            <CardHeader
              title="Continue learning"
              action={
                <Link to="/materials" className="text-sm font-medium text-brand-600 dark:text-brand-400">
                  All materials
                </Link>
              }
            />
            {loading ? (
              <LoadingSpinner label="Loading your materials…" />
            ) : (
              <div className="space-y-3">
                {materials.map((m) => (
                  <Link
                    key={m.id}
                    to={`/materials/${m.id}`}
                    className="flex items-center gap-4 rounded-xl border border-ink-200 p-4 transition-colors hover:bg-ink-50 dark:border-ink-800 dark:hover:bg-ink-800/50"
                  >
                    <span className="rounded-lg bg-brand-50 p-2 text-brand-600 dark:bg-brand-900/40 dark:text-brand-300">
                      <FileText size={16} />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold">{m.title}</p>
                      <p className="muted">Last studied {m.lastStudied.toLowerCase()}</p>
                      <div className="mt-2">
                        <ProgressBar value={m.progress} size="sm" />
                      </div>
                    </div>
                    <span className="text-sm font-semibold text-ink-500">{m.progress}%</span>
                  </Link>
                ))}
              </div>
            )}
          </Card>

          {/* Recommendations */}
          <Card>
            <CardHeader title="AI recommendations" subtitle="Personalized study priorities" />
            {loading ? (
              <LoadingSpinner label="Analyzing learner model…" />
            ) : (
              <div className="space-y-3">
                {dailyTip && (
                  <div className="rounded-xl border border-brand-100 bg-brand-50/60 p-3 text-xs text-brand-800 dark:border-brand-900/50 dark:bg-brand-950/30 dark:text-brand-300">
                    <p className="font-semibold text-brand-900 dark:text-brand-200">Daily Focus Coach:</p>
                    <p className="mt-0.5">{dailyTip}</p>
                  </div>
                )}
                {recommendations.length === 0 ? (
                  <p className="muted text-sm">Practice quizzes or flashcards to generate adaptive recommendations.</p>
                ) : (
                  recommendations.map((r) => (
                    <RecommendationCard key={r.id || r.topic} recommendation={r} />
                  ))
                )}
              </div>
            )}
          </Card>

          {/* Performance overview */}
          <div className="grid gap-5 sm:grid-cols-2 lg:col-span-3 lg:grid-cols-4">
            <StatCard icon={Percent} label="Accuracy" value={`${stats.accuracy}%`} tone="brand" />
            <StatCard icon={ListChecks} label="Questions attempted" value={stats.questionsAttempted} tone="emerald" />
            <StatCard icon={Clock} label="Study time" value={formatMinutes(stats.studyMinutes)} tone="amber" />
            <StatCard
              icon={CheckCircle2}
              label="Topics completed"
              value={`${stats.topicsCompleted}/${stats.totalTopics}`}
              tone="sky"
            />
          </div>
        </div>
      )}
    </>
  )
}

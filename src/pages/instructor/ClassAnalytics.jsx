import { useEffect, useState } from 'react'
import {
  BarChart3,
  TrendingUp,
  Award,
  Users,
  AlertTriangle,
  BookOpen,
  Mic,
  Clock,
  CheckCircle2,
  Layers,
  ArrowUpRight,
  PieChart
} from 'lucide-react'
import PageHeader from '../../components/PageHeader.jsx'
import Card, { CardHeader } from '../../components/Card.jsx'
import StatCard from '../../components/StatCard.jsx'
import ProgressBar from '../../components/ProgressBar.jsx'
import LoadingSpinner from '../../components/LoadingSpinner.jsx'
import ErrorState from '../../components/ErrorState.jsx'
import { getClassAnalyticsOverview } from '../../services/api.js'

export default function ClassAnalytics() {
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await getClassAnalyticsOverview()
        setAnalytics(data)
      } catch (err) {
        setError(err.message || 'Failed to load class analytics.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <LoadingSpinner size={32} label="Computing real-time class analytics telemetry..." />
      </div>
    )
  }

  if (error) {
    return <ErrorState message={error} onRetry={() => window.location.reload()} />
  }

  return (
    <div className="space-y-8 pb-12">
      {/* Page Header */}
      <PageHeader
        title="Class-Wide Learning Analytics"
        subtitle="Aggregate telemetry across syllabus topics, score distributions, and conceptual bottleneck detection."
      />

      {/* Top Level Metric KPIs */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={Award}
          label="Class Average Mastery"
          value={`${analytics.average_class_mastery}%`}
          hint="Calculated across all student topics"
          trend="up"
        />
        <StatCard
          icon={Users}
          label="Total Cohort Size"
          value={analytics.total_students}
          hint={`${analytics.active_students_7d} active in last 7 days`}
        />
        <StatCard
          icon={Clock}
          label="Total Study Time"
          value={`${analytics.total_study_hours} hrs`}
          hint="Cumulative learning hours logged"
        />
        <StatCard
          icon={AlertTriangle}
          label="At-Risk Retention"
          value={analytics.at_risk_students_count}
          hint={`${analytics.excelling_students_count} excelling scholars`}
          trend="neutral"
        />
      </div>

      {/* Score Distribution & Activity Engagement */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Score Distribution Bars */}
        <Card className="lg:col-span-2">
          <CardHeader
            title="Assessment Score Distribution"
            subtitle="Student score dispersion on completed curriculum assessments."
          />
          <div className="mt-4 space-y-3">
            {Object.entries(analytics.score_distribution || {}).map(([bracket, count]) => {
              const totalSubs = analytics.total_submissions_received || 1
              const pct = Math.round((count / totalSubs) * 100)
              return (
                <div key={bracket} className="space-y-1 text-xs">
                  <div className="flex justify-between font-medium text-ink-700 dark:text-ink-300">
                    <span>{bracket}% Bracket</span>
                    <span>
                      <strong className="text-ink-900 dark:text-ink-100">{count} submissions</strong> ({pct}%)
                    </span>
                  </div>
                  <ProgressBar value={pct} tone={bracket.includes('90') || bracket.includes('80') ? 'emerald' : bracket.includes('70') ? 'brand' : 'amber'} />
                </div>
              )
            })}
          </div>
        </Card>

        {/* Engagement Aggregates */}
        <Card>
          <CardHeader
            title="Cohort Activity Telemetry"
            subtitle="Interaction volume across study modalities."
          />
          <div className="mt-4 space-y-4">
            <div className="flex items-center justify-between rounded-xl bg-ink-50 p-3 text-xs dark:bg-ink-800/50">
              <div className="flex items-center gap-2.5">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-100 text-brand-700 dark:bg-brand-900 dark:text-brand-300">
                  <BookOpen size={16} />
                </span>
                <div>
                  <span className="font-bold block text-ink-900 dark:text-ink-100">Quizzes Completed</span>
                  <span className="text-[10px] text-ink-400">Class aggregate attempts</span>
                </div>
              </div>
              <span className="text-base font-bold text-ink-900 dark:text-ink-100">
                {analytics.class_quizzes_completed}
              </span>
            </div>

            <div className="flex items-center justify-between rounded-xl bg-ink-50 p-3 text-xs dark:bg-ink-800/50">
              <div className="flex items-center gap-2.5">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300">
                  <Mic size={16} />
                </span>
                <div>
                  <span className="font-bold block text-ink-900 dark:text-ink-100">AI Viva Examinations</span>
                  <span className="text-[10px] text-ink-400">Oral examinations taken</span>
                </div>
              </div>
              <span className="text-base font-bold text-ink-900 dark:text-ink-100">
                {analytics.class_vivas_completed}
              </span>
            </div>

            <div className="flex items-center justify-between rounded-xl bg-ink-50 p-3 text-xs dark:bg-ink-800/50">
              <div className="flex items-center gap-2.5">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300">
                  <Award size={16} />
                </span>
                <div>
                  <span className="font-bold block text-ink-900 dark:text-ink-100">Avg Assessment Score</span>
                  <span className="text-[10px] text-ink-400">Published exams</span>
                </div>
              </div>
              <span className="text-base font-bold text-ink-900 dark:text-ink-100">
                {analytics.average_assessment_score}%
              </span>
            </div>
          </div>
        </Card>
      </div>

      {/* Topic Mastery & Bottlenecks Table */}
      <Card>
        <CardHeader
          title="Syllabus Topic Performance & Misconception Breakdown"
          subtitle="Ranked by average class mastery to highlight concepts requiring instructional reinforcement."
        />

        <div className="overflow-x-auto mt-4">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-ink-200 text-ink-400 dark:border-ink-800 font-semibold">
                <th className="pb-3">Syllabus Topic</th>
                <th className="pb-3">Average Mastery</th>
                <th className="pb-3">Mastered / At-Risk</th>
                <th className="pb-3">Quiz Accuracy</th>
                <th className="pb-3">Viva Score</th>
                <th className="pb-3">Pedagogical Observation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-100 dark:divide-ink-800/50">
              {analytics.topic_distribution?.map((t, idx) => (
                <tr key={idx} className="hover:bg-ink-50/50 dark:hover:bg-ink-800/30">
                  <td className="py-3 font-semibold text-ink-900 dark:text-ink-100">
                    {t.topic}
                  </td>
                  <td className="py-3">
                    <div className="w-28 space-y-1">
                      <div className="flex justify-between font-bold text-ink-900 dark:text-ink-100">
                        <span>{t.average_mastery}%</span>
                      </div>
                      <ProgressBar value={t.average_mastery} />
                    </div>
                  </td>
                  <td className="py-3">
                    <span className="font-bold text-emerald-600 dark:text-emerald-400">{t.mastered_count}</span>
                    <span className="text-ink-400"> / </span>
                    <span className="font-bold text-rose-600 dark:text-rose-400">{t.at_risk_count}</span>
                  </td>
                  <td className="py-3 text-ink-700 dark:text-ink-300 font-medium">
                    {t.average_quiz_accuracy}%
                  </td>
                  <td className="py-3 text-ink-700 dark:text-ink-300 font-medium">
                    {t.average_viva_score}%
                  </td>
                  <td className="py-3 text-ink-500 dark:text-ink-400 max-w-xs leading-relaxed">
                    {t.common_weakness_summary}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}

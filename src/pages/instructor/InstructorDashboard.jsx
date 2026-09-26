import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Users,
  Award,
  BookOpenCheck,
  AlertTriangle,
  Sparkles,
  TrendingUp,
  FileText,
  MessageSquareQuote,
  ArrowRight,
  CheckCircle2,
  XCircle,
  Clock,
  PlusCircle,
  BarChart3
} from 'lucide-react'
import PageHeader from '../../components/PageHeader.jsx'
import Card, { CardHeader } from '../../components/Card.jsx'
import StatCard from '../../components/StatCard.jsx'
import ProgressBar from '../../components/ProgressBar.jsx'
import Button from '../../components/Button.jsx'
import LoadingSpinner from '../../components/LoadingSpinner.jsx'
import ErrorState from '../../components/ErrorState.jsx'
import { getInstructorDashboard } from '../../services/api.js'

export default function InstructorDashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const res = await getInstructorDashboard()
        setData(res)
      } catch (err) {
        setError(err.message || 'Failed to load instructor dashboard data.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <LoadingSpinner size={32} label="Loading instructor dashboard..." />
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
        title="Instructor Command Center"
        subtitle="Monitor student cohort performance, manage assessments, review topic mastery, and dispatch targeted guidance."
        actions={
          <div className="flex items-center gap-3">
            <Link to="/instructor/assessments/create">
              <Button variant="primary" size="sm">
                <Sparkles size={16} />
                Create Assessment (AI)
              </Button>
            </Link>
            <Link to="/instructor/reports">
              <Button variant="outline" size="sm">
                <FileText size={16} />
                Class Report
              </Button>
            </Link>
          </div>
        }
      />

      {/* Top Key Metrics */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={Users}
          label="Enrolled Students"
          value={data.total_students}
          hint="Active academic cohort"
        />
        <StatCard
          icon={Award}
          label="Class Average Mastery"
          value={`${data.average_class_mastery}%`}
          hint="Weighted across all topics"
          trend="up"
        />
        <StatCard
          icon={BookOpenCheck}
          label="Active Assessments"
          value={data.total_assessments}
          hint={`${data.total_submissions} total submissions`}
        />
        <StatCard
          icon={AlertTriangle}
          label="At-Risk Students"
          value={data.at_risk_students_count}
          hint="Mastery below 55% threshold"
          trend="neutral"
        />
      </div>

      {/* Quick Action Banners */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-brand-200 bg-gradient-to-br from-brand-50 to-brand-100/50 p-5 dark:border-brand-800/60 dark:from-brand-950/40 dark:to-brand-900/20">
          <div className="flex items-center justify-between">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 text-white shadow-sm">
              <Sparkles size={20} />
            </span>
            <span className="text-xs font-semibold text-brand-700 dark:text-brand-300">AI-Powered</span>
          </div>
          <h3 className="mt-3 font-semibold text-ink-900 dark:text-ink-100">AI Assessment Authoring</h3>
          <p className="mt-1 text-xs text-ink-600 dark:text-ink-400">
            Generate rigorous exam questions grounded in your course materials with automatic difficulty suggestions.
          </p>
          <Link to="/instructor/assessments/create" className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400">
            Author Assessment <ArrowRight size={14} />
          </Link>
        </div>

        <div className="rounded-2xl border border-purple-200 bg-gradient-to-br from-purple-50 to-purple-100/50 p-5 dark:border-purple-800/60 dark:from-purple-950/40 dark:to-purple-900/20">
          <div className="flex items-center justify-between">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-600 text-white shadow-sm">
              <BarChart3 size={20} />
            </span>
            <span className="text-xs font-semibold text-purple-700 dark:text-purple-300">Analytics</span>
          </div>
          <h3 className="mt-3 font-semibold text-ink-900 dark:text-ink-100">Topic Mastery Heatmap</h3>
          <p className="mt-1 text-xs text-ink-600 dark:text-ink-400">
            Identify specific syllabus bottlenecks, memory retention decay, and common misconceptions.
          </p>
          <Link to="/instructor/analytics" className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold text-purple-600 hover:text-purple-700 dark:text-purple-400">
            View Analytics <ArrowRight size={14} />
          </Link>
        </div>

        <div className="rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-emerald-100/50 p-5 dark:border-emerald-800/60 dark:from-emerald-950/40 dark:to-emerald-900/20">
          <div className="flex items-center justify-between">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-sm">
              <MessageSquareQuote size={20} />
            </span>
            <span className="text-xs font-semibold text-emerald-700 dark:text-emerald-300">Direct Support</span>
          </div>
          <h3 className="mt-3 font-semibold text-ink-900 dark:text-ink-100">Student Interventions</h3>
          <p className="mt-1 text-xs text-ink-600 dark:text-ink-400">
            Send actionable guidance, recommended tasks, and feedback to at-risk or excelling students.
          </p>
          <Link to="/instructor/feedback" className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-600 hover:text-emerald-700 dark:text-emerald-400">
            Dispatch Feedback <ArrowRight size={14} />
          </Link>
        </div>
      </div>

      {/* Main Content Grid: Recent Submissions & Recent Feedback */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Recent Assessment Submissions (2 Columns) */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <div className="flex items-center justify-between border-b border-ink-100 pb-4 dark:border-ink-800">
              <CardHeader
                title="Recent Assessment Submissions"
                subtitle="Live stream of student assessment completions and performance."
              />
              <Link to="/instructor/assessments">
                <Button variant="ghost" size="sm">
                  View All Assessments
                </Button>
              </Link>
            </div>

            {data.recent_submissions?.length === 0 ? (
              <div className="py-8 text-center text-sm text-ink-500 dark:text-ink-400">
                No assessment submissions recorded yet.
              </div>
            ) : (
              <div className="overflow-x-auto mt-4">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-ink-100 text-xs font-semibold text-ink-400 dark:border-ink-800">
                      <th className="pb-3">Student</th>
                      <th className="pb-3">Assessment</th>
                      <th className="pb-3">Score</th>
                      <th className="pb-3">Outcome</th>
                      <th className="pb-3 text-right">Time</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-ink-50 dark:divide-ink-800/40">
                    {data.recent_submissions.map((sub) => (
                      <tr key={sub.id} className="hover:bg-ink-50/50 dark:hover:bg-ink-800/20">
                        <td className="py-3 font-medium text-ink-900 dark:text-ink-100">
                          <Link to={`/instructor/students`} className="hover:text-brand-600">
                            {sub.student_name}
                          </Link>
                        </td>
                        <td className="py-3 text-ink-600 dark:text-ink-400 max-w-[200px] truncate">
                          {sub.assessment_title}
                        </td>
                        <td className="py-3 font-semibold text-ink-900 dark:text-ink-100">
                          {sub.score}/{sub.total_points} ({sub.percentage}%)
                        </td>
                        <td className="py-3">
                          {sub.passed ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">
                              <CheckCircle2 size={12} />
                              Passed
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2 py-0.5 text-xs font-semibold text-rose-700 dark:bg-rose-950/60 dark:text-rose-300">
                              <XCircle size={12} />
                              Retake Needed
                            </span>
                          )}
                        </td>
                        <td className="py-3 text-right text-xs text-ink-400 dark:text-ink-500">
                          {sub.submitted_at ? new Date(sub.submitted_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recently'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>

        {/* Recent Instructor Feedback & Actions (1 Column) */}
        <div className="space-y-4">
          <Card>
            <div className="flex items-center justify-between border-b border-ink-100 pb-4 dark:border-ink-800">
              <CardHeader
                title="Recent Interventions"
                subtitle="Feedback notes given to students."
              />
              <Link to="/instructor/feedback">
                <Button variant="ghost" size="sm">
                  Manage
                </Button>
              </Link>
            </div>

            {data.recent_feedbacks?.length === 0 ? (
              <div className="py-8 text-center text-sm text-ink-500 dark:text-ink-400">
                No feedback issued yet.
              </div>
            ) : (
              <div className="mt-4 space-y-3">
                {data.recent_feedbacks.map((fb) => (
                  <div key={fb.id} className="rounded-xl border border-ink-100 bg-ink-50/40 p-3 text-xs dark:border-ink-800 dark:bg-ink-800/40">
                    <div className="flex items-center justify-between font-medium text-ink-900 dark:text-ink-100">
                      <span>{fb.student_name}</span>
                      {fb.topic && (
                        <span className="rounded bg-ink-200/60 px-1.5 py-0.2 text-[10px] text-ink-700 dark:bg-ink-700 dark:text-ink-300">
                          {fb.topic}
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-ink-600 dark:text-ink-300 leading-relaxed italic">
                      "{fb.feedback_text}"
                    </p>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-4 pt-3 border-t border-ink-100 dark:border-ink-800">
              <Link to="/instructor/feedback" className="w-full">
                <Button variant="outline" size="sm" className="w-full">
                  <PlusCircle size={14} />
                  Write New Student Feedback
                </Button>
              </Link>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import {
  FileText,
  Printer,
  Download,
  Award,
  Users,
  AlertTriangle,
  CheckCircle2,
  BookOpen,
  TrendingUp,
  Sparkles,
  ArrowRight,
  ShieldCheck
} from 'lucide-react'
import PageHeader from '../../components/PageHeader.jsx'
import Card, { CardHeader } from '../../components/Card.jsx'
import Button from '../../components/Button.jsx'
import ProgressBar from '../../components/ProgressBar.jsx'
import LoadingSpinner from '../../components/LoadingSpinner.jsx'
import ErrorState from '../../components/ErrorState.jsx'
import { getClassSummaryReport } from '../../services/api.js'

export default function Reports() {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await getClassSummaryReport()
        setReport(data)
      } catch (err) {
        setError(err.message || 'Failed to generate class summary report.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const handlePrint = () => {
    window.print()
  }

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <LoadingSpinner size={32} label="Compiling executive academic report..." />
      </div>
    )
  }

  if (error) {
    return <ErrorState message={error} onRetry={() => window.location.reload()} />
  }

  return (
    <div className="space-y-8 pb-16">
      {/* Page Header (Hidden on print) */}
      <div className="print:hidden">
        <PageHeader
          title="Curriculum & Cohort Reports"
          subtitle="Formal academic report summarizing cohort mastery, top performers, at-risk students, and pedagogical recommendations."
          actions={
            <div className="flex items-center gap-3">
              <Button variant="outline" size="sm" onClick={handlePrint}>
                <Printer size={16} />
                Print / Save PDF
              </Button>
            </div>
          }
        />
      </div>

      {/* Printable Report Document Card */}
      <Card className="border border-ink-200 bg-white p-8 dark:border-ink-800 dark:bg-ink-900 shadow-sm print:border-none print:shadow-none print:p-0">
        <div className="space-y-8">
          {/* Formal Report Header */}
          <div className="border-b border-ink-200 pb-6 dark:border-ink-800">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="rounded bg-brand-100 px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider text-brand-700 dark:bg-brand-950 dark:text-brand-300">
                  Academic Performance Audit
                </span>
                <h1 className="mt-2 text-2xl font-bold text-ink-900 dark:text-ink-100">
                  Class Learning Trajectory & Mastery Report
                </h1>
                <p className="text-xs text-ink-500 dark:text-ink-400 mt-1">
                  AI Study Companion Telemetry Engine &bull; Department of Computer Science
                </p>
              </div>

              <div className="text-right text-xs text-ink-500 dark:text-ink-400">
                <p className="font-semibold text-ink-900 dark:text-ink-100">Instructor: {report.instructor_name}</p>
                <p>Generated: {new Date(report.generated_at).toLocaleDateString([], { month: 'long', day: 'numeric', year: 'numeric' })}</p>
                <p>Cohort Size: {report.total_enrolled} Enrolled Students</p>
              </div>
            </div>

            {/* High Level Score Pill Bar */}
            <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4 rounded-2xl bg-ink-50 p-4 text-center dark:bg-ink-800/60">
              <div>
                <span className="text-[11px] font-semibold text-ink-400 block">Class Avg Mastery</span>
                <span className="text-xl font-bold text-brand-600 dark:text-brand-400">
                  {report.class_average_mastery}%
                </span>
              </div>
              <div>
                <span className="text-[11px] font-semibold text-ink-400 block">Assessments Published</span>
                <span className="text-xl font-bold text-ink-900 dark:text-ink-100">
                  {report.assessment_summary.total_created}
                </span>
              </div>
              <div>
                <span className="text-[11px] font-semibold text-ink-400 block">Total Submissions</span>
                <span className="text-xl font-bold text-ink-900 dark:text-ink-100">
                  {report.assessment_summary.total_submissions}
                </span>
              </div>
              <div>
                <span className="text-[11px] font-semibold text-ink-400 block">Avg Exam Score</span>
                <span className="text-xl font-bold text-emerald-600 dark:text-emerald-400">
                  {report.assessment_summary.average_score}%
                </span>
              </div>
            </div>
          </div>

          {/* Section 1: Pedagogical Action Plan */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Sparkles size={18} className="text-brand-600" />
              <h3 className="text-sm font-bold text-ink-900 dark:text-ink-100 uppercase tracking-wider">
                1. Recommended Instructional Roadmap
              </h3>
            </div>
            <div className="rounded-2xl border border-brand-200 bg-brand-50/40 p-4 text-xs dark:border-brand-900/50 dark:bg-brand-950/20">
              <ul className="space-y-2 text-ink-700 dark:text-ink-300">
                {report.recommended_class_actions.map((act, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <CheckCircle2 size={14} className="mt-0.5 shrink-0 text-brand-600 dark:text-brand-400" />
                    <span>{act}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Section 2: Top Academic Performers */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Award size={18} className="text-emerald-600" />
              <h3 className="text-sm font-bold text-ink-900 dark:text-ink-100 uppercase tracking-wider">
                2. Top Academic Performers (Excelling Tier)
              </h3>
            </div>
            <div className="overflow-x-auto rounded-xl border border-ink-100 dark:border-ink-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-ink-50 dark:bg-ink-800/60 font-semibold text-ink-500">
                  <tr>
                    <th className="p-3">Rank</th>
                    <th className="p-3">Student</th>
                    <th className="p-3">Overall Mastery</th>
                    <th className="p-3">Quizzes Completed</th>
                    <th className="p-3">Oral Vivas Taken</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink-100 dark:divide-ink-800/50">
                  {report.top_performers.map((s, idx) => (
                    <tr key={s.id}>
                      <td className="p-3 font-bold text-brand-600">#{idx + 1}</td>
                      <td className="p-3 font-semibold text-ink-900 dark:text-ink-100">
                        {s.name} <span className="text-[10px] text-ink-400 font-normal">({s.email})</span>
                      </td>
                      <td className="p-3 font-bold text-emerald-600 dark:text-emerald-400">{s.mastery}%</td>
                      <td className="p-3">{s.quizzes}</td>
                      <td className="p-3">{s.vivas}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 3: Students Requiring Intervention */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle size={18} className="text-rose-600" />
              <h3 className="text-sm font-bold text-ink-900 dark:text-ink-100 uppercase tracking-wider">
                3. Students Requiring Remediation & Interventions
              </h3>
            </div>
            {report.students_needing_intervention.length === 0 ? (
              <p className="text-xs text-ink-500 p-3 bg-ink-50 rounded-xl">
                No students currently in the At-Risk bracket. Entire cohort is performing above the 55% threshold.
              </p>
            ) : (
              <div className="overflow-x-auto rounded-xl border border-ink-100 dark:border-ink-800">
                <table className="w-full text-left text-xs">
                  <thead className="bg-ink-50 dark:bg-ink-800/60 font-semibold text-ink-500">
                    <tr>
                      <th className="p-3">Student</th>
                      <th className="p-3">Current Mastery</th>
                      <th className="p-3">Quizzes</th>
                      <th className="p-3">Vivas</th>
                      <th className="p-3">Intervention Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-ink-100 dark:divide-ink-800/50">
                    {report.students_needing_intervention.map((s) => (
                      <tr key={s.id}>
                        <td className="p-3 font-semibold text-ink-900 dark:text-ink-100">
                          {s.name} <span className="text-[10px] text-ink-400 font-normal">({s.email})</span>
                        </td>
                        <td className="p-3 font-bold text-rose-600 dark:text-rose-400">{s.mastery}%</td>
                        <td className="p-3">{s.quizzes}</td>
                        <td className="p-3">{s.vivas}</td>
                        <td className="p-3">
                          <span className="rounded bg-rose-50 px-2 py-0.5 text-[10px] font-bold text-rose-700 dark:bg-rose-950/60 dark:text-rose-300">
                            Immediate Review Recommended
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Section 4: Syllabus Topic Breakdown */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <BookOpen size={18} className="text-ink-700 dark:text-ink-300" />
              <h3 className="text-sm font-bold text-ink-900 dark:text-ink-100 uppercase tracking-wider">
                4. Topic Mastery & Retention Breakdown
              </h3>
            </div>
            <div className="overflow-x-auto rounded-xl border border-ink-100 dark:border-ink-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-ink-50 dark:bg-ink-800/60 font-semibold text-ink-500">
                  <tr>
                    <th className="p-3">Topic</th>
                    <th className="p-3">Class Avg Mastery</th>
                    <th className="p-3">Quiz Accuracy</th>
                    <th className="p-3">Viva Score</th>
                    <th className="p-3">Identified Weakness</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink-100 dark:divide-ink-800/50">
                  {report.topic_breakdown.map((t, idx) => (
                    <tr key={idx}>
                      <td className="p-3 font-semibold text-ink-900 dark:text-ink-100">{t.topic}</td>
                      <td className="p-3 font-bold text-ink-900 dark:text-ink-100">{t.average_mastery}%</td>
                      <td className="p-3">{t.average_quiz_accuracy}%</td>
                      <td className="p-3">{t.average_viva_score}%</td>
                      <td className="p-3 text-ink-500 dark:text-ink-400">{t.common_weakness_summary}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Report Footer */}
          <div className="pt-6 border-t border-ink-200 text-center text-[11px] text-ink-400 dark:border-ink-800">
            <p>End of Official Academic Telemetry Report &bull; AI Study Companion &bull; Confidential Class Record</p>
          </div>
        </div>
      </Card>
    </div>
  )
}

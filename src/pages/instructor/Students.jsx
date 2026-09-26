import { useState, useEffect } from 'react'
import {
  Users,
  Search,
  Award,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  BookOpen,
  Mic,
  MessageSquareQuote,
  Eye,
  Calendar,
  Send,
  Sparkles,
  ShieldCheck,
  Clock
} from 'lucide-react'
import PageHeader from '../../components/PageHeader.jsx'
import Card, { CardHeader } from '../../components/Card.jsx'
import Button from '../../components/Button.jsx'
import ProgressBar from '../../components/ProgressBar.jsx'
import Modal from '../../components/Modal.jsx'
import LoadingSpinner from '../../components/LoadingSpinner.jsx'
import ErrorState from '../../components/ErrorState.jsx'
import EmptyState from '../../components/EmptyState.jsx'
import {
  getInstructorStudents,
  getInstructorStudentDetail,
  createInstructorFeedback
} from '../../services/api.js'
import { useToast } from '../../context/ToastContext.jsx'

export default function Students() {
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [riskFilter, setRiskFilter] = useState('all')

  // Student Detail Modal State
  const [selectedStudentDetail, setSelectedStudentDetail] = useState(null)
  const [detailModalOpen, setDetailModalOpen] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)

  // Feedback Modal State
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false)
  const [feedbackStudent, setFeedbackStudent] = useState(null)
  const [feedbackTopic, setFeedbackTopic] = useState('')
  const [feedbackType, setFeedbackType] = useState('general_guidance')
  const [feedbackText, setFeedbackText] = useState('')
  const [actionItemsText, setActionItemsText] = useState('')
  const [submittingFeedback, setSubmittingFeedback] = useState(false)

  const toast = useToast()

  const loadStudents = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getInstructorStudents()
      setStudents(data || [])
    } catch (err) {
      setError(err.message || 'Failed to load enrolled students.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStudents()
  }, [])

  // Open detail progress modal
  const handleInspectProgress = async (studentId) => {
    setDetailLoading(true)
    setDetailModalOpen(true)
    try {
      const detail = await getInstructorStudentDetail(studentId)
      setSelectedStudentDetail(detail)
    } catch (err) {
      toast(err.message || 'Could not fetch student progress details.', 'error')
    } finally {
      setDetailLoading(false)
    }
  }

  // Open feedback modal
  const handleOpenFeedback = (student) => {
    setFeedbackStudent(student)
    setFeedbackTopic('')
    setFeedbackType('topic_intervention')
    setFeedbackText('')
    setActionItemsText('')
    setFeedbackModalOpen(true)
  }

  // Submit feedback
  const handleSendFeedback = async (e) => {
    e.preventDefault()
    if (!feedbackText.trim() || feedbackText.trim().length < 5) {
      toast('Please provide substantive feedback (at least 5 characters).', 'error')
      return
    }

    const actionItems = actionItemsText
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean)

    setSubmittingFeedback(true)
    try {
      await createInstructorFeedback({
        student_id: feedbackStudent.id,
        topic: feedbackTopic.trim() || null,
        feedback_type: feedbackType,
        feedback_text: feedbackText.trim(),
        action_items: actionItems
      })
      toast(`Personalized feedback sent to ${feedbackStudent.name}!`, 'success')
      setFeedbackModalOpen(false)
    } catch (err) {
      toast(err.message || 'Failed to send feedback.', 'error')
    } finally {
      setSubmittingFeedback(false)
    }
  }

  // Filter students
  const filteredStudents = students.filter((s) => {
    const matchesSearch =
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.email.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesRisk =
      riskFilter === 'all' ||
      (riskFilter === 'excelling' && s.risk_status === 'excelling') ||
      (riskFilter === 'on_track' && s.risk_status === 'on_track') ||
      (riskFilter === 'at_risk' && s.risk_status === 'at_risk')
    return matchesSearch && matchesRisk
  })

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <LoadingSpinner size={32} label="Loading class roster and progress..." />
      </div>
    )
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadStudents} />
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <PageHeader
        title="Students & Learning Progress"
        subtitle="Track individual learner trajectories, inspect topic mastery matrices, and deliver targeted interventions."
      />

      {/* Filter and Search */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
          <input
            type="text"
            placeholder="Search student by name or email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-xl border border-ink-200 bg-white py-2 pl-9 pr-4 text-xs text-ink-900 placeholder:text-ink-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
          />
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-ink-500 dark:text-ink-400">Cohort Filter:</label>
          <div className="flex items-center rounded-xl border border-ink-200 bg-white p-1 dark:border-ink-800 dark:bg-ink-900">
            {['all', 'excelling', 'on_track', 'at_risk'].map((tier) => (
              <button
                key={tier}
                onClick={() => setRiskFilter(tier)}
                className={`rounded-lg px-2.5 py-1 text-xs font-semibold capitalize transition-all ${
                  riskFilter === tier
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'text-ink-600 hover:text-ink-900 dark:text-ink-400 dark:hover:text-ink-100'
                }`}
              >
                {tier.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Student Cards Grid */}
      {filteredStudents.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No students match the selected filter"
          description="Try selecting 'All' or modifying your search query."
        />
      ) : (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
          {filteredStudents.map((s) => (
            <Card key={s.id} className="flex flex-col justify-between hover:shadow-md transition-shadow">
              <div className="space-y-4">
                {/* Student Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-600 text-sm font-bold text-white shadow-sm">
                      {s.name.charAt(0).toUpperCase()}
                    </span>
                    <div>
                      <h3 className="font-bold text-ink-900 dark:text-ink-100 leading-tight">
                        {s.name}
                      </h3>
                      <p className="text-xs text-ink-400 dark:text-ink-500">{s.email}</p>
                    </div>
                  </div>

                  {s.risk_status === 'excelling' && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-bold text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">
                      <CheckCircle2 size={11} />
                      Excelling
                    </span>
                  )}
                  {s.risk_status === 'on_track' && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-bold text-brand-700 dark:bg-brand-950/60 dark:text-brand-300">
                      <TrendingUp size={11} />
                      On Track
                    </span>
                  )}
                  {s.risk_status === 'at_risk' && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2 py-0.5 text-[11px] font-bold text-rose-700 dark:bg-rose-950/60 dark:text-rose-300">
                      <AlertTriangle size={11} />
                      At Risk
                    </span>
                  )}
                </div>

                {/* Overall Mastery Meter */}
                <div>
                  <div className="flex items-center justify-between text-xs font-semibold mb-1">
                    <span className="text-ink-600 dark:text-ink-400">Overall Syllabus Mastery</span>
                    <span className="text-ink-900 dark:text-ink-100 font-bold">{s.overall_mastery}%</span>
                  </div>
                  <ProgressBar value={s.overall_mastery} />
                </div>

                {/* Micro Stats */}
                <div className="grid grid-cols-3 gap-2 rounded-xl bg-ink-50/60 p-2 text-center text-xs dark:bg-ink-800/40">
                  <div>
                    <span className="block text-[10px] font-semibold text-ink-400">Topics</span>
                    <span className="font-bold text-ink-800 dark:text-ink-200">{s.topics_tracked}</span>
                  </div>
                  <div>
                    <span className="block text-[10px] font-semibold text-ink-400">Quizzes</span>
                    <span className="font-bold text-ink-800 dark:text-ink-200">{s.quizzes_completed}</span>
                  </div>
                  <div>
                    <span className="block text-[10px] font-semibold text-ink-400">Vivas</span>
                    <span className="font-bold text-ink-800 dark:text-ink-200">{s.viva_sessions_completed}</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-5 pt-3 border-t border-ink-100 dark:border-ink-800 flex items-center justify-between gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleInspectProgress(s.id)}
                  className="flex-1"
                >
                  <Eye size={14} />
                  Inspect Progress
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleOpenFeedback(s)}
                  className="text-brand-600 hover:bg-brand-50 dark:text-brand-400 dark:hover:bg-brand-950/40"
                  title="Send feedback note"
                >
                  <MessageSquareQuote size={15} />
                  Feedback
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Student Deep-Dive Progress Modal */}
      <Modal
        isOpen={detailModalOpen}
        onClose={() => setDetailModalOpen(false)}
        title={selectedStudentDetail ? `${selectedStudentDetail.name}'s Learning Profile` : 'Student Progress'}
        size="lg"
      >
        {detailLoading ? (
          <div className="py-12 flex justify-center">
            <LoadingSpinner size={28} label="Loading detailed performance telemetry..." />
          </div>
        ) : selectedStudentDetail ? (
          <div className="space-y-6">
            {/* Summary Bar */}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 rounded-xl bg-ink-50 p-3 text-xs dark:bg-ink-800/60">
              <div>
                <span className="text-ink-400 block font-medium">Overall Mastery</span>
                <span className="font-bold text-brand-600 dark:text-brand-400 text-sm">
                  {selectedStudentDetail.overall_mastery}%
                </span>
              </div>
              <div>
                <span className="text-ink-400 block font-medium">Total Study Time</span>
                <span className="font-bold text-ink-800 dark:text-ink-200 text-sm">
                  {Math.round(selectedStudentDetail.total_study_minutes / 60)} hrs
                </span>
              </div>
              <div>
                <span className="text-ink-400 block font-medium">Active Streak</span>
                <span className="font-bold text-ink-800 dark:text-ink-200 text-sm">
                  {selectedStudentDetail.streak_days} days
                </span>
              </div>
              <div>
                <span className="text-ink-400 block font-medium">Cohort Status</span>
                <span className="font-bold capitalize text-ink-800 dark:text-ink-200 text-sm">
                  {selectedStudentDetail.risk_status.replace('_', ' ')}
                </span>
              </div>
            </div>

            {/* Topic Mastery Matrix */}
            <div>
              <h4 className="text-sm font-bold text-ink-900 dark:text-ink-100 mb-2">
                Topic Mastery & Retention Matrix ({selectedStudentDetail.topics.length})
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-ink-200 text-ink-400 dark:border-ink-800 font-semibold">
                      <th className="pb-2">Topic</th>
                      <th className="pb-2">Mastery</th>
                      <th className="pb-2">Quiz Acc</th>
                      <th className="pb-2">Flashcards</th>
                      <th className="pb-2">Viva Score</th>
                      <th className="pb-2">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-ink-100 dark:divide-ink-800/50">
                    {selectedStudentDetail.topics.map((t, idx) => (
                      <tr key={idx}>
                        <td className="py-2 font-medium text-ink-900 dark:text-ink-100">{t.topic}</td>
                        <td className="py-2 font-bold text-ink-900 dark:text-ink-100">{t.mastery}%</td>
                        <td className="py-2 text-ink-600 dark:text-ink-300">{t.quiz_accuracy}%</td>
                        <td className="py-2 text-ink-600 dark:text-ink-300">{t.flashcard_score}%</td>
                        <td className="py-2 text-ink-600 dark:text-ink-300">{t.viva_score}%</td>
                        <td className="py-2">
                          <span
                            className={`rounded-full px-2 py-0.5 text-[10px] font-bold capitalize ${
                              t.status === 'mastered'
                                ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
                                : t.status === 'proficient'
                                ? 'bg-brand-100 text-brand-800 dark:bg-brand-950/60 dark:text-brand-300'
                                : 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300'
                            }`}
                          >
                            {t.status.replace('_', ' ')}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Recent Vivas & Quizzes Tabs / List */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <h4 className="text-xs font-bold text-ink-900 dark:text-ink-100 mb-2">Recent Quizzes</h4>
                {selectedStudentDetail.recent_quizzes.length === 0 ? (
                  <p className="text-xs text-ink-400">No quizzes completed yet.</p>
                ) : (
                  <div className="space-y-1.5 text-xs">
                    {selectedStudentDetail.recent_quizzes.slice(0, 4).map((q) => (
                      <div key={q.id} className="flex justify-between rounded-lg bg-ink-50/70 p-2 dark:bg-ink-800/40">
                        <span className="font-medium text-ink-800 dark:text-ink-200">{q.topic}</span>
                        <span className="font-bold text-ink-900 dark:text-ink-100">{q.accuracy}%</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <h4 className="text-xs font-bold text-ink-900 dark:text-ink-100 mb-2">Recent Viva Sessions</h4>
                {selectedStudentDetail.recent_vivas.length === 0 ? (
                  <p className="text-xs text-ink-400">No viva sessions recorded.</p>
                ) : (
                  <div className="space-y-1.5 text-xs">
                    {selectedStudentDetail.recent_vivas.slice(0, 4).map((v) => (
                      <div key={v.id} className="flex justify-between rounded-lg bg-ink-50/70 p-2 dark:bg-ink-800/40">
                        <span className="font-medium text-ink-800 dark:text-ink-200">{v.topic} ({v.mode})</span>
                        <span className="font-bold text-brand-600 dark:text-brand-400">{v.overall_score}%</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : null}
      </Modal>

      {/* Issue Feedback Modal */}
      <Modal
        isOpen={feedbackModalOpen}
        onClose={() => setFeedbackModalOpen(false)}
        title={feedbackStudent ? `Send Feedback to ${feedbackStudent.name}` : 'Instructor Feedback'}
        size="md"
      >
        <form onSubmit={handleSendFeedback} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-ink-700 dark:text-ink-300 mb-1">
              Feedback Category
            </label>
            <select
              value={feedbackType}
              onChange={(e) => setFeedbackType(e.target.value)}
              className="w-full rounded-xl border border-ink-200 bg-white p-2.5 text-xs text-ink-900 focus:outline-none dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
            >
              <option value="topic_intervention">Topic Intervention / Conceptual Help</option>
              <option value="assessment_review">Assessment Performance Review</option>
              <option value="general_guidance">General Study Guidance</option>
              <option value="commendation">Commendation / Praise</option>
            </select>
          </div>

          <div>
            <label className="block font-semibold text-ink-700 dark:text-ink-300 mb-1">
              Related Topic (Optional)
            </label>
            <input
              type="text"
              value={feedbackTopic}
              onChange={(e) => setFeedbackTopic(e.target.value)}
              placeholder="e.g. Deadlocks"
              className="w-full rounded-xl border border-ink-200 bg-white p-2.5 text-xs text-ink-900 focus:outline-none dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
            />
          </div>

          <div>
            <label className="block font-semibold text-ink-700 dark:text-ink-300 mb-1">
              Feedback Message
            </label>
            <textarea
              rows={4}
              value={feedbackText}
              onChange={(e) => setFeedbackText(e.target.value)}
              placeholder="Write clear, encouraging, and actionable guidance for the student..."
              className="w-full rounded-xl border border-ink-200 bg-white p-2.5 text-xs text-ink-900 focus:outline-none dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
              required
            />
          </div>

          <div>
            <label className="block font-semibold text-ink-700 dark:text-ink-300 mb-1">
              Recommended Action Items (One per line)
            </label>
            <textarea
              rows={3}
              value={actionItemsText}
              onChange={(e) => setActionItemsText(e.target.value)}
              placeholder="e.g. Review Coffman conditions lecture notes&#10;Complete 10 active recall flashcards"
              className="w-full rounded-xl border border-ink-200 bg-white p-2.5 text-xs text-ink-900 focus:outline-none dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-ink-100 dark:border-ink-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setFeedbackModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={submittingFeedback}
            >
              {submittingFeedback ? <LoadingSpinner size={14} /> : <Send size={14} />}
              Send Guidance Note
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

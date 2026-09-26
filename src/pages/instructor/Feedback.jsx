import { useState, useEffect } from 'react'
import {
  MessageSquareQuote,
  Send,
  PlusCircle,
  CheckCircle2,
  Clock,
  User,
  BookOpen,
  Sparkles,
  Search,
  Filter
} from 'lucide-react'
import PageHeader from '../../components/PageHeader.jsx'
import Card, { CardHeader } from '../../components/Card.jsx'
import Button from '../../components/Button.jsx'
import LoadingSpinner from '../../components/LoadingSpinner.jsx'
import ErrorState from '../../components/ErrorState.jsx'
import EmptyState from '../../components/EmptyState.jsx'
import {
  getInstructorFeedbacks,
  createInstructorFeedback,
  getInstructorStudents
} from '../../services/api.js'
import { useToast } from '../../context/ToastContext.jsx'

export default function Feedback() {
  const [feedbacks, setFeedbacks] = useState([])
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Form State
  const [selectedStudentId, setSelectedStudentId] = useState('')
  const [feedbackType, setFeedbackType] = useState('topic_intervention')
  const [topic, setTopic] = useState('Deadlocks')
  const [message, setMessage] = useState('')
  const [actionItemsText, setActionItemsText] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const toast = useToast()

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [fbList, studList] = await Promise.all([
        getInstructorFeedbacks(),
        getInstructorStudents()
      ])
      setFeedbacks(fbList || [])
      setStudents(studList || [])
      if (studList && studList.length > 0) {
        setSelectedStudentId(studList[0].id)
      }
    } catch (err) {
      setError(err.message || 'Failed to load feedback records.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!selectedStudentId) {
      toast('Please select a student.', 'error')
      return
    }
    if (!message.trim() || message.trim().length < 5) {
      toast('Please enter a substantive guidance note (at least 5 characters).', 'error')
      return
    }

    const actionItems = actionItemsText
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean)

    setSubmitting(true)
    try {
      await createInstructorFeedback({
        student_id: Number(selectedStudentId),
        topic: topic.trim() || null,
        feedback_type: feedbackType,
        feedback_text: message.trim(),
        action_items: actionItems
      })
      toast('Personalized feedback dispatched to student!', 'success')
      setMessage('')
      setActionItemsText('')
      loadData()
    } catch (err) {
      toast(err.message || 'Failed to submit feedback.', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <LoadingSpinner size={32} label="Loading feedback records..." />
      </div>
    )
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadData} />
  }

  return (
    <div className="space-y-8 pb-12">
      {/* Page Header */}
      <PageHeader
        title="Student Feedback & Interventions"
        subtitle="Deliver personalized guidance, study task recommendations, and commendations directly to students."
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Feedback Composer Form (1 Col) */}
        <Card className="lg:col-span-1 border-t-4 border-t-brand-600">
          <CardHeader
            title="Compose Guidance Note"
            subtitle="Send targeted advice with concrete action items."
          />

          <form onSubmit={handleSubmit} className="mt-4 space-y-4 text-xs">
            <div>
              <label className="block font-semibold text-ink-700 dark:text-ink-300 mb-1">
                Recipient Student
              </label>
              <select
                value={selectedStudentId}
                onChange={(e) => setSelectedStudentId(e.target.value)}
                className="w-full rounded-xl border border-ink-200 bg-white p-2.5 text-xs text-ink-900 focus:outline-none dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
                required
              >
                {students.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.email}) — Mastery: {s.overall_mastery}%
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block font-semibold text-ink-700 dark:text-ink-300 mb-1">
                Intervention Category
              </label>
              <select
                value={feedbackType}
                onChange={(e) => setFeedbackType(e.target.value)}
                className="w-full rounded-xl border border-ink-200 bg-white p-2.5 text-xs text-ink-900 focus:outline-none dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
              >
                <option value="topic_intervention">Topic Intervention / Remediation</option>
                <option value="assessment_review">Assessment Review</option>
                <option value="general_guidance">General Study Guidance</option>
                <option value="commendation">Commendation / Outstanding Work</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-ink-700 dark:text-ink-300 mb-1">
                Related Syllabus Topic (Optional)
              </label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. Deadlocks"
                className="w-full rounded-xl border border-ink-200 bg-white p-2.5 text-xs text-ink-900 focus:outline-none dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
              />
            </div>

            <div>
              <label className="block font-semibold text-ink-700 dark:text-ink-300 mb-1">
                Guidance Message
              </label>
              <textarea
                rows={4}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Explain the student's conceptual strengths, missing nuances, or recommendations..."
                className="w-full rounded-xl border border-ink-200 bg-white p-2.5 text-xs text-ink-900 focus:outline-none dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
                required
              />
            </div>

            <div>
              <label className="block font-semibold text-ink-700 dark:text-ink-300 mb-1">
                Recommended Tasks (One per line)
              </label>
              <textarea
                rows={3}
                value={actionItemsText}
                onChange={(e) => setActionItemsText(e.target.value)}
                placeholder="e.g. Review lecture slides on Banker's Algorithm&#10;Complete 10 active recall flashcards"
                className="w-full rounded-xl border border-ink-200 bg-white p-2.5 text-xs text-ink-900 focus:outline-none dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              disabled={submitting}
              className="w-full"
            >
              {submitting ? <LoadingSpinner size={16} /> : <Send size={16} />}
              Send Guidance to Student
            </Button>
          </form>
        </Card>

        {/* Feedback History Timeline (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader
              title={`Feedback History (${feedbacks.length})`}
              subtitle="All personalized notes and interventions issued to students."
            />

            {feedbacks.length === 0 ? (
              <div className="py-12 text-center text-sm text-ink-500 dark:text-ink-400">
                No feedback notes issued yet. Use the composer on the left to send your first guidance note.
              </div>
            ) : (
              <div className="mt-4 space-y-4">
                {feedbacks.map((fb) => (
                  <div
                    key={fb.id}
                    className="rounded-2xl border border-ink-200 bg-white p-4 dark:border-ink-800 dark:bg-ink-900 shadow-sm"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-ink-100 pb-2.5 dark:border-ink-800">
                      <div className="flex items-center gap-2">
                        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-100 text-brand-700 text-xs font-bold dark:bg-brand-900 dark:text-brand-300">
                          {fb.student_name.charAt(0).toUpperCase()}
                        </span>
                        <div>
                          <span className="font-bold text-ink-900 dark:text-ink-100 text-xs">
                            {fb.student_name}
                          </span>
                          <span className="text-[10px] text-ink-400 ml-1.5">{fb.student_email}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {fb.topic && (
                          <span className="rounded-md bg-ink-100 px-2 py-0.5 text-[10px] font-semibold text-ink-700 dark:bg-ink-800 dark:text-ink-300">
                            {fb.topic}
                          </span>
                        )}
                        <span className="rounded-md bg-purple-50 px-2 py-0.5 text-[10px] font-semibold text-purple-700 dark:bg-purple-950/50 dark:text-purple-300 capitalize">
                          {fb.feedback_type.replace('_', ' ')}
                        </span>
                      </div>
                    </div>

                    <p className="mt-3 text-xs text-ink-700 dark:text-ink-200 leading-relaxed">
                      "{fb.feedback_text}"
                    </p>

                    {fb.action_items?.length > 0 && (
                      <div className="mt-3 rounded-xl bg-ink-50 p-2.5 text-xs dark:bg-ink-800/40">
                        <span className="font-semibold text-ink-700 dark:text-ink-300 block mb-1">
                          Recommended Action Items:
                        </span>
                        <ul className="list-disc list-inside space-y-0.5 text-ink-600 dark:text-ink-400">
                          {fb.action_items.map((item, i) => (
                            <li key={i}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div className="mt-3 flex items-center justify-between text-[11px] text-ink-400">
                      <span>Issued: {new Date(fb.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                      <span>
                        {fb.is_read ? (
                          <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-semibold">
                            <CheckCircle2 size={12} /> Acknowledged by student
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-ink-400">
                            <Clock size={12} /> Unread
                          </span>
                        )}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}

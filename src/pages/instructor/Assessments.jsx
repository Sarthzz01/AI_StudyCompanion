import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  BookOpenCheck,
  PlusCircle,
  Search,
  Users,
  Clock,
  Award,
  CheckCircle2,
  XCircle,
  Share2,
  Trash2,
  Eye,
  Calendar,
  AlertCircle,
  Sparkles,
  FileSpreadsheet
} from 'lucide-react'
import PageHeader from '../../components/PageHeader.jsx'
import Card from '../../components/Card.jsx'
import Button from '../../components/Button.jsx'
import Modal from '../../components/Modal.jsx'
import LoadingSpinner from '../../components/LoadingSpinner.jsx'
import ErrorState from '../../components/ErrorState.jsx'
import EmptyState from '../../components/EmptyState.jsx'
import {
  getInstructorAssessments,
  getInstructorAssessment,
  deleteInstructorAssessment,
  assignInstructorAssessment,
  getInstructorStudents
} from '../../services/api.js'
import { useToast } from '../../context/ToastContext.jsx'

export default function Assessments() {
  const [assessments, setAssessments] = useState([])
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterTopic, setFilterTopic] = useState('all')

  // Modals state
  const [selectedAssessmentDetail, setSelectedAssessmentDetail] = useState(null)
  const [detailModalOpen, setDetailModalOpen] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)

  const [assignModalOpen, setAssignModalOpen] = useState(false)
  const [assignAssessmentId, setAssignAssessmentId] = useState(null)
  const [assignToAll, setAssignToAll] = useState(true)
  const [assignStudentId, setAssignStudentId] = useState('')
  const [assignDueDate, setAssignDueDate] = useState('')
  const [assignInstructions, setAssignInstructions] = useState('')
  const [assigning, setAssigning] = useState(false)

  const toast = useToast()

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [list, studList] = await Promise.all([
        getInstructorAssessments(),
        getInstructorStudents()
      ])
      setAssessments(list || [])
      setStudents(studList || [])
    } catch (err) {
      setError(err.message || 'Failed to load assessments.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // View detail handler
  const handleViewDetail = async (id) => {
    setDetailLoading(true)
    setDetailModalOpen(true)
    try {
      const data = await getInstructorAssessment(id)
      setSelectedAssessmentDetail(data)
    } catch (err) {
      toast(err.message || 'Failed to fetch assessment details.', 'error')
    } finally {
      setDetailLoading(false)
    }
  }

  // Delete handler
  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this assessment? All associated student submissions will be permanently removed.')) {
      return
    }
    try {
      await deleteInstructorAssessment(id)
      toast('Assessment deleted successfully.', 'success')
      setAssessments((prev) => prev.filter((a) => a.id !== id))
    } catch (err) {
      toast(err.message || 'Failed to delete assessment.', 'error')
    }
  }

  // Assign modal open
  const openAssignModal = (id) => {
    setAssignAssessmentId(id)
    setAssignToAll(true)
    setAssignStudentId('')
    setAssignDueDate('')
    setAssignInstructions('')
    setAssignModalOpen(true)
  }

  // Submit assignment
  const handleAssignSubmit = async (e) => {
    e.preventDefault()
    setAssigning(true)
    try {
      await assignInstructorAssessment(assignAssessmentId, {
        assigned_to_all: assignToAll,
        student_id: assignToAll ? null : Number(assignStudentId),
        due_date: assignDueDate ? new Date(assignDueDate).toISOString() : null,
        instructions: assignInstructions.trim() || null
      })
      toast('Assessment successfully assigned! Students notified.', 'success')
      setAssignModalOpen(false)
      loadData()
    } catch (err) {
      toast(err.message || 'Failed to assign assessment.', 'error')
    } finally {
      setAssigning(false)
    }
  }

  // Filter topics
  const topics = Array.from(new Set(assessments.map((a) => a.topic).filter(Boolean)))
  const filtered = assessments.filter((a) => {
    const matchSearch =
      a.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.topic.toLowerCase().includes(searchQuery.toLowerCase())
    const matchTopic = filterTopic === 'all' || a.topic === filterTopic
    return matchSearch && matchTopic
  })

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <LoadingSpinner size={32} label="Loading assessment directory..." />
      </div>
    )
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadData} />
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <PageHeader
        title="Assessment Management"
        subtitle="Author, assign, and review curriculum assessments and evaluate student score outcomes."
        actions={
          <Link to="/instructor/assessments/create">
            <Button variant="primary" size="sm">
              <PlusCircle size={16} />
              Create Assessment
            </Button>
          </Link>
        }
      />

      {/* Filter and Search Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
          <input
            type="text"
            placeholder="Search assessments by title or topic..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-xl border border-ink-200 bg-white py-2 pl-9 pr-4 text-xs text-ink-900 placeholder:text-ink-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
          />
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-ink-500 dark:text-ink-400">Topic Filter:</label>
          <select
            value={filterTopic}
            onChange={(e) => setFilterTopic(e.target.value)}
            className="rounded-xl border border-ink-200 bg-white px-3 py-1.5 text-xs font-medium text-ink-900 focus:outline-none dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
          >
            <option value="all">All Topics ({assessments.length})</option>
            {topics.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Assessments Grid */}
      {filtered.length === 0 ? (
        <EmptyState
          icon={BookOpenCheck}
          title="No assessments found"
          description={
            searchQuery
              ? 'Try modifying your search or filter terms.'
              : 'Create your first course assessment or use the AI co-pilot to generate one.'
          }
          action={
            <Link to="/instructor/assessments/create">
              <Button variant="primary" size="sm">
                <Sparkles size={16} />
                Generate Assessment (AI)
              </Button>
            </Link>
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((a) => (
            <Card key={a.id} className="flex flex-col justify-between hover:shadow-md transition-shadow">
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <span className="rounded-lg bg-brand-50 px-2.5 py-1 text-xs font-semibold text-brand-700 dark:bg-brand-950/60 dark:text-brand-300">
                    {a.topic}
                  </span>
                  <span className="rounded-full bg-ink-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-ink-600 dark:bg-ink-800 dark:text-ink-400">
                    {a.difficulty}
                  </span>
                </div>

                <div>
                  <h3 className="font-bold text-ink-900 dark:text-ink-100 line-clamp-1 leading-snug">
                    {a.title}
                  </h3>
                  <p className="mt-1 text-xs text-ink-500 dark:text-ink-400 line-clamp-2">
                    {a.description || `${a.question_count} conceptual multiple choice questions.`}
                  </p>
                </div>

                <div className="grid grid-cols-3 gap-2 rounded-xl bg-ink-50/60 p-2.5 text-center text-xs dark:bg-ink-800/40">
                  <div>
                    <span className="block text-[10px] font-semibold text-ink-400">Time</span>
                    <span className="font-bold text-ink-800 dark:text-ink-200">{a.time_limit_minutes}m</span>
                  </div>
                  <div>
                    <span className="block text-[10px] font-semibold text-ink-400">Points</span>
                    <span className="font-bold text-ink-800 dark:text-ink-200">{a.total_points}</span>
                  </div>
                  <div>
                    <span className="block text-[10px] font-semibold text-ink-400">Submissions</span>
                    <span className="font-bold text-brand-600 dark:text-brand-400">{a.total_submissions}</span>
                  </div>
                </div>

                {a.total_submissions > 0 && (
                  <div className="flex items-center justify-between text-xs px-1">
                    <span className="text-ink-500 dark:text-ink-400">Average Score:</span>
                    <span className="font-bold text-ink-900 dark:text-ink-100">
                      {a.average_score}%
                    </span>
                  </div>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-ink-100 dark:border-ink-800 flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleViewDetail(a.id)}
                    title="View details & student submissions"
                  >
                    <Eye size={15} />
                    Submissions
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => openAssignModal(a.id)}
                    title="Assign to students"
                  >
                    <Share2 size={15} />
                    Assign
                  </Button>
                </div>

                <button
                  type="button"
                  onClick={() => handleDelete(a.id)}
                  className="rounded-lg p-1.5 text-ink-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40"
                  title="Delete assessment"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Assessment Submissions & Details Modal */}
      <Modal
        isOpen={detailModalOpen}
        onClose={() => setDetailModalOpen(false)}
        title={selectedAssessmentDetail?.title || 'Assessment Details'}
        size="lg"
      >
        {detailLoading ? (
          <div className="py-12 flex justify-center">
            <LoadingSpinner size={28} label="Fetching submission records..." />
          </div>
        ) : selectedAssessmentDetail ? (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 rounded-xl bg-ink-50 p-3 text-xs dark:bg-ink-800/60">
              <div>
                <span className="text-ink-400 block font-medium">Topic</span>
                <span className="font-bold text-ink-800 dark:text-ink-200">{selectedAssessmentDetail.topic}</span>
              </div>
              <div>
                <span className="text-ink-400 block font-medium">Questions</span>
                <span className="font-bold text-ink-800 dark:text-ink-200">{selectedAssessmentDetail.question_count}</span>
              </div>
              <div>
                <span className="text-ink-400 block font-medium">Pass Threshold</span>
                <span className="font-bold text-ink-800 dark:text-ink-200">{selectedAssessmentDetail.pass_percentage}%</span>
              </div>
              <div>
                <span className="text-ink-400 block font-medium">Average Score</span>
                <span className="font-bold text-brand-600 dark:text-brand-400">{selectedAssessmentDetail.average_score}%</span>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-bold text-ink-900 dark:text-ink-100 mb-3">
                Student Submissions ({selectedAssessmentDetail.submissions?.length || 0})
              </h4>

              {!selectedAssessmentDetail.submissions || selectedAssessmentDetail.submissions.length === 0 ? (
                <p className="text-xs text-ink-500 dark:text-ink-400 py-4 text-center">
                  No students have completed this assessment yet.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-ink-200 text-ink-400 dark:border-ink-800 font-semibold">
                        <th className="pb-2">Student</th>
                        <th className="pb-2">Score</th>
                        <th className="pb-2">Outcome</th>
                        <th className="pb-2">Time Spent</th>
                        <th className="pb-2 text-right">Date</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-ink-100 dark:divide-ink-800/50">
                      {selectedAssessmentDetail.submissions.map((sub) => (
                        <tr key={sub.id}>
                          <td className="py-2.5 font-medium text-ink-900 dark:text-ink-100">
                            {sub.student_name}
                          </td>
                          <td className="py-2.5 font-bold text-ink-900 dark:text-ink-100">
                            {sub.score}/{sub.total_points} ({sub.percentage}%)
                          </td>
                          <td className="py-2.5">
                            {sub.passed ? (
                              <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-semibold">
                                <CheckCircle2 size={12} /> Passed
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-rose-600 dark:text-rose-400 font-semibold">
                                <XCircle size={12} /> Failed
                              </span>
                            )}
                          </td>
                          <td className="py-2.5 text-ink-500">
                            {Math.floor((sub.time_spent_seconds || 0) / 60)}m {(sub.time_spent_seconds || 0) % 60}s
                          </td>
                          <td className="py-2.5 text-right text-ink-400">
                            {sub.submitted_at ? new Date(sub.submitted_at).toLocaleDateString() : 'N/A'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        ) : null}
      </Modal>

      {/* Assign Assessment Modal */}
      <Modal
        isOpen={assignModalOpen}
        onClose={() => setAssignModalOpen(false)}
        title="Assign Assessment to Cohort"
        size="md"
      >
        <form onSubmit={handleAssignSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-ink-700 dark:text-ink-300 mb-1.5">
              Assignee
            </label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="assign_target"
                  checked={assignToAll}
                  onChange={() => setAssignToAll(true)}
                  className="text-brand-600"
                />
                <span>Entire Enrolled Class ({students.length} students)</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="assign_target"
                  checked={!assignToAll}
                  onChange={() => setAssignToAll(false)}
                  className="text-brand-600"
                />
                <span>Specific Student</span>
              </label>
            </div>
          </div>

          {!assignToAll && (
            <div>
              <label className="block font-semibold text-ink-700 dark:text-ink-300 mb-1">
                Select Student
              </label>
              <select
                value={assignStudentId}
                onChange={(e) => setAssignStudentId(e.target.value)}
                required={!assignToAll}
                className="w-full rounded-xl border border-ink-200 bg-white p-2.5 text-xs text-ink-900 focus:outline-none dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
              >
                <option value="">-- Choose a student --</option>
                {students.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.email}) - Mastery: {s.overall_mastery}%
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block font-semibold text-ink-700 dark:text-ink-300 mb-1">
              Due Date & Time (Optional)
            </label>
            <input
              type="datetime-local"
              value={assignDueDate}
              onChange={(e) => setAssignDueDate(e.target.value)}
              className="w-full rounded-xl border border-ink-200 bg-white p-2.5 text-xs text-ink-900 focus:outline-none dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
            />
          </div>

          <div>
            <label className="block font-semibold text-ink-700 dark:text-ink-300 mb-1">
              Special Instructions (Optional)
            </label>
            <textarea
              rows={3}
              value={assignInstructions}
              onChange={(e) => setAssignInstructions(e.target.value)}
              placeholder="e.g. Please review lecture slides on Coffman conditions before starting..."
              className="w-full rounded-xl border border-ink-200 bg-white p-2.5 text-xs text-ink-900 focus:outline-none dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-ink-100 dark:border-ink-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setAssignModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={assigning}
            >
              {assigning ? <LoadingSpinner size={14} /> : <Share2 size={14} />}
              Confirm Assignment
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

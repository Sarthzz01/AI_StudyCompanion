import { useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { ChevronLeft, ChevronRight, Send, Clock, BookOpen } from 'lucide-react'
import Card from '../components/Card.jsx'
import Button from '../components/Button.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import QuizCard from '../components/QuizCard.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import ErrorState from '../components/ErrorState.jsx'
import Modal from '../components/Modal.jsx'
import {
  generateQuiz,
  submitQuiz,
  getMaterial,
  getStudentAssessment,
  submitStudentAssessment,
} from '../services/api.js'
import { useStudyData } from '../context/StudyDataContext.jsx'
import { useToast } from '../context/ToastContext.jsx'

export default function QuizAttempt() {
  const { id } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const toast = useToast()
  const { recordQuizAttempt } = useStudyData()

  // Assessment mode params
  const assessmentId = searchParams.get('assessment')
  const assignmentId = searchParams.get('assignment')

  // Practice quiz params
  const materialId = searchParams.get('material') || 'data-structures'
  const topic = searchParams.get('topic') || 'All topics'
  const difficulty = searchParams.get('difficulty') || 'mixed'
  const count = Number(searchParams.get('count') || 5)

  const [questions, setQuestions] = useState([])
  const [material, setMaterial] = useState(null)
  const [assessmentMeta, setAssessmentMeta] = useState(null)
  const [answers, setAnswers] = useState({}) // questionId -> option index
  const [current, setCurrent] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [attemptId, setAttemptId] = useState(null)
  const [startTime] = useState(() => Date.now())

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      if (assessmentId) {
        // Instructor Assigned Assessment Mode
        const assData = await getStudentAssessment(assessmentId)
        setAssessmentMeta(assData)
        const qs = (assData.questions || []).map((q, idx) => ({
          id: q.id || idx + 1,
          question: q.question_text || q.question,
          options: q.options || [],
          topic: assData.topic,
          points: q.points || 10,
        }))
        setQuestions(qs)
        setMaterial({ title: assData.title, isAssessment: true })
        setAnswers({})
        setCurrent(0)
      } else {
        // Self-Study Practice Quiz Mode
        const [qs, m] = await Promise.all([
          generateQuiz({ materialId, topic, difficulty, count }),
          getMaterial(materialId),
        ])
        setQuestions(qs)
        setAttemptId(qs.attemptId || null)
        setMaterial(m)
        setAnswers({})
        setCurrent(0)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, assessmentId, materialId, topic, difficulty, count])

  const select = (optionIndex) => {
    const question = questions[current]
    setAnswers((a) => ({ ...a, [question.id]: optionIndex }))
  }

  const finish = async () => {
    setSubmitting(true)

    if (assessmentId) {
      // Submitting an Assigned Assessment
      const timeSpentSeconds = Math.max(1, Math.floor((Date.now() - startTime) / 1000))
      const payload = {
        assignment_id: assignmentId ? Number(assignmentId) : null,
        time_spent_seconds: timeSpentSeconds,
        answers: questions.map((q) => ({
          question_id: Number(q.id),
          selected_option: answers[q.id] !== undefined ? Number(answers[q.id]) : -1,
        })),
      }

      try {
        const subResult = await submitStudentAssessment(assessmentId, payload)
        const attempt = {
          id: `submission-${subResult.id}`,
          assessmentId: Number(assessmentId),
          materialTitle: assessmentMeta?.title || 'Assigned Assessment',
          topic: assessmentMeta?.topic || 'Assessment',
          difficulty: assessmentMeta?.difficulty || 'medium',
          score: subResult.score,
          total: subResult.total_points,
          accuracy: subResult.percentage,
          passed: subResult.passed,
          date: new Date().toISOString().slice(0, 10),
          review: questions.map((q) => {
            const graded = (subResult.answers || []).find((a) => a.question_id === q.id)
            return {
              id: q.id,
              question: q.question,
              topic: q.topic,
              options: q.options,
              selected: answers[q.id] ?? null,
              answer: graded?.correct_answer ?? null,
              correct: graded ? graded.is_correct : false,
              explanation: graded?.explanation || 'Graded by instructor criteria.',
            }
          }),
        }
        await recordQuizAttempt(attempt)
        toast('Assessment submitted successfully!', 'success')
        navigate('/quiz-result', { state: { attempt } })
      } catch (err) {
        toast(err.message || 'The assessment could not be submitted. Try again.', 'error')
      } finally {
        setSubmitting(false)
        setConfirmOpen(false)
      }
      return
    }

    // Submitting a Self-Study Practice Quiz
    const review = questions.map((q) => ({
      id: q.id,
      question: q.question,
      topic: q.topic,
      options: q.options,
      selected: answers[q.id] ?? null,
      answer: q.answer,
      correct: answers[q.id] === q.answer,
      explanation: q.explanation,
    }))

    const score = review.filter((r) => r.correct).length
    const total = review.length

    // Per-topic tally drives the strong/weak lists and progress charts.
    const topicResults = {}
    review.forEach((r) => {
      topicResults[r.topic] = topicResults[r.topic] || { correct: 0, total: 0 }
      topicResults[r.topic].total += 1
      if (r.correct) topicResults[r.topic].correct += 1
    })

    const strongTopics = Object.entries(topicResults)
      .filter(([, v]) => v.correct / v.total >= 0.7)
      .map(([t]) => t)
    const weakTopics = Object.entries(topicResults)
      .filter(([, v]) => v.correct / v.total < 0.7)
      .map(([t]) => t)

    const attempt = {
      attemptId,
      id: attemptId ? String(attemptId) : `attempt-${Date.now()}`,
      materialId,
      materialTitle: material?.title || 'Study material',
      topic,
      difficulty,
      score,
      total,
      accuracy: total > 0 ? Math.round((score / total) * 100) : 0,
      date: new Date().toISOString().slice(0, 10),
      topicResults,
      strongTopics,
      weakTopics,
      review,
    }

    try {
      const serverResult = await submitQuiz(attempt)
      const finalAttempt = serverResult && serverResult.review ? serverResult : attempt
      await recordQuizAttempt(finalAttempt)
      navigate('/quiz-result', { state: { attempt: finalAttempt } })
    } catch (err) {
      toast(err.message || 'The quiz could not be submitted. Try again.', 'error')
    } finally {
      setSubmitting(false)
      setConfirmOpen(false)
    }
  }

  if (loading) {
    return (
      <LoadingSpinner
        label={assessmentId ? 'Preparing your official assessment questions…' : 'Generating your questions…'}
      />
    )
  }
  if (error) return <ErrorState message={error} onRetry={load} />

  const question = questions[current]
  const answeredCount = Object.keys(answers).length
  const isLast = current === questions.length - 1

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            {assessmentId && (
              <span className="flex items-center gap-1 rounded-md bg-brand-50 px-2 py-0.5 text-xs font-bold text-brand-700 dark:bg-brand-950/80 dark:text-brand-300">
                <BookOpen size={12} /> Assigned Assessment
              </span>
            )}
            <h1 className="font-display text-xl font-semibold">{material?.title}</h1>
          </div>
          <p className="muted mt-0.5 text-xs">
            {assessmentId ? (
              <>
                {assessmentMeta?.topic} &middot; {assessmentMeta?.difficulty} &middot; {questions.length} questions
                {assessmentMeta?.time_limit_minutes ? ` &middot; ${assessmentMeta.time_limit_minutes}m time limit` : ''}
              </>
            ) : (
              <>
                {topic} &middot; {difficulty} &middot; {questions.length} questions
              </>
            )}
          </p>
        </div>
        <span className="chip bg-ink-100 text-ink-600 dark:bg-ink-800 dark:text-ink-300">
          {answeredCount}/{questions.length} answered
        </span>
      </div>

      <ProgressBar value={((current + 1) / questions.length) * 100} size="sm" />

      <Card className="mt-6">
        <QuizCard
          question={question}
          index={current}
          total={questions.length}
          selected={answers[question?.id] ?? null}
          onSelect={select}
        />
      </Card>

      <div className="mt-6 flex items-center justify-between gap-3">
        <Button variant="secondary" icon={ChevronLeft} onClick={() => setCurrent((c) => c - 1)} disabled={current === 0}>
          Previous
        </Button>

        {isLast ? (
          <Button icon={Send} onClick={() => setConfirmOpen(true)} disabled={answeredCount === 0}>
            {assessmentId ? 'Submit Assessment' : 'Submit quiz'}
          </Button>
        ) : (
          <Button variant="secondary" onClick={() => setCurrent((c) => c + 1)}>
            Next
            <ChevronRight size={16} />
          </Button>
        )}
      </div>

      {/* Question jump list */}
      <div className="mt-6 flex flex-wrap gap-2">
        {questions.map((q, i) => (
          <button
            key={q.id}
            onClick={() => setCurrent(i)}
            aria-label={`Go to question ${i + 1}`}
            className={`h-9 w-9 rounded-lg text-sm font-medium transition-colors ${
              i === current
                ? 'bg-brand-600 text-white'
                : answers[q.id] !== undefined
                  ? 'bg-brand-100 text-brand-700 dark:bg-brand-900/60 dark:text-brand-200'
                  : 'bg-ink-100 text-ink-600 dark:bg-ink-800 dark:text-ink-400'
            }`}
          >
            {i + 1}
          </button>
        ))}
      </div>

      <Modal
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        title={assessmentId ? 'Submit this assessment?' : 'Submit this quiz?'}
        description={
          answeredCount < questions.length
            ? `${questions.length - answeredCount} question(s) are still unanswered and will be marked wrong.`
            : assessmentId
              ? 'All questions are answered. Your assessment will be graded and submitted to your instructor.'
              : 'All questions are answered. Your score will be added to your progress.'
        }
        footer={
          <>
            <Button variant="secondary" onClick={() => setConfirmOpen(false)}>
              Keep working
            </Button>
            <Button onClick={finish} loading={submitting}>
              {assessmentId ? 'Confirm & Submit' : 'Submit quiz'}
            </Button>
          </>
        }
      />
    </div>
  )
}

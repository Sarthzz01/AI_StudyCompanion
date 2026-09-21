import { useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { ChevronLeft, ChevronRight, Send } from 'lucide-react'
import Card from '../components/Card.jsx'
import Button from '../components/Button.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import QuizCard from '../components/QuizCard.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import ErrorState from '../components/ErrorState.jsx'
import Modal from '../components/Modal.jsx'
import { generateQuiz, submitQuiz, getMaterial } from '../services/api.js'
import { useStudyData } from '../context/StudyDataContext.jsx'
import { useToast } from '../context/ToastContext.jsx'

export default function QuizAttempt() {
  const { id } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const toast = useToast()
  const { recordQuizAttempt } = useStudyData()

  const materialId = searchParams.get('material') || 'data-structures'
  const topic = searchParams.get('topic') || 'All topics'
  const difficulty = searchParams.get('difficulty') || 'mixed'
  const count = Number(searchParams.get('count') || 5)

  const [questions, setQuestions] = useState([])
  const [material, setMaterial] = useState(null)
  const [answers, setAnswers] = useState({}) // questionId -> option index
  const [current, setCurrent] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [attemptId, setAttemptId] = useState(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const [qs, m] = await Promise.all([
        generateQuiz({ materialId, topic, difficulty, count }),
        getMaterial(materialId),
      ])
      setQuestions(qs)
      setAttemptId(qs.attemptId || null)
      setMaterial(m)
      setAnswers({})
      setCurrent(0)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, materialId, topic, difficulty, count])

  const select = (optionIndex) => {
    const question = questions[current]
    setAnswers((a) => ({ ...a, [question.id]: optionIndex }))
  }

  const finish = async () => {
    setSubmitting(true)
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

    // Per-topic tally drives the strong/weak lists and the progress charts.
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

  if (loading) return <LoadingSpinner label="Generating your questions…" />
  if (error) return <ErrorState message={error} onRetry={load} />

  const question = questions[current]
  const answeredCount = Object.keys(answers).length
  const isLast = current === questions.length - 1

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="font-display text-xl font-semibold">{material?.title}</h1>
          <p className="muted">
            {topic} · {difficulty} · {questions.length} questions
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
          selected={answers[question.id] ?? null}
          onSelect={select}
        />
      </Card>

      <div className="mt-6 flex items-center justify-between gap-3">
        <Button variant="secondary" icon={ChevronLeft} onClick={() => setCurrent((c) => c - 1)} disabled={current === 0}>
          Previous
        </Button>

        {isLast ? (
          <Button icon={Send} onClick={() => setConfirmOpen(true)} disabled={answeredCount === 0}>
            Submit quiz
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
        title="Submit this quiz?"
        description={
          answeredCount < questions.length
            ? `${questions.length - answeredCount} question(s) are still unanswered and will be marked wrong.`
            : 'All questions are answered. Your score will be added to your progress.'
        }
        footer={
          <>
            <Button variant="secondary" onClick={() => setConfirmOpen(false)}>
              Keep working
            </Button>
            <Button onClick={finish} loading={submitting}>
              Submit quiz
            </Button>
          </>
        }
      />
    </div>
  )
}

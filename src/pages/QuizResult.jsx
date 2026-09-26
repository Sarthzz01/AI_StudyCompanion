import { Link, useLocation, useNavigate } from 'react-router-dom'
import { CheckCircle2, XCircle, TrendingUp, RotateCcw, LayoutDashboard } from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import Card, { CardHeader } from '../components/Card.jsx'
import Button from '../components/Button.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import EmptyState from '../components/EmptyState.jsx'
import { useStudyData } from '../context/StudyDataContext.jsx'

export default function QuizResult() {
  const location = useLocation()
  const navigate = useNavigate()
  const { lastAttempt } = useStudyData()

  // Prefer the attempt passed through navigation; fall back to the stored one after a refresh.
  const attempt = location.state?.attempt || lastAttempt

  if (!attempt) {
    return (
      <EmptyState
        icon={TrendingUp}
        title="No quiz result to show"
        description="Attempt a quiz and your score breakdown will appear here."
        actionLabel="Go to quizzes"
        onAction={() => navigate('/quizzes')}
      />
    )
  }

  const incorrect = attempt.total - attempt.score
  const passed = attempt.accuracy >= 70

  const matTitle = attempt.materialTitle || attempt.material_title || 'Study material'

  return (
    <>
      <PageHeader title="Quiz result" subtitle={`${matTitle} · ${attempt.topic}`} />

      <div className="grid gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="flex flex-col items-center py-6 text-center">
            <p className="muted">You scored</p>
            <p className="mt-1 font-display text-5xl font-bold">
              {attempt.score} <span className="text-ink-400">/ {attempt.total}</span>
            </p>
            <p className={`mt-2 text-lg font-semibold ${passed ? 'text-emerald-600' : 'text-amber-600'}`}>
              {attempt.accuracy}% accuracy
            </p>
            <div className="mt-5 w-full max-w-sm">
              <ProgressBar value={attempt.accuracy} tone={passed ? 'emerald' : 'amber'} />
            </div>
            <p className="muted mt-4 max-w-md">
              {passed
                ? 'Solid attempt. Keep the weaker topics below in your next session.'
                : 'Worth another pass. The topics below are where most marks were lost.'}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 border-t border-ink-200 pt-5 dark:border-ink-800">
            <div className="flex items-center gap-3">
              <CheckCircle2 size={20} className="text-emerald-600" />
              <div>
                <p className="muted">Correct</p>
                <p className="text-lg font-semibold">{attempt.score}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <XCircle size={20} className="text-rose-600" />
              <div>
                <p className="muted">Incorrect</p>
                <p className="text-lg font-semibold">{incorrect}</p>
              </div>
            </div>
          </div>
        </Card>

        <Card className="h-fit">
          <CardHeader title="Topic breakdown" />
          <div className="space-y-4">
            <div>
              <p className="mb-2 text-sm font-medium text-emerald-600">Strong</p>
              {attempt.strongTopics?.length ? (
                <div className="flex flex-wrap gap-2">
                  {attempt.strongTopics.map((t) => (
                    <span key={t} className="chip bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300">
                      {t}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="muted">Nothing above 70% this time.</p>
              )}
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-rose-600">Needs practice</p>
              {attempt.weakTopics?.length ? (
                <div className="flex flex-wrap gap-2">
                  {attempt.weakTopics.map((t) => (
                    <span key={t} className="chip bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300">
                      {t}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="muted">Every topic cleared 70%.</p>
              )}
            </div>
          </div>
        </Card>

        {attempt.review?.length > 0 && (
          <Card className="lg:col-span-3">
            <CardHeader title="Answer review" subtitle="What was right, and why." />
            <div className="space-y-4">
              {attempt.review.map((item, i) => (
                <div
                  key={item.id}
                  className={`rounded-xl border p-4 ${
                    item.correct
                      ? 'border-emerald-200 bg-emerald-50/50 dark:border-emerald-900 dark:bg-emerald-950/20'
                      : 'border-rose-200 bg-rose-50/50 dark:border-rose-900 dark:bg-rose-950/20'
                  }`}
                >
                  <div className="flex items-start gap-2.5">
                    {item.correct ? (
                      <CheckCircle2 size={18} className="mt-0.5 shrink-0 text-emerald-600" />
                    ) : (
                      <XCircle size={18} className="mt-0.5 shrink-0 text-rose-600" />
                    )}
                    <div>
                      <p className="text-sm font-semibold">
                        {i + 1}. {item.question}
                      </p>
                      <p className="muted mt-1.5">
                        Your answer: {item.selected === null ? 'Not answered' : item.options[item.selected]}
                      </p>
                      {!item.correct && (
                        <p className="mt-1 text-sm font-medium text-emerald-700 dark:text-emerald-300">
                          Correct answer: {item.options[item.answer]}
                        </p>
                      )}
                      <p className="muted mt-2">{item.explanation}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <Link to="/progress">
          <Button icon={TrendingUp}>View progress</Button>
        </Link>
        <Button
          variant="secondary"
          icon={RotateCcw}
          onClick={() =>
            navigate(
              `/quizzes/retry?material=${attempt.materialId}&topic=${encodeURIComponent(attempt.topic)}&difficulty=${attempt.difficulty}&count=${attempt.total}`
            )
          }
        >
          Try again
        </Button>
        <Link to="/dashboard">
          <Button variant="ghost" icon={LayoutDashboard}>
            Back to dashboard
          </Button>
        </Link>
      </div>
    </>
  )
}

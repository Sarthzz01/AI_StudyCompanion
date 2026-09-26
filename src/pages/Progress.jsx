import { useEffect, useState } from 'react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts'
import { Link } from 'react-router-dom'
import { Percent, ListChecks, Clock, CheckCircle2, ArrowUpRight, Layers, Brain, CalendarClock, Mic, Sparkles } from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import Card, { CardHeader } from '../components/Card.jsx'
import StatCard from '../components/StatCard.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import EmptyState from '../components/EmptyState.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import { useStudyData } from '../context/StudyDataContext.jsx'
import { formatMinutes } from '../utils/format.js'

const barColor = (accuracy) => (accuracy >= 75 ? '#10b981' : accuracy >= 50 ? '#f59e0b' : '#f43f5e')

export default function Progress() {
  const { progress, attempts, refreshProgress } = useStudyData()
  const [loading, setLoading] = useState(!progress || !progress.stats)

  useEffect(() => {
    refreshProgress().finally(() => setLoading(false))
  }, [refreshProgress])

  const stats = progress?.stats || {
    accuracy: 0,
    questionsAttempted: 0,
    studyMinutes: 0,
    topicsCompleted: 0,
    totalTopics: 0,
    overallProgress: 0,
    flashcardPerformance: 0,
    recallReliability: 50,
    averageMastery: 0,
  }

  const sortedTopics = [...(progress?.topicAccuracy || [])].sort((a, b) => b.accuracy - a.accuracy)
  const strong = sortedTopics.filter((t) => t.accuracy >= 75 || (t.mastery && t.mastery >= 75))
  const weak = sortedTopics.filter((t) => t.accuracy < 55 && (!t.mastery || t.mastery < 55))

  const quizPerformance = [...(attempts || [])]
    .slice(0, 8)
    .reverse()
    .map((a, i) => ({ name: `Quiz ${i + 1}`, accuracy: a.accuracy }))

  return (
    <>
      <PageHeader title="My progress" subtitle="Your own accuracy, topic by topic." />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-7">
        <StatCard icon={Percent} label="Quiz accuracy" value={`${stats.accuracy}%`} tone="brand" />
        <StatCard
          icon={Layers}
          label="Flashcard recall"
          value={stats.flashcardPerformance > 0 ? `${stats.flashcardPerformance}%` : '—'}
          tone="emerald"
        />
        <StatCard
          icon={Brain}
          label="Recall reliability"
          value={`${stats.recallReliability || 50}%`}
          tone="purple"
        />
        <StatCard
          icon={Mic}
          label="AI Viva score"
          value={stats.averageVivaScore > 0 ? `${Math.round(stats.averageVivaScore)}%` : (stats.vivaSessionsCount > 0 ? 'Completed' : '—')}
          tone="rose"
        />
        <StatCard icon={ListChecks} label="Questions attempted" value={stats.questionsAttempted} tone="brand" />
        <StatCard icon={Clock} label="Study time" value={formatMinutes(stats.studyMinutes)} tone="amber" />
        <StatCard
          icon={CheckCircle2}
          label="Topics completed"
          value={`${stats.topicsCompleted}/${stats.totalTopics}`}
          tone="sky"
        />
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader title="Performance over time" subtitle="Accuracy from each study session" />
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={progress?.performanceOverTime || []} margin={{ top: 5, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#94a3b8" tickLine={false} axisLine={false} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} stroke="#94a3b8" tickLine={false} axisLine={false} />
                <Tooltip formatter={(v) => [`${v}%`, 'Accuracy']} />
                <Line type="monotone" dataKey="accuracy" stroke="#4f46e5" strokeWidth={2.5} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <CardHeader title="Topic-wise accuracy" subtitle="Where marks are being won and lost" />
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sortedTopics} margin={{ top: 5, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="topic" tick={{ fontSize: 10 }} stroke="#94a3b8" tickLine={false} axisLine={false} interval={0} angle={-18} textAnchor="end" height={60} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} stroke="#94a3b8" tickLine={false} axisLine={false} />
                <Tooltip
                  formatter={(v, name, item) => [
                    `${v}% (Mastery: ${item?.payload?.mastery ?? v}%)`,
                    'Quiz Accuracy'
                  ]}
                />
                <Bar dataKey="accuracy" radius={[6, 6, 0, 0]}>
                  {sortedTopics.map((t) => (
                    <Cell key={t.topic} fill={barColor(t.accuracy)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <CardHeader title="Quiz performance" subtitle="Your most recent attempts" />
          {quizPerformance.length === 0 ? (
            <EmptyState icon={Percent} title="No attempts yet" description="Take a quiz and the trend will build here." />
          ) : (
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={quizPerformance} margin={{ top: 5, right: 8, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} stroke="#94a3b8" tickLine={false} axisLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} stroke="#94a3b8" tickLine={false} axisLine={false} />
                  <Tooltip formatter={(v) => [`${v}%`, 'Accuracy']} />
                  <Bar dataKey="accuracy" fill="#6366f1" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>

        <Card>
          <CardHeader title="Study time this week" subtitle="Minutes per day" />
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={progress?.weeklyStudy || []} margin={{ top: 5, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="day" tick={{ fontSize: 12 }} stroke="#94a3b8" tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" tickLine={false} axisLine={false} />
                <Tooltip formatter={(v) => [`${v} min`, 'Studied']} />
                <Bar dataKey="minutes" fill="#0ea5e9" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <CardHeader title="Strong topics" subtitle="75% and above" />
          {strong.length === 0 ? (
            <p className="muted">Nothing above 75% yet. Keep practising.</p>
          ) : (
            <div className="space-y-4">
              {strong.map((t) => (
                <div key={t.topic} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-ink-900 dark:text-ink-100">{t.topic}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-ink-500 dark:text-ink-400">
                        Quiz: <strong className="text-ink-700 dark:text-ink-200">{t.accuracy}%</strong>
                      </span>
                      <span className="text-ink-500 dark:text-ink-400">
                        Mastery: <strong className="text-emerald-600 dark:text-emerald-400">{t.mastery || t.accuracy}%</strong>
                      </span>
                    </div>
                  </div>
                  <ProgressBar label="" value={t.mastery || t.accuracy} tone="emerald" />
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <CardHeader title="Weak topics" subtitle="Below 55% — study these first" />
          {weak.length === 0 ? (
            <p className="muted">No weak topics right now.</p>
          ) : (
            <div className="space-y-4">
              {weak.map((t) => (
                <div key={t.topic} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-ink-900 dark:text-ink-100">{t.topic}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-ink-500 dark:text-ink-400">
                        Quiz: <strong className="text-ink-700 dark:text-ink-200">{t.accuracy}%</strong>
                      </span>
                      <span className="text-ink-500 dark:text-ink-400">
                        Mastery: <strong className="text-rose-600 dark:text-rose-400">{t.mastery || t.accuracy}%</strong>
                      </span>
                    </div>
                  </div>
                  <ProgressBar label="" value={t.mastery || t.accuracy} tone="rose" />
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <CardHeader title="Review due" subtitle="Topics needing spaced-repetition refresh" />
          {(progress?.topicsNeedingReview || []).length === 0 ? (
            <p className="muted">All topics up to date. No reviews currently overdue.</p>
          ) : (
            <div className="space-y-3">
              {(progress?.topicsNeedingReview || []).map((item) => (
                <div
                  key={item.topic}
                  className="flex items-center justify-between rounded-xl border border-ink-100 bg-ink-50/50 p-3.5 dark:border-ink-800 dark:bg-ink-900/30"
                >
                  <div>
                    <p className="text-sm font-semibold text-ink-900 dark:text-ink-100">{item.topic}</p>
                    <p className="text-xs text-ink-500 dark:text-ink-400">
                      Recall probability: {Math.round((item.recall_reliability ?? 0.5) * 100)}%
                    </p>
                  </div>
                  <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-700 dark:bg-amber-950/40 dark:text-amber-400">
                    Due: {item.next_review || 'Overdue'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <CardHeader title="Recently improved" subtitle="Change in accuracy over the last two weeks" />
          {(progress?.recentlyImproved || []).length === 0 ? (
            <p className="muted">Take quizzes across multiple study sessions to build improvement trends.</p>
          ) : (
            <div className="space-y-3">
              {(progress?.recentlyImproved || []).map((t) => (
                <div key={t.topic} className="flex items-center justify-between rounded-xl border border-ink-100 p-3.5 dark:border-ink-800">
                  <p className="text-sm font-semibold text-ink-900 dark:text-ink-100">{t.topic}</p>
                  <p className="inline-flex items-center gap-1 text-sm font-medium text-emerald-600 dark:text-emerald-400">
                    <ArrowUpRight size={15} /> +{t.change}%
                  </p>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between border-b border-ink-100 pb-4 dark:border-ink-800">
            <div>
              <h3 className="font-semibold text-ink-900 dark:text-ink-100">AI Viva & Technical Interview Performance</h3>
              <p className="muted text-xs">Oral examination scores and diagnostic reports</p>
            </div>
            <Link
              to="/viva"
              className="inline-flex items-center gap-1.5 rounded-lg bg-brand-50 px-3 py-1.5 text-xs font-semibold text-brand-700 hover:bg-brand-100 dark:bg-brand-950/40 dark:text-brand-300 dark:hover:bg-brand-900/60"
            >
              <Mic size={14} /> Practice Viva
            </Link>
          </div>
          {(progress?.vivaPerformance || []).length === 0 ? (
            <div className="py-6 text-center">
              <p className="text-sm text-ink-500 dark:text-ink-400">No Viva sessions completed yet.</p>
              <p className="mt-1 text-xs text-ink-400">Practice viva voce or mock technical interviews with the AI examiner to build oral communication skills.</p>
            </div>
          ) : (
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {(progress?.vivaPerformance || []).map((v) => (
                <div
                  key={v.id}
                  className="flex flex-col justify-between rounded-xl border border-ink-100 bg-ink-50/40 p-3.5 dark:border-ink-800 dark:bg-ink-900/40"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-sm font-semibold text-ink-900 dark:text-ink-100">{v.topic}</p>
                      <span className="mt-1 inline-block rounded-md bg-brand-100/70 px-2 py-0.5 text-[10px] font-medium capitalize text-brand-800 dark:bg-brand-950/60 dark:text-brand-300">
                        {v.mode} Viva
                      </span>
                    </div>
                    <span
                      className={`text-sm font-bold ${
                        v.score >= 75
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : v.score >= 50
                          ? 'text-amber-600 dark:text-amber-400'
                          : 'text-rose-600 dark:text-rose-400'
                      }`}
                    >
                      {Math.round(v.score)}%
                    </span>
                  </div>
                  <div className="mt-3 flex items-center justify-between text-xs text-ink-400">
                    <span>{v.date}</span>
                    <Link to={`/viva`} className="text-brand-600 hover:underline dark:text-brand-400">
                      View report &rarr;
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </>
  )
}


import { Link } from 'react-router-dom'
import {
  GraduationCap,
  Bot,
  FileText,
  Layers,
  ClipboardCheck,
  TrendingUp,
  Sparkles,
  ArrowRight,
  Upload,
  BrainCircuit,
  LineChart,
} from 'lucide-react'
import Button from '../components/Button.jsx'

const features = [
  {
    icon: Bot,
    title: 'AI Tutor',
    body: 'Ask a question in plain language and get an answer grounded in your own uploaded material, with the page it came from.',
  },
  {
    icon: FileText,
    title: 'Smart Summaries',
    body: 'Turn a 200-page PDF into structured sections, key concepts and the points worth revising.',
  },
  {
    icon: Layers,
    title: 'Flashcards',
    body: 'Auto-generated cards you can flip and rate, so the ones you keep forgetting come back more often.',
  },
  {
    icon: ClipboardCheck,
    title: 'Adaptive Quizzes',
    body: 'Pick a topic and difficulty, or let the difficulty follow your recent accuracy.',
  },
  {
    icon: TrendingUp,
    title: 'Performance Tracking',
    body: 'Accuracy over time, topic by topic, so weak areas are obvious before the exam is.',
  },
  {
    icon: Sparkles,
    title: 'Personalised Learning',
    body: 'Recommendations that come from your own results rather than a generic study plan.',
  },
]

const steps = [
  { icon: Upload, title: 'Add your material', body: 'Upload a PDF, notes or slides, or pick a subject already in your library.' },
  { icon: BrainCircuit, title: 'Let the AI process it', body: 'Topics are extracted and turned into summaries, flashcards and questions.' },
  { icon: LineChart, title: 'Study and track', body: 'Attempt quizzes, watch accuracy move, and follow the recommendations that follow.' },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-white dark:bg-ink-950">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5">
        <div className="flex items-center gap-2.5">
          <span className="rounded-lg bg-brand-600 p-1.5 text-white">
            <GraduationCap size={18} />
          </span>
          <span className="font-display text-base font-semibold">AI Study Companion</span>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/login">
            <Button variant="ghost" size="sm">Log in</Button>
          </Link>
          <Link to="/signup">
            <Button size="sm">Get started</Button>
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="mx-auto max-w-6xl px-4 pb-16 pt-10 sm:pt-20">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <div>
            <span className="chip bg-brand-50 text-brand-700 dark:bg-brand-900/50 dark:text-brand-300">
              <Sparkles size={13} /> Built for students
            </span>
            <h1 className="mt-5 font-display text-4xl font-bold leading-[1.1] sm:text-5xl">
              Study from your own material, with an AI that has actually read it.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-ink-600 dark:text-ink-400">
              Upload your syllabus, notes or textbook PDFs. AI Study Companion turns them into summaries,
              flashcards and quizzes, then tracks which topics you keep getting wrong and tells you what to
              study next.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/signup">
                <Button size="lg" icon={ArrowRight}>Get started</Button>
              </Link>
              <Link to="/login">
                <Button size="lg" variant="secondary">Log in</Button>
              </Link>
            </div>
            <p className="mt-4 text-xs text-ink-500">No card needed. Your material stays in your account.</p>
          </div>

          {/* A small live-looking preview stands in for a screenshot. */}
          <div className="rounded-2xl border border-ink-200 bg-ink-50 p-4 shadow-card dark:border-ink-800 dark:bg-ink-900">
            <div className="rounded-xl border border-ink-200 bg-white p-5 dark:border-ink-800 dark:bg-ink-950">
              <p className="muted">Your weakest topic this week</p>
              <p className="mt-1 font-display text-2xl font-semibold">Graph Traversal — 44%</p>
              <div className="mt-4 h-2.5 w-full rounded-full bg-ink-200 dark:bg-ink-800">
                <div className="h-full w-[44%] rounded-full bg-rose-500" />
              </div>
              <div className="mt-6 space-y-3">
                {['Practice 10 BFS and DFS questions', 'Review 6 flashcards on adjacency lists', 'Re-read section 4 of Data Structures.pdf'].map(
                  (item) => (
                    <div key={item} className="flex items-start gap-2.5 text-sm text-ink-700 dark:text-ink-300">
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-600" />
                      {item}
                    </div>
                  )
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="border-y border-ink-200 bg-ink-50 py-16 dark:border-ink-800 dark:bg-ink-900/40">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="font-display text-2xl font-semibold">Everything in one study loop</h2>
          <p className="muted mt-2 max-w-xl">
            Each feature feeds the next, so the more you study the better the recommendations get.
          </p>
          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {features.map(({ icon: Icon, title, body }) => (
              <div key={title} className="card">
                <span className="inline-flex rounded-xl bg-brand-50 p-2.5 text-brand-600 dark:bg-brand-900/40 dark:text-brand-300">
                  <Icon size={18} />
                </span>
                <h3 className="mt-4 text-base font-semibold">{title}</h3>
                <p className="muted mt-2 leading-relaxed">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works — a genuine three-step sequence, so numbering earns its place. */}
      <section className="mx-auto max-w-6xl px-4 py-16">
        <h2 className="font-display text-2xl font-semibold">How it works</h2>
        <ol className="mt-8 grid gap-6 sm:grid-cols-3">
          {steps.map(({ icon: Icon, title, body }, i) => (
            <li key={title} className="relative rounded-2xl border border-ink-200 p-5 dark:border-ink-800">
              <span className="font-display text-sm font-semibold text-brand-600">Step {i + 1}</span>
              <span className="mt-3 inline-flex rounded-xl bg-ink-100 p-2.5 text-ink-700 dark:bg-ink-800 dark:text-ink-200">
                <Icon size={18} />
              </span>
              <h3 className="mt-3 text-base font-semibold">{title}</h3>
              <p className="muted mt-2 leading-relaxed">{body}</p>
            </li>
          ))}
        </ol>
      </section>

      <footer className="border-t border-ink-200 py-8 dark:border-ink-800">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 text-sm text-ink-500 sm:flex-row">
          <div className="flex items-center gap-2">
            <GraduationCap size={16} />
            AI Study Companion
          </div>
          <p>A student project. Built with React, Vite and Tailwind CSS.</p>
        </div>
      </footer>
    </div>
  )
}

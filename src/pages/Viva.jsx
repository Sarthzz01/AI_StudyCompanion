import { useEffect, useState, useRef } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import {
  Mic,
  MicOff,
  BookOpen,
  Code2,
  Briefcase,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  Send,
  HelpCircle,
  Award,
  ArrowRight,
  TrendingUp,
  History,
  Clock,
  Layers,
  FileText,
  ChevronDown,
  ChevronUp,
  Bot,
  User,
  ShieldCheck,
  Zap,
} from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import Card, { CardHeader } from '../components/Card.jsx'
import StatCard from '../components/StatCard.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import Button from '../components/Button.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import ErrorState from '../components/ErrorState.jsx'
import EmptyState from '../components/EmptyState.jsx'
import {
  startVivaSession,
  submitVivaAnswer,
  endVivaSession,
  getVivaSession,
  getVivaHistory,
  getMaterials,
} from '../services/api.js'
import { useStudyData } from '../context/StudyDataContext.jsx'

const MODES = [
  {
    id: 'basic',
    name: 'Basic Viva',
    icon: BookOpen,
    badge: 'Foundation',
    badgeTone: 'emerald',
    description: 'Oral exam testing foundational definitions, core principles, and working mechanics.',
    color: 'border-emerald-200 dark:border-emerald-800/60 bg-emerald-50/40 dark:bg-emerald-950/20 text-emerald-700 dark:text-emerald-300',
  },
  {
    id: 'technical',
    name: 'Technical Viva',
    icon: Code2,
    badge: 'In-Depth',
    badgeTone: 'brand',
    description: 'Rigorous technical probe into internal architectures, algorithmic complexities, edge cases, and trade-offs.',
    color: 'border-brand-200 dark:border-brand-800/60 bg-brand-50/40 dark:bg-brand-950/20 text-brand-700 dark:text-brand-300',
  },
  {
    id: 'interview',
    name: 'Technical Interview',
    icon: Briefcase,
    badge: 'Practical / Scenario',
    badgeTone: 'purple',
    description: 'Realistic engineering interview scenarios, system design, failure troubleshooting, and practical problem-solving.',
    color: 'border-purple-200 dark:border-purple-800/60 bg-purple-50/40 dark:bg-purple-950/20 text-purple-700 dark:text-purple-300',
  },
]

const DEFAULT_TOPICS = [
  'Routing Algorithms',
  'Deadlocks',
  'Graph Traversal',
  'Transactions & ACID',
  'Tree Traversal',
  'Process Synchronization',
  'Page Replacement',
  'Relational Algebra',
  'Application Protocols',
  'BST Operations',
]

export default function Viva() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { refreshProgress } = useStudyData()

  // Main UI State: 'setup' | 'session' | 'report' | 'history'
  const [viewState, setViewState] = useState('setup')
  const [materials, setMaterials] = useState([])
  const [topicOptions, setTopicOptions] = useState(DEFAULT_TOPICS)

  // Setup Form State
  const [selectedTopic, setSelectedTopic] = useState(searchParams.get('topic') || 'Routing Algorithms')
  const [selectedMode, setSelectedMode] = useState(searchParams.get('mode') || 'technical')
  const [selectedDifficulty, setSelectedDifficulty] = useState(searchParams.get('difficulty') || 'medium')
  const [selectedMaterialId, setSelectedMaterialId] = useState(searchParams.get('material') || '')
  const [totalQuestions, setTotalQuestions] = useState(4)

  // Live Session State
  const [sessionId, setSessionId] = useState(null)
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(1)
  const [sessionTotalQuestions, setSessionTotalQuestions] = useState(4)
  const [studentAnswer, setStudentAnswer] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [currentEvaluation, setCurrentEvaluation] = useState(null)
  const [hasNextQuestion, setHasNextQuestion] = useState(false)
  const [nextQuestionData, setNextQuestionData] = useState(null)
  const [isSessionComplete, setIsSessionComplete] = useState(false)

  // Final Report State
  const [sessionReport, setSessionReport] = useState(null)

  // History State
  const [historyData, setHistoryData] = useState({ total_sessions: 0, average_score: 0, sessions: [] })

  // UI Micro-states
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [isDictating, setIsDictating] = useState(false)
  const [showIdealHints, setShowIdealHints] = useState(false)
  const [expandedTranscripts, setExpandedTranscripts] = useState({})

  const answerInputRef = useRef(null)

  // Fetch initial materials & history
  useEffect(() => {
    async function init() {
      try {
        const mats = await getMaterials()
        setMaterials(mats || [])

        // Extract all topics from materials
        const extracted = new Set(DEFAULT_TOPICS)
        mats.forEach((m) => {
          if (m.topics_json && Array.isArray(m.topics_json)) {
            m.topics_json.forEach((t) => {
              if (t.name) extracted.add(t.name)
            })
          }
        })
        setTopicOptions(Array.from(extracted))

        const hist = await getVivaHistory()
        setHistoryData(hist)
      } catch (err) {
        console.warn('Initial viva setup fetch warning:', err)
      }
    }
    init()
  }, [])

  // Auto-fill from URL params if present
  useEffect(() => {
    const urlTopic = searchParams.get('topic')
    const urlMode = searchParams.get('mode')
    const urlDiff = searchParams.get('difficulty')
    const urlMat = searchParams.get('material')

    if (urlTopic) setSelectedTopic(urlTopic)
    if (urlMode) setSelectedMode(urlMode)
    if (urlDiff) setSelectedDifficulty(urlDiff)
    if (urlMat) setSelectedMaterialId(urlMat)
  }, [searchParams])

  // Handle Speech / Dictation Simulation
  const toggleDictation = () => {
    if (!isDictating) {
      // Check for browser speech recognition
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
        const recognition = new SpeechRecognition()
        recognition.continuous = true
        recognition.interimResults = true
        recognition.lang = 'en-US'

        recognition.onstart = () => setIsDictating(true)
        recognition.onresult = (event) => {
          let transcript = ''
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            transcript += event.results[i][0].transcript
          }
          setStudentAnswer((prev) => (prev ? `${prev} ${transcript}` : transcript))
        }
        recognition.onerror = () => setIsDictating(false)
        recognition.onend = () => setIsDictating(false)

        recognition.start()
        window._vivaRecognition = recognition
      } else {
        setIsDictating(true)
        setTimeout(() => setIsDictating(false), 3000)
      }
    } else {
      if (window._vivaRecognition) {
        window._vivaRecognition.stop()
      }
      setIsDictating(false)
    }
  }

  // Start Session Action
  const handleStartSession = async () => {
    if (!selectedTopic) {
      setError('Please select or specify a topic to practice.')
      return
    }

    setLoading(true)
    setError(null)
    try {
      const data = await startVivaSession({
        topic: selectedTopic,
        mode: selectedMode,
        difficulty: selectedDifficulty,
        material_id: selectedMaterialId || null,
        total_questions: totalQuestions,
      })

      setSessionId(data.session_id)
      setCurrentQuestion(data.current_question)
      setCurrentQuestionIndex(data.current_question_index)
      setSessionTotalQuestions(data.total_questions)
      setStudentAnswer('')
      setCurrentEvaluation(null)
      setHasNextQuestion(false)
      setNextQuestionData(null)
      setIsSessionComplete(false)
      setViewState('session')
      setShowIdealHints(false)
    } catch (err) {
      setError(err.message || 'Failed to start viva session.')
    } finally {
      setLoading(false)
    }
  }

  // Submit Answer Action
  const handleSubmitAnswer = async (e) => {
    if (e) e.preventDefault()
    if (!studentAnswer.trim() || studentAnswer.trim().length < 5) {
      setError('Please provide a substantive answer (at least 5 characters).')
      return
    }

    setIsSubmitting(true)
    setError(null)
    try {
      const result = await submitVivaAnswer(sessionId, {
        question_id: currentQuestion.id,
        answer_text: studentAnswer,
      })

      setCurrentEvaluation(result.evaluation)
      setHasNextQuestion(result.has_next_question)
      setNextQuestionData(result.next_question)
      setIsSessionComplete(result.is_session_complete)
    } catch (err) {
      setError(err.message || 'Failed to evaluate your answer.')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Advance to Next Question
  const handleProceedNext = () => {
    if (nextQuestionData) {
      setCurrentQuestion(nextQuestionData)
      setCurrentQuestionIndex((prev) => prev + 1)
      setStudentAnswer('')
      setCurrentEvaluation(null)
      setHasNextQuestion(false)
      setNextQuestionData(null)
      setShowIdealHints(false)
      if (answerInputRef.current) {
        answerInputRef.current.focus()
      }
    }
  }

  // Finalize Session Action
  const handleEndSession = async () => {
    setLoading(true)
    setError(null)
    try {
      const report = await endVivaSession(sessionId)
      setSessionReport(report)
      setViewState('report')
      refreshProgress?.()

      // Refresh history
      const hist = await getVivaHistory()
      setHistoryData(hist)
    } catch (err) {
      setError(err.message || 'Failed to finalize viva session.')
    } finally {
      setLoading(false)
    }
  }

  // View Past Session from History
  const handleViewHistoricalSession = async (sId) => {
    setLoading(true)
    setError(null)
    try {
      const report = await getVivaSession(sId)
      setSessionReport(report)
      setViewState('report')
    } catch (err) {
      setError(err.message || 'Failed to load past viva report.')
    } finally {
      setLoading(false)
    }
  }

  const toggleTranscript = (index) => {
    setExpandedTranscripts((prev) => ({
      ...prev,
      [index]: !prev[index],
    }))
  }

  const wordCount = studentAnswer.trim() ? studentAnswer.trim().split(/\s+/).length : 0

  return (
    <div className="space-y-6 pb-12">
      <PageHeader
        title="AI Viva & Technical Interview"
        subtitle="Interactive oral examinations, technical deep dives, and scenario-based interview practice with instant AI evaluation."
        actions={
          viewState !== 'session' && (
            <div className="flex items-center gap-2">
              <Button
                variant={viewState === 'setup' ? 'primary' : 'secondary'}
                size="sm"
                onClick={() => setViewState('setup')}
              >
                <Zap size={15} />
                New Session
              </Button>
              <Button
                variant={viewState === 'history' ? 'primary' : 'secondary'}
                size="sm"
                onClick={async () => {
                  setViewState('history')
                  const hist = await getVivaHistory()
                  setHistoryData(hist)
                }}
              >
                <History size={15} />
                History ({historyData.total_sessions})
              </Button>
            </div>
          )
        }
      />

      {error && <ErrorState title="Viva Notice" message={error} onRetry={() => setError(null)} />}

      {/* ===================================================================== */}
      {/* 1. SETUP VIEW                                                        */}
      {/* ===================================================================== */}
      {viewState === 'setup' && (
        <div className="space-y-6">
          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard
              icon={Award}
              label="Completed Vivas"
              value={historyData.total_sessions}
              tone="brand"
            />
            <StatCard
              icon={TrendingUp}
              label="Average Viva Score"
              value={`${historyData.average_score}%`}
              tone="emerald"
            />
            <StatCard
              icon={Bot}
              label="Examiner Engine"
              value="Gemini 2.5 Flash"
              subtext="4-Dimension Evaluation"
              tone="purple"
            />
          </div>

          <Card>
            <CardHeader
              title="Configure Practice Session"
              subtitle="Select your focus topic, evaluation mode, and difficulty"
            />

            <div className="space-y-6">
              {/* Mode Selection Cards */}
              <div>
                <label className="block text-sm font-semibold text-ink-900 dark:text-ink-100 mb-2">
                  Select Viva Mode
                </label>
                <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                  {MODES.map((m) => {
                    const Icon = m.icon
                    const isSelected = selectedMode === m.id
                    return (
                      <div
                        key={m.id}
                        onClick={() => setSelectedMode(m.id)}
                        className={`cursor-pointer rounded-2xl border p-4 transition-all ${isSelected
                          ? 'border-brand-600 bg-brand-50/60 ring-2 ring-brand-500/20 dark:border-brand-500 dark:bg-brand-950/40'
                          : 'border-ink-200 bg-white hover:border-brand-300 dark:border-ink-800 dark:bg-ink-900 dark:hover:border-ink-700'
                          }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${m.color}`}>
                            <Icon size={20} />
                          </div>
                          <span
                            className={`rounded-full px-2 py-0.5 text-xs font-semibold ${m.badgeTone === 'emerald'
                              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300'
                              : m.badgeTone === 'purple'
                                ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-300'
                                : 'bg-brand-100 text-brand-800 dark:bg-brand-900/50 dark:text-brand-300'
                              }`}
                          >
                            {m.badge}
                          </span>
                        </div>
                        <h4 className="font-semibold text-ink-900 dark:text-ink-100">{m.name}</h4>
                        <p className="mt-1 text-xs text-ink-500 dark:text-ink-400 leading-relaxed">
                          {m.description}
                        </p>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Topic & Subject Picker */}
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-ink-700 dark:text-ink-300 mb-1.5">
                    Topic to Practice
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={selectedTopic}
                      onChange={(e) => setSelectedTopic(e.target.value)}
                      placeholder="e.g. Routing Algorithms, Deadlocks, Graph Traversal"
                      list="viva-topics-list"
                      className="w-full rounded-xl border border-ink-200 bg-white px-3.5 py-2.5 text-sm text-ink-900 placeholder:text-ink-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
                    />
                    <datalist id="viva-topics-list">
                      {topicOptions.map((top) => (
                        <option key={top} value={top} />
                      ))}
                    </datalist>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {DEFAULT_TOPICS.slice(0, 5).map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => setSelectedTopic(t)}
                        className={`rounded-lg px-2 py-0.5 text-xs transition-colors ${selectedTopic === t
                          ? 'bg-brand-600 text-white font-medium'
                          : 'bg-ink-100 text-ink-600 hover:bg-ink-200 dark:bg-ink-800 dark:text-ink-300'
                          }`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-ink-700 dark:text-ink-300 mb-1.5">
                    Grounding Material (Optional)
                  </label>
                  <select
                    value={selectedMaterialId}
                    onChange={(e) => setSelectedMaterialId(e.target.value)}
                    className="w-full rounded-xl border border-ink-200 bg-white px-3.5 py-2.5 text-sm text-ink-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
                  >
                    <option value="">All Course Materials / Automatic</option>
                    {materials.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.title}
                      </option>
                    ))}
                  </select>
                  <p className="mt-1.5 text-xs text-ink-500 dark:text-ink-400">
                    Questions will be grounded in relevant lecture notes and textbook excerpts.
                  </p>
                </div>
              </div>

              {/* Difficulty & Number of Questions */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-ink-700 dark:text-ink-300 mb-1.5">
                    Initial Difficulty
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {['easy', 'medium', 'hard'].map((d) => (
                      <button
                        key={d}
                        type="button"
                        onClick={() => setSelectedDifficulty(d)}
                        className={`rounded-xl border py-2 text-xs font-semibold capitalize transition-all ${selectedDifficulty === d
                          ? 'border-brand-600 bg-brand-50 text-brand-700 dark:border-brand-500 dark:bg-brand-950/40 dark:text-brand-300 ring-2 ring-brand-500/20'
                          : 'border-ink-200 bg-white text-ink-600 hover:bg-ink-50 dark:border-ink-800 dark:bg-ink-900 dark:text-ink-400'
                          }`}
                      >
                        {d}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-ink-700 dark:text-ink-300 mb-1.5">
                    Questions Target
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {[3, 4, 5].map((count) => (
                      <button
                        key={count}
                        type="button"
                        onClick={() => setTotalQuestions(count)}
                        className={`rounded-xl border py-2 text-xs font-semibold transition-all ${totalQuestions === count
                          ? 'border-brand-600 bg-brand-50 text-brand-700 dark:border-brand-500 dark:bg-brand-950/40 dark:text-brand-300 ring-2 ring-brand-500/20'
                          : 'border-ink-200 bg-white text-ink-600 hover:bg-ink-50 dark:border-ink-800 dark:bg-ink-900 dark:text-ink-400'
                          }`}
                      >
                        {count} Questions
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Start Action Button */}
              <div className="pt-2 border-t border-ink-100 dark:border-ink-800 flex justify-end">
                <Button
                  size="lg"
                  onClick={handleStartSession}
                  disabled={loading || !selectedTopic}
                >
                  {loading ? <LoadingSpinner size={18} /> : <Zap size={18} />}
                  Begin Viva Examination
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* ===================================================================== */}
      {/* 2. LIVE VIVA SESSION VIEW                                             */}
      {/* ===================================================================== */}
      {viewState === 'session' && currentQuestion && (
        <div className="space-y-6">
          {/* Session Header Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-ink-200 bg-white p-4 dark:border-ink-800 dark:bg-ink-900">
            <div className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white">
                <Bot size={20} />
              </span>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-ink-900 dark:text-ink-100 capitalize">
                    {selectedTopic}
                  </h3>
                  <span className="rounded-full bg-brand-100 px-2 py-0.5 text-xs font-semibold text-brand-700 dark:bg-brand-900/50 dark:text-brand-300 capitalize">
                    {selectedMode} Viva
                  </span>
                </div>
                <p className="text-xs text-ink-500 dark:text-ink-400">
                  Question {currentQuestionIndex} of {sessionTotalQuestions}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-36 hidden sm:block">
                <ProgressBar
                  value={((currentQuestionIndex - (currentEvaluation ? 0 : 1)) / sessionTotalQuestions) * 100}
                />
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleEndSession}
                className="text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/40"
              >
                End Viva & View Report
              </Button>
            </div>
          </div>

          {/* Question Card */}
          <Card className="border-l-4 border-l-brand-600">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-semibold text-brand-700 dark:bg-brand-950/60 dark:text-brand-300">
                    <Bot size={13} />
                    AI Examiner
                  </span>
                  {currentQuestion.question_type === 'follow_up' && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-800 dark:bg-amber-900/50 dark:text-amber-300">
                      <RotateCw size={12} />
                      Adaptive Follow-Up
                    </span>
                  )}
                  <span className="rounded-full bg-ink-100 px-2 py-0.5 text-[11px] font-medium uppercase text-ink-600 dark:bg-ink-800 dark:text-ink-400">
                    {currentQuestion.difficulty}
                  </span>
                </div>

                {currentQuestion.ideal_concept_points?.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setShowIdealHints(!showIdealHints)}
                    className="flex items-center gap-1 text-xs text-ink-500 hover:text-brand-600 dark:text-ink-400 dark:hover:text-brand-400"
                  >
                    <HelpCircle size={13} />
                    {showIdealHints ? 'Hide Guidelines' : 'Topic Guidelines'}
                  </button>
                )}
              </div>

              <h2 className="text-lg font-semibold text-ink-900 dark:text-ink-100 leading-snug">
                {currentQuestion.question_text}
              </h2>

              {showIdealHints && currentQuestion.ideal_concept_points?.length > 0 && (
                <div className="rounded-xl bg-ink-50 p-3 text-xs text-ink-600 dark:bg-ink-800/60 dark:text-ink-300 space-y-1">
                  <p className="font-semibold text-ink-700 dark:text-ink-200">Key concepts examiner looks for:</p>
                  <ul className="list-disc list-inside space-y-0.5">
                    {currentQuestion.ideal_concept_points.map((pt, i) => (
                      <li key={i}>{pt}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </Card>

          {/* Student Answer & Feedback Area */}
          {!currentEvaluation ? (
            <Card>
              <CardHeader
                title="Your Oral / Written Explanation"
                subtitle="Express your reasoning clearly, addressing foundational mechanisms and edge cases."
              />
              <form onSubmit={handleSubmitAnswer} className="space-y-4">
                <div className="relative">
                  <textarea
                    ref={answerInputRef}
                    rows={6}
                    value={studentAnswer}
                    onChange={(e) => setStudentAnswer(e.target.value)}
                    placeholder="Speak or type your explanation here in complete sentences..."
                    className="w-full rounded-2xl border border-ink-200 bg-ink-50/50 p-4 text-sm text-ink-900 placeholder:text-ink-400 focus:border-brand-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-ink-800 dark:bg-ink-900/60 dark:text-ink-100 dark:focus:bg-ink-900"
                  />
                  {isDictating && (
                    <div className="absolute right-4 top-4 flex items-center gap-2 rounded-full bg-rose-500 px-3 py-1 text-xs font-semibold text-white animate-pulse">
                      <span className="h-2 w-2 rounded-full bg-white animate-ping" />
                      Listening...
                    </div>
                  )}
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                  <div className="flex items-center gap-3">
                    <Button
                      type="button"
                      variant={isDictating ? 'primary' : 'outline'}
                      size="sm"
                      onClick={toggleDictation}
                      className={isDictating ? 'bg-rose-600 hover:bg-rose-700 text-white' : ''}
                    >
                      {isDictating ? <MicOff size={15} /> : <Mic size={15} />}
                      {isDictating ? 'Stop Recording' : 'Voice Dictate'}
                    </Button>
                    <span className="text-xs text-ink-400 dark:text-ink-500">
                      {wordCount} words
                    </span>
                  </div>

                  <Button
                    type="submit"
                    disabled={isSubmitting || !studentAnswer.trim()}
                    size="lg"
                  >
                    {isSubmitting ? (
                      <>
                        <LoadingSpinner size={16} />
                        Examiner Evaluating...
                      </>
                    ) : (
                      <>
                        <Send size={16} />
                        Submit Answer
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </Card>
          ) : (
            /* Live Evaluation Feedback Display */
            <div className="space-y-4 animate-fadeIn">
              <Card className="border-t-4 border-t-brand-600">
                <div className="space-y-5">
                  <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-ink-100 dark:border-ink-800">
                    <div className="flex items-center gap-2.5">
                      <div
                        className={`flex h-11 w-11 items-center justify-center rounded-2xl text-lg font-bold ${currentEvaluation.score >= 80
                          ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
                          : currentEvaluation.score >= 60
                            ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300'
                            : 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300'
                          }`}
                      >
                        {Math.round(currentEvaluation.score)}%
                      </div>
                      <div>
                        <h4 className="font-semibold text-ink-900 dark:text-ink-100">
                          {currentEvaluation.score >= 80
                            ? 'Strong Performance'
                            : currentEvaluation.score >= 60
                              ? 'Solid Response'
                              : 'Needs Reinforcement'}
                        </h4>
                        <p className="text-xs text-ink-500 dark:text-ink-400">
                          AI Examiner Evaluation Breakdown
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {hasNextQuestion ? (
                        <Button size="md" onClick={handleProceedNext}>
                          Next Question
                          <ArrowRight size={16} />
                        </Button>
                      ) : (
                        <Button size="md" onClick={handleEndSession}>
                          <Award size={16} />
                          View Final Report
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* 4 Dimensional Metric Bars */}
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    <div className="rounded-xl border border-ink-100 bg-ink-50/50 p-3 dark:border-ink-800 dark:bg-ink-900/40">
                      <div className="flex justify-between text-xs font-semibold mb-1">
                        <span className="text-ink-700 dark:text-ink-300">Correctness</span>
                        <span className="text-brand-600 dark:text-brand-400">
                          {Math.round(currentEvaluation.correctness)}%
                        </span>
                      </div>
                      <ProgressBar value={currentEvaluation.correctness} />
                    </div>

                    <div className="rounded-xl border border-ink-100 bg-ink-50/50 p-3 dark:border-ink-800 dark:bg-ink-900/40">
                      <div className="flex justify-between text-xs font-semibold mb-1">
                        <span className="text-ink-700 dark:text-ink-300">Relevance</span>
                        <span className="text-emerald-600 dark:text-emerald-400">
                          {Math.round(currentEvaluation.relevance)}%
                        </span>
                      </div>
                      <ProgressBar value={currentEvaluation.relevance} />
                    </div>

                    <div className="rounded-xl border border-ink-100 bg-ink-50/50 p-3 dark:border-ink-800 dark:bg-ink-900/40">
                      <div className="flex justify-between text-xs font-semibold mb-1">
                        <span className="text-ink-700 dark:text-ink-300">Completeness</span>
                        <span className="text-purple-600 dark:text-purple-400">
                          {Math.round(currentEvaluation.completeness)}%
                        </span>
                      </div>
                      <ProgressBar value={currentEvaluation.completeness} />
                    </div>

                    <div className="rounded-xl border border-ink-100 bg-ink-50/50 p-3 dark:border-ink-800 dark:bg-ink-900/40">
                      <div className="flex justify-between text-xs font-semibold mb-1">
                        <span className="text-ink-700 dark:text-ink-300">Conceptual Depth</span>
                        <span className="text-amber-600 dark:text-amber-400">
                          {Math.round(currentEvaluation.conceptual_understanding)}%
                        </span>
                      </div>
                      <ProgressBar value={currentEvaluation.conceptual_understanding} />
                    </div>
                  </div>

                  {/* Feedback Text */}
                  <div className="rounded-xl bg-brand-50/60 p-4 dark:bg-brand-950/30 border border-brand-100 dark:border-brand-900/50">
                    <p className="text-xs font-semibold text-brand-900 dark:text-brand-200 mb-1">
                      Examiner Commentary:
                    </p>
                    <p className="text-sm text-brand-800 dark:text-brand-300 leading-relaxed">
                      {currentEvaluation.feedback}
                    </p>
                  </div>

                  {/* Strengths & Missing Points Chips */}
                  <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                    {currentEvaluation.key_strengths?.length > 0 && (
                      <div className="space-y-1.5">
                        <h5 className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-400">
                          <CheckCircle2 size={14} />
                          Strengths Demonstrated
                        </h5>
                        <div className="space-y-1">
                          {currentEvaluation.key_strengths.map((str, i) => (
                            <div
                              key={i}
                              className="rounded-lg bg-emerald-50 px-2.5 py-1.5 text-xs text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-100 dark:border-emerald-900/40"
                            >
                              {str}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {currentEvaluation.missing_points?.length > 0 && (
                      <div className="space-y-1.5">
                        <h5 className="flex items-center gap-1.5 text-xs font-semibold text-amber-700 dark:text-amber-400">
                          <AlertTriangle size={14} />
                          Omitted or Missing Concepts
                        </h5>
                        <div className="space-y-1">
                          {currentEvaluation.missing_points.map((miss, i) => (
                            <div
                              key={i}
                              className="rounded-lg bg-amber-50 px-2.5 py-1.5 text-xs text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-100 dark:border-amber-900/40"
                            >
                              {miss}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* 3. FINAL VIVA REPORT VIEW                                             */}
      {/* ===================================================================== */}
      {viewState === 'report' && sessionReport && (
        <div className="space-y-6">
          {/* Report Hero Card */}
          <Card className="border-t-4 border-t-brand-600">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6 p-2">
              <div className="flex items-center gap-5">
                <div
                  className={`flex h-20 w-20 flex-col items-center justify-center rounded-3xl border text-center ${sessionReport.overall_score >= 80
                    ? 'border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300'
                    : sessionReport.overall_score >= 60
                      ? 'border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-950/50 dark:text-amber-300'
                      : 'border-rose-300 bg-rose-50 text-rose-800 dark:border-rose-800 dark:bg-rose-950/50 dark:text-rose-300'
                    }`}
                >
                  <span className="text-2xl font-black">{Math.round(sessionReport.overall_score)}%</span>
                  <span className="text-[10px] font-semibold uppercase tracking-wide">Score</span>
                </div>

                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-bold text-ink-900 dark:text-ink-100 capitalize">
                      {sessionReport.topic}
                    </h2>
                    <span className="rounded-full bg-brand-100 px-2.5 py-0.5 text-xs font-semibold text-brand-700 dark:bg-brand-900/50 dark:text-brand-300 capitalize">
                      {sessionReport.mode} Viva
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-ink-500 dark:text-ink-400">
                    {sessionReport.completed_questions} questions evaluated • Synchronized to your Learner Model
                  </p>
                  {sessionReport.overall_feedback && (
                    <p className="mt-2 text-sm text-ink-700 dark:text-ink-200 italic">
                      "{sessionReport.overall_feedback}"
                    </p>
                  )}
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Button variant="secondary" onClick={() => setViewState('setup')}>
                  <RotateCw size={15} />
                  Practice Again
                </Button>
                <Link to="/study-plan">
                  <Button variant="primary">
                    Go to Study Plan
                    <ArrowRight size={15} />
                  </Button>
                </Link>
              </div>
            </div>
          </Card>

          {/* 4 Score Metrics */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              icon={ShieldCheck}
              label="Correctness"
              value={`${Math.round(sessionReport.correctness_score)}%`}
              subtext="Factual & conceptual accuracy"
              tone="brand"
            />
            <StatCard
              icon={Zap}
              label="Relevance"
              value={`${Math.round(sessionReport.relevance_score)}%`}
              subtext="Directness of answer"
              tone="emerald"
            />
            <StatCard
              icon={Layers}
              label="Completeness"
              value={`${Math.round(sessionReport.completeness_score)}%`}
              subtext="Coverage of key points"
              tone="purple"
            />
            <StatCard
              icon={Sparkles}
              label="Conceptual Depth"
              value={`${Math.round(sessionReport.conceptual_score)}%`}
              subtext="Depth & reasoning"
              tone="amber"
            />
          </div>

          {/* Strengths & Weak Areas */}
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <Card>
              <CardHeader
                title="Demonstrated Strengths"
                subtitle="Concepts and mechanisms explained with clarity"
              />
              <div className="space-y-2">
                {(sessionReport.strengths || []).map((str, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-2.5 rounded-xl bg-emerald-50/60 p-3 text-xs text-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-200 border border-emerald-100 dark:border-emerald-900/40"
                  >
                    <CheckCircle2 size={16} className="text-emerald-600 dark:text-emerald-400 mt-0.5 shrink-0" />
                    <span>{str}</span>
                  </div>
                ))}
              </div>
            </Card>

            <Card>
              <CardHeader
                title="Identified Weak Areas"
                subtitle="Topics and gaps flagged for targeted review"
              />
              <div className="space-y-2">
                {(sessionReport.weak_areas || []).map((w, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-2.5 rounded-xl bg-amber-50/60 p-3 text-xs text-amber-900 dark:bg-amber-950/30 dark:text-amber-200 border border-amber-100 dark:border-amber-900/40"
                  >
                    <AlertTriangle size={16} className="text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
                    <span>{w}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Actionable Improvement Roadmap */}
          <Card className="border border-brand-200 dark:border-brand-900/50 bg-brand-50/20 dark:bg-brand-950/10">
            <CardHeader
              title="Targeted Action Roadmap"
              subtitle="Concrete pedagogical steps recommended by your AI examiner"
            />
            <div className="space-y-2.5">
              {(sessionReport.suggested_improvements || []).map((imp, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-xl bg-white p-3 text-xs text-ink-800 shadow-sm dark:bg-ink-900 dark:text-ink-200 border border-ink-100 dark:border-ink-800"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-100 text-[11px] font-bold text-brand-700 dark:bg-brand-900 dark:text-brand-300">
                      {i + 1}
                    </span>
                    <span>{imp}</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Full Q&A Transcript */}
          <Card>
            <CardHeader
              title="Complete Session Transcript"
              subtitle="Review every examiner question, your response, and detailed feedback"
            />
            <div className="space-y-3">
              {(sessionReport.transcript || []).map((item, idx) => {
                const isExpanded = expandedTranscripts[idx] !== false
                const score = item.evaluation?.score || 0
                return (
                  <div
                    key={item.question_id || idx}
                    className="rounded-2xl border border-ink-200 bg-white dark:border-ink-800 dark:bg-ink-900 overflow-hidden"
                  >
                    <div
                      onClick={() => toggleTranscript(idx)}
                      className="flex cursor-pointer items-center justify-between p-4 hover:bg-ink-50 dark:hover:bg-ink-800/50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-ink-100 text-xs font-bold text-ink-700 dark:bg-ink-800 dark:text-ink-300">
                          Q{idx + 1}
                        </span>
                        <div>
                          <p className="font-semibold text-ink-900 dark:text-ink-100 text-sm">
                            {item.question_text}
                          </p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-[11px] text-ink-400 capitalize">
                              {item.question_type === 'follow_up' ? 'Adaptive Follow-Up' : 'Main Question'}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${score >= 80
                            ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
                            : score >= 60
                              ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300'
                              : 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300'
                            }`}
                        >
                          {Math.round(score)}%
                        </span>
                        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="border-t border-ink-100 bg-ink-50/40 p-4 dark:border-ink-800 dark:bg-ink-900/60 space-y-3 text-xs">
                        <div>
                          <p className="font-semibold text-ink-600 dark:text-ink-400 mb-1">
                            Your Response:
                          </p>
                          <p className="rounded-xl bg-white p-3 text-ink-800 dark:bg-ink-800 dark:text-ink-200 border border-ink-100 dark:border-ink-700">
                            {item.answer_text || 'No answer recorded'}
                          </p>
                        </div>

                        {item.evaluation && (
                          <div className="space-y-2">
                            <div className="rounded-xl bg-brand-50/60 p-3 text-brand-900 dark:bg-brand-950/40 dark:text-brand-200 border border-brand-100 dark:border-brand-900/40">
                              <p className="font-semibold mb-0.5">Examiner Evaluation:</p>
                              <p>{item.evaluation.feedback}</p>
                            </div>

                            <div className="grid grid-cols-4 gap-2 text-center text-[11px]">
                              <div className="rounded-lg bg-white p-2 dark:bg-ink-800">
                                <span className="text-ink-400 block">Correctness</span>
                                <span className="font-bold text-ink-900 dark:text-ink-100">
                                  {Math.round(item.evaluation.correctness)}%
                                </span>
                              </div>
                              <div className="rounded-lg bg-white p-2 dark:bg-ink-800">
                                <span className="text-ink-400 block">Relevance</span>
                                <span className="font-bold text-ink-900 dark:text-ink-100">
                                  {Math.round(item.evaluation.relevance)}%
                                </span>
                              </div>
                              <div className="rounded-lg bg-white p-2 dark:bg-ink-800">
                                <span className="text-ink-400 block">Completeness</span>
                                <span className="font-bold text-ink-900 dark:text-ink-100">
                                  {Math.round(item.evaluation.completeness)}%
                                </span>
                              </div>
                              <div className="rounded-lg bg-white p-2 dark:bg-ink-800">
                                <span className="text-ink-400 block">Conceptual</span>
                                <span className="font-bold text-ink-900 dark:text-ink-100">
                                  {Math.round(item.evaluation.conceptual_understanding)}%
                                </span>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </Card>
        </div>
      )}

      {/* ===================================================================== */}
      {/* 4. HISTORY VIEW                                                       */}
      {/* ===================================================================== */}
      {viewState === 'history' && (
        <Card>
          <CardHeader
            title="Past Viva & Interview Sessions"
            subtitle="Review your previous oral examinations, question histories, and progress."
          />

          {historyData.sessions?.length === 0 ? (
            <EmptyState
              icon={Award}
              title="No Viva Sessions Yet"
              message="Start your first AI viva or technical interview practice to build oral presentation mastery."
              actionLabel="Start New Session"
              onAction={() => setViewState('setup')}
            />
          ) : (
            <div className="space-y-3">
              {historyData.sessions.map((s) => (
                <div
                  key={s.id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-ink-200 bg-white p-4 transition-all hover:border-brand-300 dark:border-ink-800 dark:bg-ink-900 dark:hover:border-ink-700"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`flex h-10 w-10 items-center justify-center rounded-xl text-xs font-bold ${s.overall_score >= 80
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
                        : s.overall_score >= 60
                          ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300'
                          : 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300'
                        }`}
                    >
                      {Math.round(s.overall_score)}%
                    </span>
                    <div>
                      <h4 className="font-semibold text-ink-900 dark:text-ink-100 capitalize">
                        {s.topic}
                      </h4>
                      <p className="text-xs text-ink-500 dark:text-ink-400 capitalize">
                        {s.mode} Viva • {s.difficulty} • {new Date(s.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleViewHistoricalSession(s.id)}
                    >
                      View Report
                      <ArrowRight size={14} />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  )
}

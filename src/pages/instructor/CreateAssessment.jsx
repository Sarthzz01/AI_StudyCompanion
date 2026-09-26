import { useState, useEffect } from 'react'
import { useNavigate, Link, useSearchParams } from 'react-router-dom'
import {
  Sparkles,
  Plus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Save,
  ArrowLeft,
  BookOpen,
  Clock,
  Award,
  Layers,
  Edit3
} from 'lucide-react'
import PageHeader from '../../components/PageHeader.jsx'
import Card, { CardHeader } from '../../components/Card.jsx'
import Button from '../../components/Button.jsx'
import Input from '../../components/Input.jsx'
import LoadingSpinner from '../../components/LoadingSpinner.jsx'
import { createInstructorAssessment, aiGenerateAssessmentQuestions, getMaterials } from '../../services/api.js'
import { useToast } from '../../context/ToastContext.jsx'

const DEFAULT_TOPICS = [
  'Deadlocks',
  'Routing Algorithms',
  'Transactions & ACID',
  'Tree Traversal',
  'Process Synchronization',
  'Page Replacement',
  'Relational Algebra',
  'BST Operations',
  'Graph Traversal',
  'Application Protocols'
]

export default function CreateAssessment() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const toast = useToast()

  // Form State
  const [title, setTitle] = useState(searchParams.get('title') || 'Comprehensive Topic Assessment')
  const [topic, setTopic] = useState(searchParams.get('topic') || 'Deadlocks')
  const [difficulty, setDifficulty] = useState('medium')
  const [timeLimitMinutes, setTimeLimitMinutes] = useState(25)
  const [passPercentage, setPassPercentage] = useState(60)
  const [selectedMaterialId, setSelectedMaterialId] = useState('')
  const [materials, setMaterials] = useState([])

  // AI Generator Panel State
  const [isGeneratingAI, setIsGeneratingAI] = useState(false)
  const [aiQuestionCount, setAiQuestionCount] = useState(4)

  // Questions List
  const [questions, setQuestions] = useState([
    {
      id: 1,
      question_text: 'Which condition is NOT one of the Coffman conditions required for deadlocks to occur?',
      question_type: 'multiple_choice',
      options: [
        'Mutual Exclusion',
        'Preemption Allowed',
        'Hold and Wait',
        'Circular Wait'
      ],
      correct_answer: 1,
      points: 25,
      explanation: 'No preemption is the required condition; allowing preemption prevents deadlock.',
      concept_tested: 'Coffman Conditions',
      difficulty: 'easy'
    }
  ])

  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  // Load course materials for grounding
  useEffect(() => {
    async function loadMats() {
      try {
        const data = await getMaterials()
        setMaterials(data || [])
      } catch (err) {
        console.warn('Could not fetch materials for assessment generator:', err)
      }
    }
    loadMats()
  }, [])

  // Calculate total points dynamically
  const totalPoints = questions.reduce((sum, q) => sum + (Number(q.points) || 10), 0)

  // AI Generation Handler
  const handleAIGenerate = async () => {
    if (!topic.trim()) {
      setError('Please select or specify a topic for AI generation.')
      return
    }

    setIsGeneratingAI(true)
    setError(null)
    try {
      const res = await aiGenerateAssessmentQuestions({
        topic: topic.trim(),
        difficulty,
        question_count: aiQuestionCount,
        material_id: selectedMaterialId || null,
        include_explanations: true
      })

      if (res.questions && res.questions.length > 0) {
        setQuestions(res.questions)
        if (res.suggested_title) setTitle(res.suggested_title)
        if (res.suggested_time_minutes) setTimeLimitMinutes(res.suggested_time_minutes)
        if (res.suggested_pass_percentage) setPassPercentage(res.suggested_pass_percentage)
        toast('AI Assessment generated! You can now review and edit questions.', 'success')
      }
    } catch (err) {
      setError(err.message || 'AI generation encountered an issue.')
    } finally {
      setIsGeneratingAI(false)
    }
  }

  // Question manipulation handlers
  const handleQuestionTextChange = (qIndex, text) => {
    setQuestions((prev) => {
      const next = [...prev]
      next[qIndex].question_text = text
      return next
    })
  }

  const handleOptionChange = (qIndex, optIndex, text) => {
    setQuestions((prev) => {
      const next = [...prev]
      const opts = [...next[qIndex].options]
      opts[optIndex] = text
      next[qIndex].options = opts
      return next
    })
  }

  const handleCorrectAnswerChange = (qIndex, optIndex) => {
    setQuestions((prev) => {
      const next = [...prev]
      next[qIndex].correct_answer = optIndex
      return next
    })
  }

  const handlePointsChange = (qIndex, pts) => {
    setQuestions((prev) => {
      const next = [...prev]
      next[qIndex].points = Number(pts) || 10
      return next
    })
  }

  const handleExplanationChange = (qIndex, text) => {
    setQuestions((prev) => {
      const next = [...prev]
      next[qIndex].explanation = text
      return next
    })
  }

  const handleAddQuestion = () => {
    setQuestions((prev) => [
      ...prev,
      {
        id: prev.length + 1,
        question_text: '',
        question_type: 'multiple_choice',
        options: ['', '', '', ''],
        correct_answer: 0,
        points: 20,
        explanation: '',
        concept_tested: topic,
        difficulty
      }
    ])
  }

  const handleDeleteQuestion = (qIndex) => {
    if (questions.length <= 1) {
      setError('An assessment must contain at least one question.')
      return
    }
    setQuestions((prev) => prev.filter((_, idx) => idx !== qIndex))
  }

  // Save assessment handler
  const handleSave = async (e) => {
    e.preventDefault()
    if (!title.trim()) {
      setError('Please provide an assessment title.')
      return
    }
    if (!topic.trim()) {
      setError('Please provide a topic.')
      return
    }
    for (let i = 0; i < questions.length; i++) {
      const q = questions[i]
      if (!q.question_text.trim()) {
        setError(`Question ${i + 1} text cannot be blank.`)
        return
      }
      if (q.options.some((opt) => !opt.trim())) {
        setError(`All 4 choices in Question ${i + 1} must be filled out.`)
        return
      }
    }

    setSaving(true)
    setError(null)
    try {
      await createInstructorAssessment({
        title: title.trim(),
        topic: topic.trim(),
        difficulty,
        time_limit_minutes: Number(timeLimitMinutes),
        total_points: totalPoints,
        pass_percentage: Number(passPercentage),
        questions: questions.map((q, idx) => ({
          id: idx + 1,
          question_text: q.question_text.trim(),
          question_type: q.question_type || 'multiple_choice',
          options: q.options.map((o) => o.trim()),
          correct_answer: Number(q.correct_answer),
          points: Number(q.points) || 10,
          explanation: q.explanation?.trim() || null,
          concept_tested: q.concept_tested || topic,
          difficulty: q.difficulty || difficulty
        })),
        is_published: true
      })

      toast('Assessment created and published successfully!', 'success')
      navigate('/instructor/assessments')
    } catch (err) {
      setError(err.message || 'Failed to save assessment.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-8 pb-16">
      {/* Page Header */}
      <PageHeader
        title="Author New Assessment"
        subtitle="Design comprehensive assessments manually or co-create with the AI curriculum generator."
        actions={
          <div className="flex items-center gap-3">
            <Link to="/instructor/assessments">
              <Button variant="ghost" size="sm">
                <ArrowLeft size={16} />
                Back to Assessments
              </Button>
            </Link>
          </div>
        }
      />

      {error && (
        <div className="flex items-center gap-3 rounded-2xl border border-rose-200 bg-rose-50/80 p-4 text-sm text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          <AlertCircle size={18} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* AI Assistance Co-Pilot Banner */}
      <Card className="border-2 border-brand-200 bg-gradient-to-r from-brand-50/70 via-purple-50/40 to-white dark:border-brand-800/60 dark:from-brand-950/40 dark:via-purple-950/20 dark:to-ink-900">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-1.5 rounded-full bg-brand-100 px-3 py-0.5 text-xs font-bold text-brand-700 dark:bg-brand-900/60 dark:text-brand-300">
              <Sparkles size={13} />
              AI Assessment Co-Pilot
            </div>
            <h3 className="text-base font-bold text-ink-900 dark:text-ink-100">
              Generate Questions Grounded in Syllabus & Course Materials
            </h3>
            <p className="text-xs text-ink-600 dark:text-ink-400">
              Select a topic and difficulty. Gemini will construct balanced, rigorous conceptual questions that you can review and edit.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <label className="text-xs font-semibold text-ink-600 dark:text-ink-400">Questions:</label>
              <select
                value={aiQuestionCount}
                onChange={(e) => setAiQuestionCount(Number(e.target.value))}
                className="rounded-xl border border-ink-200 bg-white px-3 py-1.5 text-xs font-medium text-ink-900 focus:outline-none dark:border-ink-700 dark:bg-ink-800 dark:text-ink-100"
              >
                <option value={3}>3 Questions</option>
                <option value={4}>4 Questions</option>
                <option value={5}>5 Questions</option>
                <option value={8}>8 Questions</option>
              </select>
            </div>

            <Button
              variant="primary"
              size="md"
              onClick={handleAIGenerate}
              disabled={isGeneratingAI}
            >
              {isGeneratingAI ? <LoadingSpinner size={16} /> : <Sparkles size={16} />}
              {isGeneratingAI ? 'Generating with AI...' : 'Generate with AI'}
            </Button>
          </div>
        </div>
      </Card>

      {/* Main Form */}
      <form onSubmit={handleSave} className="space-y-6">
        {/* Assessment Settings Card */}
        <Card>
          <CardHeader
            title="Assessment Specifications"
            subtitle="Configure target topic, grading criteria, and time constraints."
          />

          <div className="mt-4 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-ink-700 dark:text-ink-300 mb-1.5">
                Assessment Title
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Midterm Evaluation: Concurrency & Deadlocks"
                className="w-full rounded-xl border border-ink-200 bg-white px-3.5 py-2 text-sm text-ink-900 placeholder:text-ink-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-ink-700 dark:text-ink-300 mb-1.5">
                Syllabus Topic
              </label>
              <input
                type="text"
                list="topic-suggestions"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. Deadlocks"
                className="w-full rounded-xl border border-ink-200 bg-white px-3.5 py-2 text-sm text-ink-900 placeholder:text-ink-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
                required
              />
              <datalist id="topic-suggestions">
                {DEFAULT_TOPICS.map((t) => (
                  <option key={t} value={t} />
                ))}
              </datalist>
            </div>

            <div>
              <label className="block text-xs font-semibold text-ink-700 dark:text-ink-300 mb-1.5">
                Difficulty Level
              </label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full rounded-xl border border-ink-200 bg-white px-3.5 py-2 text-sm text-ink-900 focus:outline-none dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100 capitalize"
              >
                <option value="easy">Easy (Foundational)</option>
                <option value="medium">Medium (Standard)</option>
                <option value="hard">Hard (Advanced / Edge Cases)</option>
                <option value="mixed">Mixed Difficulty</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-ink-700 dark:text-ink-300 mb-1.5">
                Time Limit (Minutes)
              </label>
              <input
                type="number"
                min={5}
                max={180}
                value={timeLimitMinutes}
                onChange={(e) => setTimeLimitMinutes(Number(e.target.value))}
                className="w-full rounded-xl border border-ink-200 bg-white px-3.5 py-2 text-sm text-ink-900 focus:outline-none dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-ink-700 dark:text-ink-300 mb-1.5">
                Pass Threshold (%)
              </label>
              <input
                type="number"
                min={0}
                max={100}
                value={passPercentage}
                onChange={(e) => setPassPercentage(Number(e.target.value))}
                className="w-full rounded-xl border border-ink-200 bg-white px-3.5 py-2 text-sm text-ink-900 focus:outline-none dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
              />
            </div>
          </div>
        </Card>

        {/* Questions Editor Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-ink-900 dark:text-ink-100">
                Assessment Questions ({questions.length})
              </h2>
              <p className="text-xs text-ink-500 dark:text-ink-400">
                Total Assessment Points: <span className="font-bold text-brand-600 dark:text-brand-400">{totalPoints} pts</span>
              </p>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleAddQuestion}
            >
              <Plus size={15} />
              Add Question
            </Button>
          </div>

          {questions.map((q, qIndex) => (
            <Card key={qIndex} className="space-y-4 border-l-4 border-l-brand-600">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-600 text-xs font-bold text-white">
                    {qIndex + 1}
                  </span>
                  <span className="text-xs font-semibold text-ink-600 dark:text-ink-400">
                    Multiple Choice Question
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5">
                    <label className="text-xs font-semibold text-ink-500 dark:text-ink-400">Points:</label>
                    <input
                      type="number"
                      min={1}
                      max={100}
                      value={q.points}
                      onChange={(e) => handlePointsChange(qIndex, e.target.value)}
                      className="w-16 rounded-lg border border-ink-200 bg-white px-2 py-1 text-xs font-bold text-ink-900 dark:border-ink-700 dark:bg-ink-800 dark:text-ink-100"
                    />
                  </div>
                  {questions.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleDeleteQuestion(qIndex)}
                      className="rounded-lg p-1.5 text-ink-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40"
                      title="Delete question"
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </div>
              </div>

              {/* Question Text Prompt */}
              <div>
                <label className="block text-xs font-semibold text-ink-700 dark:text-ink-300 mb-1">
                  Question Statement
                </label>
                <textarea
                  rows={2}
                  value={q.question_text}
                  onChange={(e) => handleQuestionTextChange(qIndex, e.target.value)}
                  placeholder="Enter the problem statement or question here..."
                  className="w-full rounded-xl border border-ink-200 bg-ink-50/50 p-3 text-sm text-ink-900 placeholder:text-ink-400 focus:border-brand-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-ink-800 dark:bg-ink-900/60 dark:text-ink-100 dark:focus:bg-ink-900"
                  required
                />
              </div>

              {/* Options Radio List */}
              <div className="space-y-2 pt-1">
                <label className="block text-xs font-semibold text-ink-700 dark:text-ink-300">
                  Choices (Select the radio button beside the correct answer):
                </label>
                <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                  {q.options.map((opt, optIndex) => (
                    <div
                      key={optIndex}
                      className={`flex items-center gap-2.5 rounded-xl border p-2.5 transition-all ${
                        q.correct_answer === optIndex
                          ? 'border-emerald-500 bg-emerald-50/40 dark:border-emerald-700 dark:bg-emerald-950/30'
                          : 'border-ink-200 bg-white dark:border-ink-800 dark:bg-ink-900'
                      }`}
                    >
                      <input
                        type="radio"
                        name={`correct-ans-${qIndex}`}
                        checked={q.correct_answer === optIndex}
                        onChange={() => handleCorrectAnswerChange(qIndex, optIndex)}
                        className="h-4 w-4 text-emerald-600 focus:ring-emerald-500"
                      />
                      <input
                        type="text"
                        value={opt}
                        onChange={(e) => handleOptionChange(qIndex, optIndex, e.target.value)}
                        placeholder={`Option ${optIndex + 1}`}
                        className="flex-1 bg-transparent text-xs text-ink-900 placeholder:text-ink-400 focus:outline-none dark:text-ink-100"
                        required
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Explanation Field */}
              <div>
                <label className="block text-xs font-semibold text-ink-700 dark:text-ink-300 mb-1">
                  Explanation for Solution Key (Shown after student submission)
                </label>
                <input
                  type="text"
                  value={q.explanation || ''}
                  onChange={(e) => handleExplanationChange(qIndex, e.target.value)}
                  placeholder="Pedagogical explanation of why the correct choice is accurate..."
                  className="w-full rounded-xl border border-ink-200 bg-white px-3 py-1.5 text-xs text-ink-900 placeholder:text-ink-400 focus:border-brand-500 focus:outline-none dark:border-ink-800 dark:bg-ink-900 dark:text-ink-100"
                />
              </div>
            </Card>
          ))}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-ink-200 dark:border-ink-800">
          <Link to="/instructor/assessments">
            <Button type="button" variant="outline" size="md">
              Cancel
            </Button>
          </Link>
          <div className="flex items-center gap-3">
            <Button
              type="submit"
              variant="primary"
              size="lg"
              disabled={saving}
            >
              {saving ? <LoadingSpinner size={18} /> : <Save size={18} />}
              Save & Publish Assessment
            </Button>
          </div>
        </div>
      </form>
    </div>
  )
}

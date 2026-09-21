import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ChevronLeft, ChevronRight, RotateCcw, Layers, Sparkles } from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import Card from '../components/Card.jsx'
import Select from '../components/Select.jsx'
import Button from '../components/Button.jsx'
import Flashcard from '../components/Flashcard.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import EmptyState from '../components/EmptyState.jsx'
import { getFlashcards, generateFlashcards, recordFlashcardReview, getMaterials } from '../services/api.js'
import { useToast } from '../context/ToastContext.jsx'

const difficulties = [
  { label: 'Easy', value: 'easy', tone: 'bg-emerald-600 hover:bg-emerald-700' },
  { label: 'Medium', value: 'medium', tone: 'bg-amber-500 hover:bg-amber-600' },
  { label: 'Hard', value: 'hard', tone: 'bg-rose-600 hover:bg-rose-700' },
]

export default function Flashcards() {
  const [searchParams] = useSearchParams()
  const toast = useToast()

  const [materials, setMaterials] = useState([])
  const [materialId, setMaterialId] = useState(searchParams.get('material') || 'data-structures')
  const [cards, setCards] = useState([])
  const [index, setIndex] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [ratings, setRatings] = useState({})
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    getMaterials().then(setMaterials).catch(() => setMaterials([]))
  }, [])

  useEffect(() => {
    setLoading(true)
    getFlashcards(materialId)
      .then((data) => {
        setCards(data)
        setIndex(0)
        setFlipped(false)
        setRatings({})
      })
      .finally(() => setLoading(false))
  }, [materialId])

  const go = (step) => {
    setFlipped(false)
    setIndex((i) => Math.min(cards.length - 1, Math.max(0, i + step)))
  }

  const rate = async (value) => {
    const card = cards[index]
    setRatings((r) => ({ ...r, [card.id]: value }))
    const topicLabel = card.topic || card.topic_name || 'Card'
    toast(`Marked "${topicLabel}" as ${value}`, 'success')
    try {
      await recordFlashcardReview(card.id, value)
    } catch {
      /* ignore background review logging error */
    }
    if (index < cards.length - 1) go(1)
  }

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      const newCards = await generateFlashcards({ materialId, count: 5 })
      setCards(newCards)
      setIndex(0)
      setFlipped(false)
      setRatings({})
      toast('Generated high-yield flashcards with AI!', 'success')
    } catch (err) {
      toast(err.message || 'Could not generate flashcards.', 'error')
    } finally {
      setGenerating(false)
    }
  }

  const restart = () => {
    setIndex(0)
    setFlipped(false)
    setRatings({})
  }

  const materialOptions = materials.length
    ? materials.map((m) => ({ value: m.id, label: m.title }))
    : [{ value: 'data-structures', label: 'Data Structures' }]

  const reviewed = Object.keys(ratings).length

  return (
    <>
      <PageHeader title="Flashcards" subtitle="Flip a card, then rate how well you recalled it." />

      <div className="mb-6 flex flex-wrap items-center gap-3">
        <div className="sm:w-72">
          <Select
            options={materialOptions}
            value={materialId}
            onChange={(e) => setMaterialId(e.target.value)}
            aria-label="Choose material"
          />
        </div>
        <Button
          variant="secondary"
          icon={Sparkles}
          onClick={handleGenerate}
          loading={generating}
          disabled={loading}
        >
          Generate new cards with AI
        </Button>
      </div>

      {loading ? (
        <LoadingSpinner label="Building your deck…" />
      ) : cards.length === 0 ? (
        <EmptyState
          icon={Layers}
          title="No flashcards for this material yet"
          description="Click below to generate high-yield active recall flashcards with Gemini AI from your study material."
          actionLabel="Generate with AI"
          onAction={handleGenerate}
        />
      ) : (
        <div className="mx-auto max-w-2xl">
          <div className="mb-4 flex items-center justify-between text-sm text-ink-600 dark:text-ink-400">
            <span>
              Card {index + 1} of {cards.length}
            </span>
            <span>{reviewed} reviewed</span>
          </div>
          <ProgressBar value={((index + 1) / cards.length) * 100} size="sm" />

          <div className="mt-6">
            <Flashcard card={cards[index]} flipped={flipped} onFlip={() => setFlipped((f) => !f)} />
          </div>

          <div className="mt-6 flex items-center justify-between gap-3">
            <Button variant="secondary" icon={ChevronLeft} onClick={() => go(-1)} disabled={index === 0}>
              Previous
            </Button>
            <Button variant="ghost" icon={RotateCcw} onClick={restart}>
              Restart
            </Button>
            <Button variant="secondary" onClick={() => go(1)} disabled={index === cards.length - 1}>
              Next
              <ChevronRight size={16} />
            </Button>
          </div>

          <Card className="mt-6">
            <p className="mb-3 text-sm font-medium">How well did you recall this?</p>
            <div className="grid grid-cols-3 gap-3">
              {difficulties.map((d) => (
                <button
                  key={d.value}
                  onClick={() => rate(d.value)}
                  className={`rounded-xl px-3 py-2.5 text-sm font-medium text-white transition-colors ${d.tone} ${
                    ratings[cards[index].id] === d.value ? 'ring-2 ring-offset-2 ring-ink-400 dark:ring-offset-ink-900' : ''
                  }`}
                >
                  {d.label}
                </button>
              ))}
            </div>
            <p className="muted mt-3">Your rating decides how soon the card comes back in a future deck.</p>
          </Card>
        </div>
      )}
    </>
  )
}

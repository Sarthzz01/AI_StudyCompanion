import { RotateCw } from 'lucide-react'

/**
 * Card flips with a CSS 3D transform. Clicking or pressing Enter/Space toggles it.
 */
export default function Flashcard({ card, flipped, onFlip }) {
  return (
    <div className="[perspective:1400px]">
      <div
        role="button"
        tabIndex={0}
        aria-label={flipped ? 'Show question' : 'Show answer'}
        onClick={onFlip}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            onFlip()
          }
        }}
        className={`relative h-72 w-full cursor-pointer rounded-2xl transition-transform duration-500 [transform-style:preserve-3d] ${
          flipped ? '[transform:rotateY(180deg)]' : ''
        }`}
      >
        {/* Front */}
        <div className="absolute inset-0 flex flex-col justify-between rounded-2xl border border-ink-200 bg-white p-6 shadow-card [backface-visibility:hidden] dark:border-ink-800 dark:bg-ink-900">
          <span className="chip w-fit bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300">
            {card.topic}
          </span>
          <p className="font-display text-xl font-semibold leading-snug">{card.front}</p>
          <p className="inline-flex items-center gap-1.5 text-xs text-ink-500">
            <RotateCw size={13} /> Click to reveal the answer
          </p>
        </div>

        {/* Back */}
        <div className="absolute inset-0 flex flex-col justify-between rounded-2xl border border-brand-200 bg-brand-50 p-6 shadow-card [backface-visibility:hidden] [transform:rotateY(180deg)] dark:border-brand-800 dark:bg-brand-950/60">
          <p className="text-sm leading-relaxed text-ink-800 dark:text-ink-100">{card.back}</p>
          <p className="text-xs text-ink-500 dark:text-ink-400">{card.source}</p>
        </div>
      </div>
    </div>
  )
}

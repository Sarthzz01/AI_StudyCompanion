/**
 * One quiz question with its options. Selection is controlled by the parent so
 * answers survive moving back and forth between questions.
 */
export default function QuizCard({ question, index, total, selected, onSelect }) {
  return (
    <div>
      <p className="muted">
        Question {index + 1} of {total} · {question.topic}
      </p>
      <h2 className="mt-2 font-display text-xl font-semibold leading-snug">{question.question}</h2>

      <fieldset className="mt-6 space-y-3">
        <legend className="sr-only">Answer options</legend>
        {question.options.map((option, i) => {
          const isSelected = selected === i
          return (
            <label
              key={option}
              className={`flex cursor-pointer items-start gap-3 rounded-xl border p-4 text-sm transition-colors ${
                isSelected
                  ? 'border-brand-500 bg-brand-50 dark:bg-brand-950/50'
                  : 'border-ink-200 hover:border-brand-300 hover:bg-ink-50 dark:border-ink-800 dark:hover:bg-ink-800/50'
              }`}
            >
              <input
                type="radio"
                name={`q-${question.id}`}
                className="mt-0.5 h-4 w-4 accent-brand-600"
                checked={isSelected}
                onChange={() => onSelect(i)}
              />
              <span>{option}</span>
            </label>
          )
        })}
      </fieldset>
    </div>
  )
}

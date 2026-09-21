import { Bot, User, FileText } from 'lucide-react'

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <span
        className={`mt-0.5 h-8 w-8 shrink-0 rounded-lg p-1.5 ${
          isUser
            ? 'bg-ink-200 text-ink-700 dark:bg-ink-800 dark:text-ink-200'
            : 'bg-brand-600 text-white'
        }`}
      >
        {isUser ? <User size={20} /> : <Bot size={20} />}
      </span>

      <div className={`max-w-[46rem] ${isUser ? 'text-right' : ''}`}>
        <div
          className={`inline-block whitespace-pre-line rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? 'bg-brand-600 text-white'
              : 'border border-ink-200 bg-white text-ink-800 dark:border-ink-800 dark:bg-ink-900 dark:text-ink-200'
          }`}
        >
          {message.content}
        </div>

        {message.sources?.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {message.sources.map((s, i) => (
              <span
                key={`${s.label}-${i}`}
                className="chip border border-ink-200 bg-ink-50 text-ink-600 dark:border-ink-800 dark:bg-ink-900 dark:text-ink-300"
              >
                <FileText size={12} />
                {s.label} — {s.page}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

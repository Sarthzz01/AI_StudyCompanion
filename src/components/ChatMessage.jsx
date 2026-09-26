import { useState } from 'react'
import { Bot, User, FileText, Check, Copy } from 'lucide-react'

function CodeBlock({ language, code }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.warn('Failed to copy code', err)
    }
  }

  return (
    <div className="my-3 overflow-hidden rounded-xl border border-ink-800 bg-ink-950 text-ink-100 shadow-md">
      {/* Code Header Bar */}
      <div className="flex items-center justify-between border-b border-ink-800/80 bg-ink-900/90 px-4 py-1.5 text-xs text-ink-400">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-red-500/80" />
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500/80" />
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/80" />
          </div>
          <span className="font-mono text-[11px] uppercase tracking-wider font-semibold text-ink-300 ml-1">
            {language || 'code'}
          </span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium text-ink-400 transition hover:bg-ink-800 hover:text-white"
        >
          {copied ? (
            <>
              <Check size={12} className="text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy size={12} />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      {/* Code Content */}
      <pre className="overflow-x-auto p-4 font-mono text-xs leading-relaxed text-ink-100">
        <code>{code}</code>
      </pre>
    </div>
  )
}

function formatInline(text) {
  if (!text) return ''
  // Split on bold, inline code, or bullet markers
  const tokens = text.split(/(\*\*.*?\*\*|`.*?`)/g)
  return tokens.map((tok, i) => {
    if (tok.startsWith('**') && tok.endsWith('**') && tok.length >= 4) {
      return (
        <strong key={i} className="font-semibold text-ink-900 dark:text-white">
          {tok.slice(2, -2)}
        </strong>
      )
    }
    if (tok.startsWith('`') && tok.endsWith('`') && tok.length >= 2) {
      return (
        <code
          key={i}
          className="rounded-md bg-brand-50 border border-brand-200/60 px-1.5 py-0.5 font-mono text-xs font-medium text-brand-700 dark:border-brand-900/50 dark:bg-brand-950/60 dark:text-brand-300"
        >
          {tok.slice(1, -1)}
        </code>
      )
    }
    return tok
  })
}

function FormattedContent({ text, isUser }) {
  if (isUser) {
    return <div className="whitespace-pre-wrap">{text}</div>
  }

  // Split code blocks
  const parts = text.split(/(```[\s\S]*?```)/g)
  return (
    <div className="space-y-2 text-left text-sm leading-relaxed">
      {parts.map((part, index) => {
        if (part.startsWith('```') && part.endsWith('```')) {
          const lines = part.slice(3, -3).trim().split('\n')
          const firstLine = lines[0].trim()
          const isLang = /^[a-zA-Z0-9_-]+$/.test(firstLine)
          const codeContent = isLang ? lines.slice(1).join('\n') : lines.join('\n')
          return (
            <CodeBlock
              key={index}
              language={isLang ? firstLine : ''}
              code={codeContent}
            />
          )
        }

        return (
          <div key={index} className="whitespace-pre-line leading-relaxed text-ink-800 dark:text-ink-200">
            {formatInline(part)}
          </div>
        )
      })}
    </div>
  )
}

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  const [copiedMsg, setCopiedMsg] = useState(false)

  const handleCopyMessage = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopiedMsg(true)
      setTimeout(() => setCopiedMsg(false), 2000)
    } catch (err) {
      console.warn('Could not copy message:', err)
    }
  }

  return (
    <div className={`group flex gap-3.5 transition-opacity ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl shadow-xs transition-transform duration-200 group-hover:scale-105 ${
          isUser
            ? 'bg-gradient-to-tr from-brand-600 to-indigo-600 text-white shadow-brand-500/20'
            : 'bg-gradient-to-br from-indigo-600 via-brand-600 to-purple-600 text-white shadow-indigo-500/20'
        }`}
      >
        {isUser ? <User size={18} /> : <Bot size={19} />}
      </div>

      {/* Message Box */}
      <div className={`max-w-[48rem] ${isUser ? 'text-right' : 'text-left'}`}>
        <div
          className={`relative inline-block rounded-2xl px-4 py-3 shadow-xs transition-all ${
            isUser
              ? 'bg-gradient-to-r from-brand-600 to-indigo-600 text-white rounded-tr-sm'
              : 'border border-ink-200/90 bg-white text-ink-900 rounded-tl-sm shadow-sm dark:border-ink-800/80 dark:bg-ink-900/90 dark:text-ink-100'
          }`}
        >
          <FormattedContent text={message.content} isUser={isUser} />

          {/* Copy Message Action Button on Assistant message */}
          {!isUser && (
            <div className="mt-2.5 flex items-center justify-between border-t border-ink-100/80 pt-2 opacity-0 transition-opacity group-hover:opacity-100 dark:border-ink-800/80">
              <button
                onClick={handleCopyMessage}
                className="flex items-center gap-1 text-[11px] font-medium text-ink-400 transition hover:text-brand-600 dark:hover:text-brand-400"
                title="Copy entire response"
              >
                {copiedMsg ? (
                  <>
                    <Check size={12} className="text-emerald-500" />
                    <span className="text-emerald-500">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy size={12} />
                    <span>Copy message</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Citations & Sources */}
        {message.sources?.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {message.sources.map((s, i) => (
              <span
                key={`${s.label}-${i}`}
                className="chip border border-brand-200/70 bg-brand-50/60 text-[11px] text-brand-700 shadow-2xs dark:border-brand-900/50 dark:bg-brand-950/40 dark:text-brand-300"
              >
                <FileText size={12} className="text-brand-500" />
                {s.label} — {s.page}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

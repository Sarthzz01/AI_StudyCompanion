import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Send, Mic, Bot, Sparkles } from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import Card from '../components/Card.jsx'
import Select from '../components/Select.jsx'
import Button from '../components/Button.jsx'
import ChatMessage from '../components/ChatMessage.jsx'
import { askTutor, getMaterials } from '../services/api.js'
import { suggestedQuestions } from '../data/mockTutor.js'
import { useToast } from '../context/ToastContext.jsx'

export default function Tutor() {
  const [searchParams] = useSearchParams()
  const toast = useToast()
  const scrollRef = useRef(null)

  const [materials, setMaterials] = useState([])
  const [materialId, setMaterialId] = useState(searchParams.get('material') || 'data-structures')
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Ask me anything from your study material. I answer from the material you have selected and show which page the answer came from.',
      sources: [],
    },
  ])
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)

  useEffect(() => {
    getMaterials().then(setMaterials).catch(() => setMaterials([]))
  }, [])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, thinking])

  const send = async (question) => {
    const text = (question ?? input).trim()
    if (!text || thinking) return

    setMessages((list) => [...list, { id: `u-${Date.now()}`, role: 'user', content: text }])
    setInput('')
    setThinking(true)

    try {
      const { answer, sources } = await askTutor({ question: text, materialId })
      setMessages((list) => [...list, { id: `a-${Date.now()}`, role: 'assistant', content: answer, sources }])
    } catch (err) {
      toast(err.message || 'The tutor could not answer that. Try again.', 'error')
    } finally {
      setThinking(false)
    }
  }

  const materialOptions = materials.length
    ? materials.map((m) => ({ value: m.id, label: m.title }))
    : [{ value: 'data-structures', label: 'Data Structures' }]

  return (
    <>
      <PageHeader title="AI Tutor" subtitle="Answers grounded in your own material, with sources." />

      <div className="grid gap-5 lg:grid-cols-4">
        <Card className="lg:col-span-1">
          <Select
            label="Material"
            options={materialOptions}
            value={materialId}
            onChange={(e) => setMaterialId(e.target.value)}
          />
          <p className="muted mt-3">
            The tutor only answers from the selected material, so switch it before asking about another subject.
          </p>

          <h3 className="mt-6 text-sm font-semibold">Try asking</h3>
          <div className="mt-2 space-y-2">
            {suggestedQuestions.map((q) => (
              <button
                key={q}
                onClick={() => send(q)}
                disabled={thinking}
                className="flex w-full items-start gap-2 rounded-lg border border-ink-200 px-3 py-2 text-left text-sm hover:border-brand-300 hover:bg-brand-50 disabled:opacity-50 dark:border-ink-800 dark:hover:bg-brand-950/40"
              >
                <Sparkles size={14} className="mt-0.5 shrink-0 text-brand-600" />
                {q}
              </button>
            ))}
          </div>
        </Card>

        <Card className="flex h-[70vh] flex-col lg:col-span-3">
          <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto pr-1">
            {messages.map((m) => (
              <ChatMessage key={m.id} message={m} />
            ))}

            {thinking && (
              <div className="flex items-center gap-3">
                <span className="h-8 w-8 rounded-lg bg-brand-600 p-1.5 text-white">
                  <Bot size={20} />
                </span>
                <div className="flex items-center gap-1.5 rounded-2xl border border-ink-200 px-4 py-3 dark:border-ink-800">
                  {[0, 150, 300].map((delay) => (
                    <span
                      key={delay}
                      className="h-2 w-2 animate-bounce rounded-full bg-ink-400"
                      style={{ animationDelay: `${delay}ms` }}
                    />
                  ))}
                  <span className="ml-1 text-xs text-ink-500">Searching your material…</span>
                </div>
              </div>
            )}
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault()
              send()
            }}
            className="mt-4 flex items-end gap-2 border-t border-ink-200 pt-4 dark:border-ink-800"
          >
            <textarea
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  send()
                }
              }}
              placeholder="Ask a question about this material…"
              aria-label="Your question"
              className="field max-h-32 flex-1 resize-none"
            />
            <Button
              type="button"
              variant="secondary"
              icon={Mic}
              aria-label="Voice input"
              onClick={() => toast('Voice input arrives with the backend.', 'info')}
            />
            <Button type="submit" icon={Send} disabled={!input.trim() || thinking}>
              Send
            </Button>
          </form>
        </Card>
      </div>
    </>
  )
}

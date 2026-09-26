import { useEffect, useRef, useState, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Send,
  Bot,
  AlertCircle,
  RotateCcw,
  Trash2,
  Plus,
  MessageSquare,
  Loader2,
  Search,
  BookOpen,
  X,
  Edit3,
  Check,
} from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import Card from '../components/Card.jsx'
import Button from '../components/Button.jsx'
import ChatMessage from '../components/ChatMessage.jsx'
import {
  askTutor,
  getMaterials,
  getTutorConversations,
  getTutorConversation,
  deleteTutorConversation,
  renameTutorConversation,
} from '../services/api.js'
import { useToast } from '../context/ToastContext.jsx'

const INITIAL_WELCOME = {
  id: 'welcome',
  role: 'assistant',
  content: 'Hello! I am your AI Tutor. What would you like to learn today?',
  sources: [],
}

export default function Tutor() {
  const [searchParams] = useSearchParams()
  const toast = useToast()
  const scrollRef = useRef(null)
  const inputRef = useRef(null)

  // Scope & materials
  const [materials, setMaterials] = useState([])
  const [materialId, setMaterialId] = useState(searchParams.get('material') || 'general')

  // Conversation history sessions (ChatGPT style)
  const [conversations, setConversations] = useState([])
  const [currentConversationId, setCurrentConversationId] = useState(null)
  const [conversationTitle, setConversationTitle] = useState('New Chat')
  const [loadingConversations, setLoadingConversations] = useState(false)
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  // Renaming state
  const [renamingConvId, setRenamingConvId] = useState(null)
  const [renameInput, setRenameInput] = useState('')

  // Current active chat messages
  const [messages, setMessages] = useState([INITIAL_WELCOME])
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const [error, setError] = useState(null)

  // Load materials catalogue
  useEffect(() => {
    getMaterials()
      .then((data) => setMaterials(Array.isArray(data) ? data : []))
      .catch(() => setMaterials([]))
  }, [])

  // Load user conversation threads on mount
  useEffect(() => {
    loadConversationList()
  }, [])

  const loadConversationList = async () => {
    setLoadingConversations(true)
    try {
      const list = await getTutorConversations()
      setConversations(list)
    } catch (err) {
      console.warn('Could not load tutor conversations:', err)
    } finally {
      setLoadingConversations(false)
    }
  }

  // Filter conversations by search term
  const filteredConversations = useMemo(() => {
    if (!searchQuery.trim()) return conversations
    const q = searchQuery.toLowerCase()
    return conversations.filter(
      (c) =>
        (c.title && c.title.toLowerCase().includes(q)) ||
        (c.last_message && c.last_message.toLowerCase().includes(q))
    )
  }, [conversations, searchQuery])

  // Auto-scroll when messages update
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth',
      })
    }
  }, [messages, thinking, error])

  // Start a fresh chat
  const startNewChat = () => {
    setCurrentConversationId(null)
    setConversationTitle('New Chat')
    setMessages([INITIAL_WELCOME])
    setError(null)
    setInput('')
    setRenamingConvId(null)
    setTimeout(() => inputRef.current?.focus(), 50)
  }

  // Load an existing conversation thread
  const selectConversation = async (convId) => {
    if (convId === currentConversationId) return
    setLoadingMessages(true)
    setError(null)
    setRenamingConvId(null)

    try {
      const msgs = await getTutorConversation(convId)
      if (Array.isArray(msgs) && msgs.length > 0) {
        const loadedMessages = msgs
          .map((item) => [
            {
              id: `u-${item.id}`,
              role: 'user',
              content: item.question,
            },
            {
              id: `a-${item.id}`,
              role: 'assistant',
              content: item.answer,
              sources: item.sources || [],
            },
          ])
          .flat()

        setMessages(loadedMessages)
        setCurrentConversationId(convId)

        // Find conversation title from list
        const match = conversations.find((c) => c.conversation_id === convId)
        if (match) {
          setConversationTitle(match.title || 'Conversation')
          if (match.material_id && match.material_id !== 'general') {
            setMaterialId(match.material_id)
          }
        }
      } else {
        startNewChat()
      }
    } catch (err) {
      toast('Failed to load conversation.', 'error')
    } finally {
      setLoadingMessages(false)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }

  // Delete an entire conversation thread
  const handleDeleteConversation = async (e, convId) => {
    e.stopPropagation()
    try {
      await deleteTutorConversation(convId)
      setConversations((prev) => prev.filter((c) => c.conversation_id !== convId))
      toast('Conversation deleted', 'info')

      if (currentConversationId === convId) {
        startNewChat()
      }
    } catch (err) {
      toast('Failed to delete conversation', 'error')
    }
  }

  // Rename a conversation thread
  const startRename = (e, c) => {
    e.stopPropagation()
    setRenamingConvId(c.conversation_id)
    setRenameInput(c.title || '')
  }

  const saveRename = async (e, convId) => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    const trimmed = renameInput.trim()
    if (!trimmed) {
      setRenamingConvId(null)
      return
    }
    try {
      await renameTutorConversation(convId, trimmed)
      setConversations((prev) =>
        prev.map((c) => (c.conversation_id === convId ? { ...c, title: trimmed } : c))
      )
      if (currentConversationId === convId) {
        setConversationTitle(trimmed)
      }
      toast('Chat renamed', 'success')
    } catch (err) {
      toast('Failed to rename chat', 'error')
    } finally {
      setRenamingConvId(null)
    }
  }

  const cancelRename = (e) => {
    if (e) e.stopPropagation()
    setRenamingConvId(null)
  }

  // Send a question to the AI Tutor
  const send = async (question) => {
    const text = (question ?? input).trim()
    if (!text || thinking) return

    setError(null)
    const userMsg = { id: `u-${Date.now()}`, role: 'user', content: text }

    setMessages((list) => [...list, userMsg])
    setInput('')
    setThinking(true)

    // Build context history
    const historyPayload = messages
      .filter((m) => m.id !== 'welcome' && (m.role === 'user' || m.role === 'assistant'))
      .slice(-8)
      .map((m) => ({ role: m.role, content: m.content }))

    try {
      const response = await askTutor({
        message: text,
        materialId: materialId === 'general' ? undefined : materialId,
        conversation_id: currentConversationId,
        history: historyPayload,
      })

      const newConvId = response.conversation_id || currentConversationId
      const newTitle = response.title || text.slice(0, 40)

      setMessages((list) => [
        ...list,
        {
          id: `a-${Date.now()}`,
          role: 'assistant',
          content: response.answer,
          sources: response.sources || [],
        },
      ])

      // If this was a new conversation, update active conversation state and sidebar
      if (!currentConversationId && newConvId) {
        setCurrentConversationId(newConvId)
        setConversationTitle(newTitle)
        setConversations((prev) => [
          {
            conversation_id: newConvId,
            title: newTitle,
            last_message: text,
            updated_at: 'Just now',
            message_count: 1,
            material_id: materialId,
          },
          ...prev,
        ])
      } else {
        // Update existing conversation timestamp in sidebar list
        setConversations((prev) =>
          prev.map((c) =>
            c.conversation_id === newConvId
              ? { ...c, updated_at: 'Just now', last_message: text }
              : c
          )
        )
      }
    } catch (err) {
      const errMsg = err.message || 'The AI Tutor could not answer that. Please try again.'
      setError(errMsg)
      toast(errMsg, 'error')
    } finally {
      setThinking(false)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }

  const materialOptions = [
    { value: 'general', label: '🌐 All Subjects & General Knowledge' },
    ...materials.map((m) => ({ value: m.id, label: `📄 ${m.title}` })),
  ]

  const activeMaterial = materials.find((m) => m.id === materialId)

  return (
    <>
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between mb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink-900 dark:text-white flex items-center gap-2.5">
            AI Tutor
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Online
            </span>
          </h1>
          <p className="text-xs text-ink-500 dark:text-ink-400 mt-0.5">
            Conversational academic AI tutor powered by OpenAI.
          </p>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-4">
        {/* Left Sidebar: ChatGPT-style Chat History */}
        <Card className="flex h-[78vh] flex-col p-3.5 lg:col-span-1 border border-ink-200/80 bg-white/95 shadow-sm dark:border-ink-800/80 dark:bg-ink-900/90">
          {/* New Chat Button */}
          <button
            onClick={startNewChat}
            className="group relative flex w-full items-center justify-between gap-2 overflow-hidden rounded-xl bg-gradient-to-r from-brand-600 via-brand-500 to-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-md shadow-brand-500/20 transition-all duration-200 hover:from-brand-500 hover:to-indigo-500 hover:shadow-lg hover:shadow-brand-500/30 active:scale-[0.98]"
          >
            <span className="flex items-center gap-2">
              <Plus size={18} className="transition-transform duration-200 group-hover:rotate-90" />
              New Chat
            </span>
            <span className="rounded-md bg-white/20 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-white">
              AI
            </span>
          </button>

          {/* Search Bar for History */}
          <div className="relative mt-3">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search chat history…"
              className="w-full rounded-lg border border-ink-200/90 bg-ink-50/70 py-1.5 pl-8 pr-7 text-xs text-ink-800 placeholder:text-ink-400 focus:border-brand-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-ink-800 dark:bg-ink-950/60 dark:text-ink-200 dark:focus:bg-ink-900"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-ink-400 hover:text-ink-600 dark:hover:text-ink-200"
              >
                <X size={12} />
              </button>
            )}
          </div>

          {/* Section Header */}
          <div className="mt-3 flex items-center justify-between px-1">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-ink-400 dark:text-ink-500">
              Recent Chats
            </span>
            {conversations.length > 0 && (
              <span className="rounded-full bg-ink-100 px-2 py-0.2 text-[10px] font-semibold text-ink-600 dark:bg-ink-800 dark:text-ink-300">
                {filteredConversations.length}
              </span>
            )}
          </div>

          {/* Conversations List */}
          <div className="mt-2 flex-1 space-y-1 overflow-y-auto pr-1">
            {loadingConversations ? (
              <div className="flex h-32 flex-col items-center justify-center gap-2 text-xs text-ink-500">
                <Loader2 size={16} className="animate-spin text-brand-600" />
                <span>Loading history…</span>
              </div>
            ) : filteredConversations.length === 0 ? (
              <div className="flex h-40 flex-col items-center justify-center px-2 text-center text-xs text-ink-400 dark:text-ink-500">
                <MessageSquare size={24} className="mb-2 text-ink-300 dark:text-ink-700" />
                <p className="font-medium text-ink-600 dark:text-ink-400">
                  {searchQuery ? 'No matching chats' : 'No chat history yet'}
                </p>
                <p className="mt-0.5 text-[11px]">
                  {searchQuery ? 'Try a different keyword' : 'Start a chat to save your history.'}
                </p>
              </div>
            ) : (
              filteredConversations.map((c) => {
                const isActive = currentConversationId === c.conversation_id
                const isRenaming = renamingConvId === c.conversation_id

                return (
                  <div
                    key={c.conversation_id}
                    onClick={() => selectConversation(c.conversation_id)}
                    className={`group relative flex cursor-pointer items-center justify-between rounded-xl px-3 py-2 text-xs transition-all duration-150 ${
                      isActive
                        ? 'border-l-[3px] border-brand-600 bg-gradient-to-r from-brand-50 to-indigo-50/40 font-semibold text-brand-950 shadow-2xs dark:border-brand-500 dark:from-brand-950/70 dark:to-indigo-950/40 dark:text-brand-100'
                        : 'border-l-[3px] border-transparent text-ink-700 hover:bg-ink-100/70 hover:text-ink-900 dark:text-ink-300 dark:hover:bg-ink-800/50 dark:hover:text-ink-100'
                    }`}
                  >
                    {isRenaming ? (
                      <form
                        onSubmit={(e) => saveRename(e, c.conversation_id)}
                        onClick={(e) => e.stopPropagation()}
                        className="flex items-center gap-1 w-full"
                      >
                        <input
                          type="text"
                          autoFocus
                          value={renameInput}
                          onChange={(e) => setRenameInput(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Escape') cancelRename(e)
                          }}
                          className="w-full rounded-md border border-brand-500 bg-white px-2 py-0.5 text-xs text-ink-900 focus:outline-none dark:bg-ink-950 dark:text-white"
                        />
                        <button
                          type="submit"
                          title="Save title"
                          className="rounded p-1 text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950/40"
                        >
                          <Check size={13} />
                        </button>
                        <button
                          type="button"
                          onClick={cancelRename}
                          title="Cancel"
                          className="rounded p-1 text-ink-400 hover:bg-ink-100 dark:hover:bg-ink-800"
                        >
                          <X size={13} />
                        </button>
                      </form>
                    ) : (
                      <>
                        <div className="flex items-center gap-2.5 min-w-0 pr-14">
                          <MessageSquare
                            size={14}
                            className={`shrink-0 transition-colors ${
                              isActive
                                ? 'text-brand-600 dark:text-brand-400'
                                : 'text-ink-400 group-hover:text-brand-500'
                            }`}
                          />
                          <div className="truncate text-left">
                            <p className="truncate leading-tight font-medium">
                              {c.title || 'Conversation'}
                            </p>
                            <span className="text-[10px] text-ink-400 dark:text-ink-500 font-normal">
                              {c.updated_at || 'Recent'}
                            </span>
                          </div>
                        </div>

                        {/* Action buttons on hover */}
                        <div className="absolute right-1.5 flex items-center gap-0.5 opacity-0 transition-all group-hover:opacity-100">
                          <button
                            onClick={(e) => startRename(e, c)}
                            title="Rename chat"
                            className="rounded-md p-1 text-ink-400 hover:bg-ink-200/70 hover:text-ink-800 dark:hover:bg-ink-800 dark:hover:text-ink-100"
                          >
                            <Edit3 size={13} />
                          </button>
                          <button
                            onClick={(e) => handleDeleteConversation(e, c.conversation_id)}
                            title="Delete chat"
                            className="rounded-md p-1 text-ink-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/50 dark:hover:text-red-400"
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                )
              })
            )}
          </div>

          {/* Scope Selector in Footer of Sidebar */}
          <div className="mt-auto border-t border-ink-100/80 pt-3 dark:border-ink-800/80">
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-[11px] font-semibold uppercase tracking-wider text-ink-500 dark:text-ink-400 flex items-center gap-1.5">
                <BookOpen size={12} className="text-brand-600" />
                Learning Scope
              </label>
            </div>
            <select
              value={materialId}
              onChange={(e) => setMaterialId(e.target.value)}
              className="field text-xs py-1.5 px-2 bg-ink-50/50 dark:bg-ink-950/40 rounded-lg border-ink-200 dark:border-ink-800"
            >
              {materialOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </Card>

        {/* Right Main Chat Area */}
        <Card className="flex h-[78vh] flex-col p-4 lg:col-span-3 border border-ink-200/80 bg-white/95 shadow-sm dark:border-ink-800/80 dark:bg-ink-900/90">
          {/* Header of Active Chat */}
          <div className="flex items-center justify-between border-b border-ink-100/90 pb-3 dark:border-ink-800/90">
            <div className="flex items-center gap-3 min-w-0">
              <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-600 text-white shadow-sm shadow-brand-500/20">
                <Bot size={19} />
                <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-white bg-emerald-500 dark:border-ink-900" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h2 className="truncate text-sm font-semibold text-ink-900 dark:text-white">
                    {conversationTitle}
                  </h2>
                  {currentConversationId && (
                    <button
                      onClick={() => {
                        const match = conversations.find((c) => c.conversation_id === currentConversationId)
                        if (match) startRename({ stopPropagation: () => {} }, match)
                      }}
                      title="Rename this conversation"
                      className="rounded p-1 text-ink-400 hover:bg-ink-100 hover:text-ink-800 dark:hover:bg-ink-800 dark:hover:text-ink-100 transition-colors"
                    >
                      <Edit3 size={13} />
                    </button>
                  )}
                  <span className="rounded-full bg-brand-50 px-2 py-0.5 text-[10px] font-semibold text-brand-700 dark:bg-brand-950/80 dark:text-brand-300 border border-brand-200/50 dark:border-brand-800/50">
                    GPT-4o Tutor
                  </span>
                </div>
                <p className="truncate text-[11px] text-ink-500 dark:text-ink-400">
                  {materialId === 'general'
                    ? 'General Academic & Coding Knowledge'
                    : `Grounded in: ${activeMaterial?.title || 'Selected Document'}`}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={startNewChat}
                className="flex items-center gap-1.5 rounded-lg border border-ink-200/80 bg-white px-2.5 py-1.5 text-xs font-medium text-ink-700 shadow-2xs transition hover:border-brand-300 hover:bg-brand-50/50 hover:text-brand-600 dark:border-ink-800 dark:bg-ink-900 dark:text-ink-300 dark:hover:bg-ink-800"
              >
                <Plus size={13} />
                <span className="hidden sm:inline">New Chat</span>
              </button>
            </div>
          </div>

          {/* Messages Stream */}
          <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto py-4 pr-1">
            {loadingMessages ? (
              <div className="flex h-full flex-col items-center justify-center gap-2 text-sm text-ink-500">
                <Loader2 size={24} className="animate-spin text-brand-600" />
                <span className="text-xs font-medium">Loading conversation messages…</span>
              </div>
            ) : (
              messages.map((m) => <ChatMessage key={m.id} message={m} />)
            )}

            {/* Thinking Indicator */}
            {thinking && (
              <div className="flex items-center gap-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-brand-600 text-white shadow-sm shadow-brand-500/20">
                  <Bot size={18} />
                </span>
                <div className="flex items-center gap-2.5 rounded-2xl border border-ink-200/90 bg-white px-4 py-3 shadow-xs dark:border-ink-800 dark:bg-ink-900">
                  <div className="flex items-center gap-1">
                    {[0, 150, 300].map((delay) => (
                      <span
                        key={delay}
                        className="h-2 w-2 animate-bounce rounded-full bg-brand-600"
                        style={{ animationDelay: `${delay}ms` }}
                      />
                    ))}
                  </div>
                  <span className="text-xs font-medium text-ink-600 dark:text-ink-400">
                    AI Tutor is formulating an explanation…
                  </span>
                </div>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="flex items-start gap-2.5 rounded-xl border border-red-200 bg-red-50/80 p-3.5 text-xs text-red-800 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
                <AlertCircle size={16} className="mt-0.5 shrink-0 text-red-600 dark:text-red-400" />
                <div className="flex-1">
                  <div className="font-semibold">Unable to get answer</div>
                  <div className="mt-0.5">{error}</div>
                </div>
                <Button
                  size="sm"
                  variant="secondary"
                  icon={RotateCcw}
                  onClick={() => {
                    const lastUser = [...messages].reverse().find((m) => m.role === 'user')
                    if (lastUser) send(lastUser.content)
                  }}
                >
                  Retry
                </Button>
              </div>
            )}
          </div>

          {/* ChatGPT-style Floating Prompt Input Form */}
          <div className="border-t border-ink-100/90 pt-3 dark:border-ink-800/90">
            <form
              onSubmit={(e) => {
                e.preventDefault()
                send()
              }}
              className="relative flex items-center rounded-2xl border border-ink-200/90 bg-ink-50/40 p-1.5 shadow-xs transition-all focus-within:border-brand-500 focus-within:bg-white focus-within:ring-4 focus-within:ring-brand-500/15 dark:border-ink-800 dark:bg-ink-950/50 dark:focus-within:bg-ink-900"
            >
              <textarea
                ref={inputRef}
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    if (input.trim() && !thinking) {
                      send()
                    }
                  }
                }}
                placeholder={
                  materialId === 'general'
                    ? 'Ask anything (e.g., Explain binary search trees, solve this equation)…'
                    : `Ask a question grounded in ${activeMaterial?.title || 'this study material'}…`
                }
                aria-label="Your question"
                disabled={thinking}
                className="w-full resize-none border-0 bg-transparent py-2 pl-3 pr-12 text-xs sm:text-sm text-ink-900 placeholder:text-ink-400 focus:outline-none focus:ring-0 disabled:opacity-60 dark:text-ink-100"
              />
              <button
                type="submit"
                disabled={!input.trim() || thinking}
                aria-label="Send question"
                className="absolute right-2.5 flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-r from-brand-600 to-indigo-600 text-white shadow-xs transition-all hover:from-brand-500 hover:to-indigo-500 hover:scale-105 active:scale-95 disabled:opacity-30 disabled:scale-100 disabled:cursor-not-allowed"
              >
                {thinking ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Send size={15} className="ml-0.5" />
                )}
              </button>
            </form>
            <div className="mt-2 flex items-center justify-between px-1 text-[10px] text-ink-400 dark:text-ink-500">
              <span>↵ Enter to send • Shift + ↵ for new line</span>
              <span>OpenAI Responses API</span>
            </div>
          </div>
        </Card>
      </div>
    </>
  )
}

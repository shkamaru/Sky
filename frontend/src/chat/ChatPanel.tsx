import { useState, useEffect, useRef } from 'react'
import { useAppStore } from '../store/useAppStore'

interface Message {
  role: 'user' | 'assistant' | 'agent'
  content: string
}

export default function ChatPanel({ nodeId, onClose }: { nodeId: number; onClose: () => void }) {
  const { activeModel } = useAppStore()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetch(`/api/chat/${nodeId}/history`)
      .then((r) => r.json())
      .then((d) => setMessages(d.messages || []))
  }, [nodeId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || streaming) return
    const userMsg = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }])
    setStreaming(true)

    const res = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ node_id: nodeId, message: userMsg, model: activeModel }),
    })

    const reader = res.body!.getReader()
    const decoder = new TextDecoder()
    let assistantMsg = ''
    setMessages((prev) => [...prev, { role: 'assistant', content: '' }])

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const token = decoder.decode(value)
      assistantMsg += token
      setMessages((prev) => {
        const updated = [...prev]
        updated[updated.length - 1] = { role: 'assistant', content: assistantMsg }
        return updated
      })
    }
    setStreaming(false)
  }

  return (
    <div className="flex flex-col h-full bg-[#0d0d1a] border-l border-[#2a2a4a]">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#2a2a4a]">
        <span className="text-sm text-[#a78bfa] font-medium">Sky</span>
        <button
          onClick={onClose}
          className="text-[#6b7280] hover:text-white text-lg leading-none"
        >
          ×
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <p className="text-[#4b5563] text-sm text-center mt-8">
            Start a conversation…
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] px-3 py-2 rounded-lg text-sm leading-relaxed whitespace-pre-wrap ${
                msg.role === 'user'
                  ? 'bg-[#6c63ff] text-white'
                  : 'bg-[#1a1a2e] text-[#e2e8f0] border border-[#2a2a4a]'
              }`}
            >
              {msg.content}
              {streaming && i === messages.length - 1 && msg.role === 'assistant' && (
                <span className="animate-pulse">▌</span>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-[#2a2a4a]">
        <div className="flex gap-2">
          <textarea
            className="flex-1 bg-[#1a1a2e] text-[#e2e8f0] border border-[#2a2a4a] rounded-lg px-3 py-2 text-sm resize-none outline-none focus:border-[#6c63ff] transition-colors"
            rows={2}
            placeholder="Message Sky…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                sendMessage()
              }
            }}
          />
          <button
            onClick={sendMessage}
            disabled={streaming || !input.trim()}
            className="px-3 py-2 bg-[#6c63ff] text-white rounded-lg text-sm font-medium disabled:opacity-40 hover:bg-[#7c73ff] transition-colors"
          >
            ↑
          </button>
        </div>
        <p className="text-[#4b5563] text-xs mt-1">Enter to send · Shift+Enter for newline</p>
      </div>
    </div>
  )
}

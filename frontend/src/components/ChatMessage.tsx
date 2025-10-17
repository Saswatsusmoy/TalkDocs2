'use client'

import { useState } from 'react'
import MarkdownMessage from './MarkdownMessage'

interface ChatMessageProps {
  message: {
    id: string
    content: string
    role: 'user' | 'assistant'
    timestamp: Date
    sources?: Array<{
      title: string
      url: string
      similarity_score?: number
    }>
  }
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const [copied, setCopied] = useState(false)

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
        <div className={`message-bubble ${message.role === 'user' ? 'user-message' : 'assistant-message'} max-w-3xl`}>
          {message.role === 'assistant' && (
            <div className="flex items-center justify-between mb-2 text-xs text-gray-400">
              <div className="flex items-center gap-2">
                <span>AI Assistant</span>
                <span className="text-gray-500">
                  {message.timestamp.toLocaleTimeString()}
                </span>
              </div>
              <button
                onClick={copyToClipboard}
                className="px-2 py-1 text-xs text-gray-400 hover:text-white"
              >
                {copied ? 'Copied' : 'Copy'}
              </button>
            </div>
          )}
        
        {message.role === 'user' && (
          <div className="flex items-center gap-2 mb-2 text-xs text-blue-300">
            <span>You</span>
            <span className="text-gray-500">
              {message.timestamp.toLocaleTimeString()}
            </span>
          </div>
        )}

        {/* Message content with proper formatting */}
        {message.role === 'assistant' ? (
          <div className="space-y-3">
            <MarkdownMessage content={message.content} role={message.role} />
          </div>
        ) : (
          <div className="whitespace-pre-wrap leading-relaxed text-terminal-text">
            {message.content}
          </div>
        )}

        {/* Sources section for assistant messages */}
        {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
          <div className="mt-4 pt-3 border-t border-gray-700">
            <div className="text-xs text-gray-400 mb-2">Sources:</div>
            <div className="space-y-1">
              {message.sources.map((source, index) => (
                <div key={index} className="flex items-center gap-2 text-xs">
                  <span className="text-gray-500">•</span>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 transition-colors truncate"
                    title={source.title}
                  >
                    {source.title}
                  </a>
                  {source.similarity_score && (
                    <span className="text-gray-500">
                      ({(source.similarity_score * 100).toFixed(0)}%)
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

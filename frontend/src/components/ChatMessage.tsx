'use client'

import { useState } from 'react'
import { Copy, Check, Code, Terminal } from 'lucide-react'

interface ChatMessageProps {
  message: {
    id: string
    content: string
    role: 'user' | 'assistant'
    timestamp: Date
  }
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const [copied, setCopied] = useState(false)

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const formatCodeBlocks = (content: string) => {
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g
    const parts = []
    let lastIndex = 0
    let match

    while ((match = codeBlockRegex.exec(content)) !== null) {
      // Add text before code block
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: content.slice(lastIndex, match.index)
        })
      }

      // Add code block
      parts.push({
        type: 'code',
        language: match[1] || 'text',
        content: match[2]
      })

      lastIndex = match.index + match[0].length
    }

    // Add remaining text
    if (lastIndex < content.length) {
      parts.push({
        type: 'text',
        content: content.slice(lastIndex)
      })
    }

    return parts.length > 0 ? parts : [{ type: 'text', content }]
  }

  const messageParts = formatCodeBlocks(message.content)

  return (
    <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`message-bubble ${message.role === 'user' ? 'user-message' : 'assistant-message'} max-w-3xl`}>
        {message.role === 'assistant' && (
          <div className="flex items-center gap-2 mb-2 text-xs text-gray-400">
            <Terminal className="w-4 h-4" />
            <span>AI Assistant</span>
            <span className="text-gray-500">
              {message.timestamp.toLocaleTimeString()}
            </span>
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

        <div className="space-y-3">
          {messageParts.map((part, index) => (
            <div key={index}>
              {part.type === 'text' ? (
                <div className="whitespace-pre-wrap leading-relaxed">
                  {part.content}
                </div>
              ) : (
                <div className="relative">
                  <div className="flex items-center justify-between bg-gray-800 px-3 py-2 rounded-t-md border-b border-gray-700">
                    <div className="flex items-center gap-2">
                      <Code className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-300 font-mono">
                        {part.language}
                      </span>
                    </div>
                    <button
                      onClick={copyToClipboard}
                      className="flex items-center gap-1 px-2 py-1 text-xs text-gray-400 hover:text-white transition-colors"
                    >
                      {copied ? (
                        <>
                          <Check className="w-3 h-3" />
                          Copied
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          Copy
                        </>
                      )}
                    </button>
                  </div>
                  <pre className="code-block rounded-b-md">
                    <code className={`language-${part.language}`}>
                      {part.content}
                    </code>
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

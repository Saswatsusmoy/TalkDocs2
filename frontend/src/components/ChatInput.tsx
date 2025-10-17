'use client'

import { useState, useRef, KeyboardEvent } from 'react'
import { Send, Loader2, Download, Trash2 } from 'lucide-react'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  isLoading: boolean
  onExportChat: () => void
  onClearChat: () => void
}

export default function ChatInput({ onSendMessage, isLoading, onExportChat, onClearChat }: ChatInputProps) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = () => {
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim())
      setMessage('')
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value)
    
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }

  return (
    <div className="sticky bottom-0 bg-terminal-bg border-t border-terminal-border p-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-end gap-3">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything... (Press Enter to send, Shift+Enter for new line)"
              className="chat-input w-full px-4 py-3 pr-12 resize-none min-h-[52px] max-h-[120px]"
              disabled={isLoading}
              rows={1}
            />
            <div className="absolute right-3 top-3 text-xs text-gray-500">
              {message.length > 0 && `${message.length} chars`}
            </div>
          </div>
          
          <button
            onClick={handleSubmit}
            disabled={!message.trim() || isLoading}
            className="btn-primary px-4 py-3 rounded-lg flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>
        
        {/* Action buttons */}
        <div className="flex items-center justify-center gap-3 mt-3">
          <button
            onClick={onExportChat}
            className="flex items-center gap-2 px-3 py-2 text-sm text-button-text hover:text-white transition-colors border border-terminal-border rounded-lg hover:border-button-hover"
          >
            <Download className="w-4 h-4" />
            <span className="hidden sm:inline">Export Chat</span>
          </button>
          <button
            onClick={onClearChat}
            className="flex items-center gap-2 px-3 py-2 text-sm text-button-text hover:text-red-400 transition-colors border border-terminal-border rounded-lg hover:border-red-500"
          >
            <Trash2 className="w-4 h-4" />
            <span className="hidden sm:inline">Clear Chat</span>
          </button>
        </div>
      </div>
    </div>
  )
}

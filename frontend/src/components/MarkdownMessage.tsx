'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useState } from 'react'

interface MarkdownMessageProps {
  content: string
  role: 'user' | 'assistant'
}

export default function MarkdownMessage({ content, role }: MarkdownMessageProps) {
  const [copiedCode, setCopiedCode] = useState<string | null>(null)

  const copyToClipboard = async (code: string, language: string) => {
    await navigator.clipboard.writeText(code)
    setCopiedCode(`${language}-${code.slice(0, 20)}`)
    setTimeout(() => setCopiedCode(null), 2000)
  }

  const components = {
    code({ node, inline, className, children, ...props }: any) {
      const match = /language-(\w+)/.exec(className || '')
      const language = match ? match[1] : ''
      const code = String(children).replace(/\n$/, '')

      if (!inline && language) {
        const copyKey = `${language}-${code.slice(0, 20)}`
        const isCopied = copiedCode === copyKey

        return (
          <div className="relative my-4">
            <div className="flex items-center justify-between bg-gray-800 px-3 py-2 rounded-t-md border-b border-gray-700">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-300 font-mono">
                  {language}
                </span>
              </div>
              <button
                onClick={() => copyToClipboard(code, language)}
                className="px-2 py-1 text-xs text-gray-400 hover:text-white"
              >
                {isCopied ? 'Copied' : 'Copy'}
              </button>
            </div>
            <SyntaxHighlighter
              style={oneDark}
              language={language}
              PreTag="div"
              className="rounded-b-md !mt-0"
              {...props}
            >
              {code}
            </SyntaxHighlighter>
          </div>
        )
      }

      return (
        <code
          className="bg-gray-800 px-1.5 py-0.5 rounded text-sm font-mono text-terminal-green border border-gray-700"
          {...props}
        >
          {children}
        </code>
      )
    },
    h1: ({ children }: any) => (
      <h1 className="text-2xl font-bold text-terminal-text mt-6 mb-4 pb-2 border-b border-terminal-border">
        {children}
      </h1>
    ),
    h2: ({ children }: any) => (
      <h2 className="text-xl font-bold text-terminal-text mt-5 mb-3 pb-1 border-b border-gray-700">
        {children}
      </h2>
    ),
    h3: ({ children }: any) => (
      <h3 className="text-lg font-semibold text-terminal-text mt-4 mb-2">
        {children}
      </h3>
    ),
    h4: ({ children }: any) => (
      <h4 className="text-base font-semibold text-terminal-text mt-3 mb-2">
        {children}
      </h4>
    ),
    p: ({ children }: any) => (
      <p className="mb-3 leading-relaxed text-terminal-text">
        {children}
      </p>
    ),
    ul: ({ children }: any) => (
      <ul className="mb-3 ml-4 space-y-1">
        {children}
      </ul>
    ),
    ol: ({ children }: any) => (
      <ol className="mb-3 ml-4 space-y-1 list-decimal">
        {children}
      </ol>
    ),
    li: ({ children }: any) => (
      <li className="text-terminal-text">
        {children}
      </li>
    ),
    blockquote: ({ children }: any) => (
      <blockquote className="border-l-4 border-terminal-green pl-4 py-2 my-4 bg-gray-800/50 rounded-r">
        <div className="text-gray-300 italic">
          {children}
        </div>
      </blockquote>
    ),
    table: ({ children }: any) => (
      <div className="overflow-x-auto my-4">
        <table className="min-w-full border border-gray-700 rounded-lg overflow-hidden">
          {children}
        </table>
      </div>
    ),
    thead: ({ children }: any) => (
      <thead className="bg-gray-800">
        {children}
      </thead>
    ),
    tbody: ({ children }: any) => (
      <tbody className="bg-gray-900">
        {children}
      </tbody>
    ),
    tr: ({ children }: any) => (
      <tr className="border-b border-gray-700">
        {children}
      </tr>
    ),
    th: ({ children }: any) => (
      <th className="px-4 py-2 text-left text-sm font-semibold text-terminal-text border-r border-gray-700 last:border-r-0">
        {children}
      </th>
    ),
    td: ({ children }: any) => (
      <td className="px-4 py-2 text-sm text-terminal-text border-r border-gray-700 last:border-r-0">
        {children}
      </td>
    ),
    a: ({ href, children }: any) => (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-400 hover:text-blue-300 underline transition-colors"
      >
        {children}
      </a>
    ),
    strong: ({ children }: any) => (
      <strong className="font-semibold text-terminal-green">
        {children}
      </strong>
    ),
    em: ({ children }: any) => (
      <em className="italic text-gray-300">
        {children}
      </em>
    ),
    hr: () => (
      <hr className="my-6 border-terminal-border" />
    ),
  }

  return (
    <div className="prose prose-invert max-w-none">
      <ReactMarkdown
        components={components}
        remarkPlugins={[remarkGfm]}
        className="text-terminal-text"
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

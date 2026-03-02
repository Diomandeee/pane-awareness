'use client'

import { useState } from 'react'

interface CodeBlockProps {
  code: string
  language?: string
}

export default function CodeBlock({ code, language }: CodeBlockProps) {
  const [copied, setCopied] = useState(false)

  const copy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative group">
      {language && (
        <div className="absolute top-0 left-0 px-3 py-1 text-xs text-gray-500 font-mono">
          {language}
        </div>
      )}
      <button
        onClick={copy}
        className="absolute top-2 right-2 px-2 py-1 text-xs rounded bg-surface-200 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity hover:text-gray-200"
      >
        {copied ? 'Copied!' : 'Copy'}
      </button>
      <pre className="bg-surface-50 border border-surface-300 rounded-lg p-4 overflow-x-auto">
        <code className="text-sm font-mono text-gray-300">{code}</code>
      </pre>
    </div>
  )
}

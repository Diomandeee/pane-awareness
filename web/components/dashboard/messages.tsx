import type { PaneMessage } from '@/lib/types'
import { timeAgo } from './utils'

interface MessagesProps {
  messages: PaneMessage[]
}

export default function Messages({ messages }: MessagesProps) {
  return (
    <div className="border border-surface-300 rounded-lg overflow-hidden">
      <div className="px-4 py-2 border-b border-surface-300">
        <h3 className="text-sm font-semibold">Message Log</h3>
      </div>
      <div className="p-4 max-h-[300px] overflow-y-auto">
        {messages.length > 0 ? (
          messages.map((m, i) => (
            <div
              key={m.id || i}
              className="py-1.5 border-b border-surface-200 last:border-0"
            >
              <div className="flex items-center gap-2 mb-0.5 text-[11px]">
                <span className="text-blue-400 font-mono">
                  {m.from?.split('/').pop() || '??'}
                </span>
                <span className="text-gray-500">&rarr;</span>
                <span className="text-green-400 font-mono">
                  {m.target === 'all'
                    ? 'ALL'
                    : m.target?.split('/').pop() || m.target}
                </span>
                {m.priority === 'urgent' && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-900/50 text-red-400">
                    urgent
                  </span>
                )}
                {m.msg_type && m.msg_type !== 'info' && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-200 text-gray-400">
                    {m.msg_type}
                  </span>
                )}
                <span className="text-[11px] text-gray-500 ml-auto">
                  {timeAgo(m.timestamp)}
                </span>
              </div>
              <p className="text-xs truncate">{m.message}</p>
            </div>
          ))
        ) : (
          <p className="text-sm text-gray-500">No messages</p>
        )}
      </div>
    </div>
  )
}

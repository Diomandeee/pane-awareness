import type { ThreadNote } from '@/lib/types'
import { timeAgo } from './utils'

interface ThreadsProps {
  threads: ThreadNote[]
}

export default function Threads({ threads }: ThreadsProps) {
  return (
    <div className="border border-surface-300 rounded-lg overflow-hidden">
      <div className="px-4 py-2 border-b border-surface-300">
        <h3 className="text-sm font-semibold">Handoff Threads</h3>
      </div>
      <div className="p-4">
        {threads.length > 0 ? (
          threads.map((t) => (
            <div
              key={t.filename}
              className="py-2 border-b border-surface-200 last:border-0"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs text-blue-400">{t.from_pane}</span>
                <span className="text-gray-500">&rarr;</span>
                <span className="text-xs text-green-400">{t.to_pane}</span>
                <span className="text-[11px] text-gray-500 ml-auto">
                  {timeAgo(t.modified)}
                </span>
              </div>
              <p className="text-xs truncate">{t.task}</p>
            </div>
          ))
        ) : (
          <p className="text-sm text-gray-500">No handoff threads</p>
        )}
      </div>
    </div>
  )
}

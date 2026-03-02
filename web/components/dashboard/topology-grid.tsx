import type { LivePane } from '@/lib/types'

interface TopologyGridProps {
  panes: LivePane[]
}

const quadrants = ['top-left', 'top-right', 'bottom-left', 'bottom-right']

export default function TopologyGrid({ panes }: TopologyGridProps) {
  return (
    <div className="border border-surface-300 rounded-lg overflow-hidden">
      <div className="px-4 py-2 border-b border-surface-300">
        <h3 className="text-sm font-semibold">Active Topology</h3>
      </div>
      <div className="p-4">
        {panes.length > 0 ? (
          <div className="grid grid-cols-2 gap-3">
            {quadrants.map((q) => {
              const panesInQ = panes.filter((p) => p.quadrant === q)
              return (
                <div
                  key={q}
                  className="border border-surface-300 rounded-lg p-3 min-h-[80px]"
                >
                  <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">
                    {q}
                  </p>
                  {panesInQ.length === 0 ? (
                    <p className="text-xs text-gray-600 italic">empty</p>
                  ) : (
                    panesInQ.map((p, i) => (
                      <div key={i} className="mt-1">
                        <p className="text-sm font-semibold">{p.project}</p>
                        <p className="text-[11px] text-gray-500 truncate">
                          {p.last_prompt || 'idle'}
                        </p>
                        {p.key_topics.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {p.key_topics.slice(0, 4).map((t) => (
                              <span
                                key={t}
                                className="text-[9px] px-1.5 py-0.5 rounded bg-surface-200 text-gray-400"
                              >
                                {t}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )
            })}
          </div>
        ) : (
          <p className="text-sm text-gray-500">No active panes</p>
        )}
      </div>
    </div>
  )
}

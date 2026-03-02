import type { ClaimNote } from '@/lib/types'
import { timeAgo } from './utils'

interface ClaimsProps {
  claims: ClaimNote[]
}

export default function Claims({ claims }: ClaimsProps) {
  return (
    <div className="border border-surface-300 rounded-lg overflow-hidden">
      <div className="px-4 py-2 border-b border-surface-300">
        <h3 className="text-sm font-semibold">Resource Claims</h3>
      </div>
      <div className="p-4">
        {claims.length > 0 ? (
          claims.map((c) => (
            <div
              key={c.filename}
              className="py-2 border-b border-surface-200 last:border-0"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-200 text-gray-400">
                  {c.event || '?'}
                </span>
                <span className="text-[11px] text-gray-500">
                  {timeAgo(c.modified)}
                </span>
              </div>
              <p className="text-xs font-mono">{c.resource}</p>
              <p className="text-[11px] text-gray-500 mt-0.5">
                Holder: {c.holder} &middot; {c.scope}
              </p>
            </div>
          ))
        ) : (
          <p className="text-sm text-gray-500">No claims</p>
        )}
      </div>
    </div>
  )
}

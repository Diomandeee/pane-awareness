import type { PredictionNote } from '@/lib/types'
import { timeAgo } from './utils'

interface PredictionsProps {
  predictions: PredictionNote[]
}

export default function Predictions({ predictions }: PredictionsProps) {
  return (
    <div className="border border-surface-300 rounded-lg overflow-hidden">
      <div className="px-4 py-2 border-b border-surface-300">
        <h3 className="text-sm font-semibold">Convergence Predictions</h3>
      </div>
      <div className="p-4">
        {predictions.length > 0 ? (
          predictions.map((p) => (
            <div
              key={p.filename}
              className="py-2 border-b border-surface-200 last:border-0"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="flex gap-1">
                  <Badge label={p.prediction_type || '?'} />
                  <Badge label={p.status || '?'} />
                </span>
                <span className="text-[11px] text-gray-500">
                  {timeAgo(p.modified)}
                </span>
              </div>
              <p className="text-xs">
                {p.pane_a} &harr; {p.pane_b}
              </p>
              <p className="text-[11px] text-gray-500 mt-0.5">
                Confidence: {p.confidence} &middot; {p.urgency || 'NORMAL'}
              </p>
            </div>
          ))
        ) : (
          <p className="text-sm text-gray-500">No predictions</p>
        )}
      </div>
    </div>
  )
}

function Badge({ label }: { label: string }) {
  return (
    <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-200 text-gray-400">
      {label}
    </span>
  )
}

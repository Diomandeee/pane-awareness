import type { PredictionStats } from '@/lib/types'

interface AccuracyProps {
  stats: PredictionStats
}

export default function Accuracy({ stats }: AccuracyProps) {
  if (stats.resolved <= 0) return null

  return (
    <div className="border border-surface-300 rounded-lg overflow-hidden">
      <div className="px-4 py-2 border-b border-surface-300">
        <h3 className="text-sm font-semibold">Prediction Accuracy</h3>
      </div>
      <div className="p-4">
        <div className="grid grid-cols-5 gap-4 text-center mb-4">
          <div>
            <p className="text-2xl font-bold">{stats.total}</p>
            <p className="text-[11px] text-gray-500">Total</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-green-400">{stats.prevented}</p>
            <p className="text-[11px] text-gray-500">Prevented</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-yellow-400">{stats.occurred}</p>
            <p className="text-[11px] text-gray-500">Occurred</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-red-400">{stats.false_positive}</p>
            <p className="text-[11px] text-gray-500">False Positive</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-500">{stats.expired}</p>
            <p className="text-[11px] text-gray-500">Expired</p>
          </div>
        </div>
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-400">Prevention Rate</span>
            <span className="text-xs font-bold">{stats.prevention_rate}%</span>
          </div>
          <div className="bg-surface-300 rounded-full h-2">
            <div
              className="bg-green-400 rounded-full h-2 transition-all duration-300"
              style={{ width: `${Math.min(stats.prevention_rate, 100)}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

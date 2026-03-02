export default function DemoBanner() {
  return (
    <div className="rounded-lg border border-yellow-800/50 bg-yellow-900/20 px-4 py-3 mb-6">
      <p className="text-sm text-yellow-400">
        <strong>Demo Mode</strong> — Viewing sample data. Set{' '}
        <code className="bg-surface-200 px-1 py-0.5 rounded text-xs">
          NEXT_PUBLIC_PANE_API_URL
        </code>{' '}
        and run the Dashboard API to see live data.
      </p>
    </div>
  )
}

import Link from 'next/link'

export default function Hero() {
  return (
    <section className="py-24 px-4">
      <div className="max-w-4xl mx-auto text-center">
        <div className="inline-block mb-6 px-3 py-1 rounded-full border border-surface-300 text-xs text-gray-400">
          Zero dependencies &middot; Pure Python &middot; File-based coordination
        </div>

        <h1 className="text-5xl sm:text-6xl font-bold tracking-tight mb-6">
          <span className="text-brand-400">Cross-session</span> coordination
          <br />
          for AI coding assistants
        </h1>

        <p className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          When you run 2&ndash;4 concurrent AI sessions in a tiled terminal, each operates in isolation.{' '}
          <strong className="text-gray-200">pane-awareness</strong> fixes this by giving each session
          visibility into the others&apos; work.
        </p>

        <div className="flex items-center justify-center gap-4">
          <Link
            href="/docs/configuration"
            className="px-6 py-3 rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-medium transition-colors"
          >
            Get Started
          </Link>
          <a
            href="https://github.com/Diomandeee/pane-awareness"
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 rounded-lg border border-surface-300 hover:border-gray-500 text-gray-300 font-medium transition-colors"
          >
            View on GitHub
          </a>
        </div>
      </div>
    </section>
  )
}

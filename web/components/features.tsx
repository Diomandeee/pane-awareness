const features = [
  {
    title: 'Topic Tracking',
    description:
      'Each prompt is analyzed for keywords. Over the last 10 prompts, topics are classified as deepening, emerging, fading, or stable.',
    icon: '&#9670;',
  },
  {
    title: 'Convergence Prediction',
    description:
      'Four signal types detect when panes are heading toward the same work — mutual deepening, approaching, cross-approach, and domain proximity.',
    icon: '&#9651;',
  },
  {
    title: 'Resource Claims',
    description:
      'Cooperative advisory locking prevents duplicate work on files and APIs. Claims auto-expire when the holding pane goes stale.',
    icon: '&#9632;',
  },
  {
    title: 'Cross-Pane Messaging',
    description:
      '8 message types — info, question, delegate, handoff, claim, release, ack, and block — for structured inter-session communication.',
    icon: '&#9993;',
  },
  {
    title: 'Handoff Context',
    description:
      'Rich tiered context blobs for delegating tasks between panes — project state, recent prompts, git diff, active claims, and custom fields.',
    icon: '&#8644;',
  },
  {
    title: 'Delegation Suggestions',
    description:
      'Automatic recommendations for who should do what, based on trajectory drift and domain expertise across all active panes.',
    icon: '&#9881;',
  },
]

export default function Features() {
  return (
    <section className="py-16 px-4">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-12">Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f) => (
            <div
              key={f.title}
              className="p-6 rounded-lg border border-surface-300 bg-surface-50 hover:border-brand-800 transition-colors"
            >
              <div
                className="text-2xl mb-3 text-brand-400"
                dangerouslySetInnerHTML={{ __html: f.icon }}
              />
              <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
              <p className="text-sm text-gray-400 leading-relaxed">{f.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

import DocsSidebar from '@/components/docs-sidebar'

export default function DocsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="max-w-6xl mx-auto px-4 py-8 flex gap-8">
      <DocsSidebar />
      <article className="flex-1 min-w-0">{children}</article>
    </div>
  )
}

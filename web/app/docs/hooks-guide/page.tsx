import MarkdownRenderer from '@/components/markdown-renderer'
import { docsContent } from '@/lib/docs-content'

export default function HooksGuidePage() {
  return <MarkdownRenderer content={docsContent['hooks-guide']} />
}

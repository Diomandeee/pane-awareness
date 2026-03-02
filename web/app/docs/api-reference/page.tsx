import MarkdownRenderer from '@/components/markdown-renderer'
import { docsContent } from '@/lib/docs-content'

export default function ApiReferencePage() {
  return <MarkdownRenderer content={docsContent['api-reference']} />
}

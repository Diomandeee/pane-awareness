import MarkdownRenderer from '@/components/markdown-renderer'
import { docsContent } from '@/lib/docs-content'

export default function ConfigurationPage() {
  return <MarkdownRenderer content={docsContent.configuration} />
}

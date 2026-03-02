import MarkdownRenderer from '@/components/markdown-renderer'
import { docsContent } from '@/lib/docs-content'

export default function McpToolsPage() {
  return <MarkdownRenderer content={docsContent['mcp-tools']} />
}

import MarkdownRenderer from '@/components/markdown-renderer'
import { docsContent } from '@/lib/docs-content'

export default function VaultIntegrationPage() {
  return <MarkdownRenderer content={docsContent['vault-integration']} />
}

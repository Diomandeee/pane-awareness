'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const docs = [
  { href: '/docs/configuration', label: 'Configuration' },
  { href: '/docs/api-reference', label: 'API Reference' },
  { href: '/docs/mcp-tools', label: 'MCP Tools' },
  { href: '/docs/hooks-guide', label: 'Hooks Guide' },
  { href: '/docs/vault-integration', label: 'Vault Integration' },
]

export default function DocsSidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-56 shrink-0 hidden md:block">
      <nav className="sticky top-20 space-y-1">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-3">
          Documentation
        </p>
        {docs.map(({ href, label }) => {
          const active = pathname === href
          return (
            <Link
              key={href}
              href={href}
              className={`block px-3 py-2 rounded-md text-sm transition-colors ${
                active
                  ? 'bg-surface-100 text-brand-400 font-medium'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-surface-100'
              }`}
            >
              {label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}

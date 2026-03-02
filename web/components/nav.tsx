'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const links = [
  { href: '/', label: 'Home' },
  { href: '/docs/configuration', label: 'Docs' },
  { href: '/dashboard', label: 'Dashboard' },
]

export default function Nav() {
  const pathname = usePathname()

  return (
    <nav className="sticky top-0 z-50 border-b border-surface-300 bg-surface/80 backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-bold text-lg">
          <span className="text-brand-400">&#9638;</span>
          <span>pane-awareness</span>
        </Link>

        <div className="flex items-center gap-6">
          {links.map(({ href, label }) => {
            const active =
              href === '/'
                ? pathname === '/'
                : pathname.startsWith(href)
            return (
              <Link
                key={href}
                href={href}
                className={`text-sm transition-colors ${
                  active
                    ? 'text-brand-400 font-medium'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                {label}
              </Link>
            )
          })}
          <a
            href="https://github.com/Diomandeee/pane-awareness"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-gray-400 hover:text-gray-200 transition-colors"
          >
            GitHub
          </a>
        </div>
      </div>
    </nav>
  )
}

import type { Metadata } from 'next'
import './globals.css'
import Nav from '@/components/nav'

export const metadata: Metadata = {
  title: 'pane-awareness — Cross-Session Coordination for AI Coding',
  description:
    'Coordinate parallel AI coding sessions with topic tracking, convergence prediction, resource claims, and cross-pane messaging.',
  openGraph: {
    title: 'pane-awareness',
    description: 'Cross-session coordination for AI coding assistants running in parallel terminal panes.',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-surface text-gray-100 antialiased min-h-screen">
        <Nav />
        <main>{children}</main>
      </body>
    </html>
  )
}

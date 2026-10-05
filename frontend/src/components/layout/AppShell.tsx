/**
 * Page shell.
 *
 * Supplies the landmarks, the skip link and the vertical rhythm that every page
 * shares, so individual pages never re-implement page-level structure. The main
 * landmark is focusable via the skip link, which is the only reliable way to
 * move a keyboard user's cursor past a sticky header.
 */

import { useEffect, type ReactNode } from 'react'
import { useLocation } from 'react-router-dom'
import { SiteHeader } from './SiteHeader'
import { SiteFooter } from './SiteFooter'
import { copy } from '@/lib/copy'
import { cn } from '@/lib/cn'

interface AppShellProps {
  children: ReactNode
  /** Controls the header action slot. */
  actions?: ReactNode
  /** Removes the vertical padding above the content, for full-bleed pages. */
  bare?: boolean
}

export function AppShell({ children, actions, bare = false }: AppShellProps) {
  const location = useLocation()

  // A single h1 per page means focus must move to the new page heading on
  // navigation, otherwise focus stays on a link inside the old page body. Each
  // page marks its h1 with tabIndex={-1} so it can receive focus without
  // appearing in the tab order.
  useEffect(() => {
    document.querySelector<HTMLElement>('main h1')?.focus()
  }, [location.pathname])

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <a href="#main-content" className="skip-link">
        {copy.app.skipToContent}
      </a>

      <SiteHeader actions={actions} />

      <main
        id="main-content"
        tabIndex={-1}
        className={cn(
          'mx-auto w-full max-w-content flex-1',
          !bare && 'px-4 py-8 sm:px-6 sm:py-10',
        )}
      >
        {children}
      </main>

      <SiteFooter />
    </div>
  )
}
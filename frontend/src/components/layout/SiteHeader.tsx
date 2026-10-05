/**
 * Persistent site header.
 *
 * A single sticky bar rather than a full navigation tree: the product has three
 * routes and two of them are steps within one task. Sticky is deliberate, so
 * the case reference and the export control stay reachable while scrolling a
 * long trace, but the bar is thin enough not to compete with the content.
 */

import { Link, useLocation } from 'react-router-dom'
import { FileDown, Plus } from 'lucide-react'
import { Wordmark } from './Wordmark'
import { usingMockData } from '@/lib/api'
import { copy } from '@/lib/copy'
import { cn } from '@/lib/cn'

interface SiteHeaderProps {
  /** Rendered on the right, before the navigation. Used for the export pair. */
  actions?: React.ReactNode
}

export function SiteHeader({ actions }: SiteHeaderProps) {
  const location = useLocation()
  const onResult = location.pathname.startsWith('/cases/')

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-header">
      <div className="mx-auto flex w-full max-w-content items-center gap-4 px-4 py-3 sm:px-6">
        <Wordmark className="min-w-0 flex-1" />

        <nav aria-label="Primary" className="flex shrink-0 items-center gap-1">
          {actions}
          <Link
            to="/"
            className={cn(
              'btn btn-quiet hidden sm:inline-flex',
              onResult && 'border border-border-subtle',
            )}
            aria-current={onResult ? 'page' : undefined}
          >
            <Plus size={16} strokeWidth={1.5} aria-hidden="true" />
            {copy.nav.home}
          </Link>
          <Link to="/" className="btn btn-quiet px-2 sm:hidden" aria-label={copy.nav.home}>
            <Plus size={18} strokeWidth={1.5} aria-hidden="true" />
          </Link>
        </nav>
      </div>

      {usingMockData ? (
        <div className="border-t border-border-subtle bg-status-attention-bg">
          <div className="mx-auto flex w-full max-w-content items-center gap-2 px-4 py-1.5 sm:px-6">
            <FileDown size={14} strokeWidth={1.5} aria-hidden="true" className="shrink-0 text-status-attention-fg" />
            <p className="text-xs text-status-attention-fg">{copy.home.demo.dataNotice}</p>
          </div>
        </div>
      ) : null}
    </header>
  )
}
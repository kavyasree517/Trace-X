/**
 * Product wordmark.
 *
 * Drawn in text rather than as an image or glyph: no logotype asset exists, and
 * a wordmark built from type stays legible at any size, respects the font
 * fallback, and is announced correctly by assistive technology.
 */

import { Link } from 'react-router-dom'
import { cn } from '@/lib/cn'
import { copy } from '@/lib/copy'

interface WordmarkProps {
  className?: string
  /** Renders as a link to the home route. */
  asLink?: boolean
}

export function Wordmark({ className, asLink = true }: WordmarkProps) {
  const content = (
    <span className="inline-flex items-baseline gap-2">
      <span className="text-lg font-semibold tracking-tight text-primary">
        {copy.app.name}
      </span>
      <span
        aria-hidden="true"
        className="hidden h-4 w-px bg-border-strong sm:block"
      />
      <span className="hidden text-xs leading-tight text-muted sm:block">
        Trust-aware risk analysis and connection evidence
      </span>
    </span>
  )

  if (!asLink) {
    return <span className={cn('inline-flex', className)}>{content}</span>
  }

  return (
    <Link
      to="/"
      className={cn(
        'inline-flex rounded-sm transition-opacity duration-fast hover:opacity-80',
        className,
      )}
      aria-label={copy.nav.homeLabel}
    >
      {content}
    </Link>
  )
}
/**
 * Link that opens an external block explorer in a new tab.
 *
 * `rel="noopener noreferrer"` is not optional: without it the opened page gains
 * access to this window through `window.opener` and learns the referrer. The
 * icon is decorative and the accessible name states where the link goes, which
 * is what a screen reader user needs in place of the visual cue.
 */

import { ExternalLink as ExternalLinkIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { cn } from '@/lib/cn'
import { copy } from '@/lib/copy'

interface ExternalLinkProps {
  href: string
  children: ReactNode
  /** Overrides the accessible name. Include the destination for clarity. */
  accessibleName?: string
  showIcon?: boolean
  className?: string
}

export function ExternalLink({
  href,
  children,
  accessibleName,
  showIcon = true,
  className,
}: ExternalLinkProps) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        'inline-flex items-center gap-1 rounded-sm text-accent',
        'underline decoration-accent-border underline-offset-2',
        'transition-colors duration-fast hover:text-accent-hover hover:decoration-accent',
        className,
      )}
      aria-label={accessibleName}
    >
      {children}
      {showIcon ? (
        <>
          <ExternalLinkIcon size={14} strokeWidth={1.5} aria-hidden="true" />
          <span className="sr-only">{copy.common.externalLink}</span>
        </>
      ) : null}
    </a>
  )
}
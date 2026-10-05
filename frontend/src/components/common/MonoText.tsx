/**
 * Monospace value display for addresses and transaction hashes.
 *
 * Long identifiers are abbreviated by default because an untruncated 66 character
 * hash destroys any layout it sits in. The full value is always one interaction
 * away, is exposed to assistive technology in full via the title, and is
 * printed verbatim in every table, so a truncated value is never the only way to
 * read it.
 */

import { useId, useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { CopyButton } from './CopyButton'
import { formatAddress, formatHash } from '@/lib/format'
import { copy } from '@/lib/copy'
import { cn } from '@/lib/cn'

interface MonoTextProps {
  value: string
  /** Shortens to first 6 and last 4. Use `hash` for first 10 and last 6. */
  variant?: 'address' | 'hash'
  /** Removes the expand control. Use where the full value is already visible. */
  alwaysFull?: boolean
  showCopy?: boolean
  /** Accessible name for the copy control, for example "wallet address". */
  copyLabel?: string
  className?: string
}

export function MonoText({
  value,
  variant = 'address',
  alwaysFull = false,
  showCopy = true,
  copyLabel,
  className,
}: MonoTextProps) {
  const [expanded, setExpanded] = useState(false)
  const regionId = useId()

  const abbreviated = variant === 'hash' ? formatHash(value) : formatAddress(value)
  const display = alwaysFull || expanded ? value : abbreviated
  const isTruncated = display !== value

  const toggleLabel = expanded ? copy.common.collapse : copy.common.expand

  return (
    <span className={cn('inline-flex max-w-full items-center gap-1', className)}>
      <code
        id={regionId}
        className={cn(
          'min-w-0 truncate rounded-sm text-sm text-primary',
          !alwaysFull && 'cursor-pointer',
        )}
        title={value}
      >
        {display}
      </code>

      {isTruncated ? (
        <button
          type="button"
          onClick={() => setExpanded((current) => !current)}
          className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-sm text-muted transition-colors duration-fast hover:bg-surface-subtle hover:text-accent"
          aria-expanded={expanded}
          aria-controls={regionId}
          aria-label={`${toggleLabel}: ${value}`}
        >
          {expanded ? (
            <ChevronDown size={14} strokeWidth={1.5} aria-hidden="true" />
          ) : (
            <ChevronRight size={14} strokeWidth={1.5} aria-hidden="true" />
          )}
        </button>
      ) : null}

      {showCopy ? <CopyButton value={value} label={copyLabel ?? display} /> : null}
    </span>
  )
}
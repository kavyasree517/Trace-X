/**
 * Progressive disclosure panel built on native details and summary.
 *
 * Native disclosure is used deliberately: it gives keyboard operation, the
 * expanded state and the correct semantics with no JavaScript and no focus
 * management to get wrong. Styling removes the default marker and supplies one.
 *
 * The component is uncontrolled unless `open` and `onOpenChange` are both
 * supplied, in which case the parent owns the state. That is what lets a list of
 * panels guarantee a single open section while still working standalone.
 */

import { useId, type ReactNode } from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/cn'

interface ExpandablePanelProps {
  title: string
  /** Rendered beside the title. Keep it to one short line. */
  description?: string
  children: ReactNode
  defaultOpen?: boolean
  /** Controlled expanded state. Requires `onOpenChange`. */
  open?: boolean
  onOpenChange?: (open: boolean) => void
  className?: string
}

export function ExpandablePanel({
  title,
  description,
  children,
  defaultOpen = false,
  open,
  onOpenChange,
  className,
}: ExpandablePanelProps) {
  const panelId = useId()
  const isControlled = open !== undefined && onOpenChange !== undefined

  const handleToggle = (event: React.SyntheticEvent<HTMLDetailsElement>) => {
    if (!isControlled) return
    const next = event.currentTarget.open
    if (next !== open) onOpenChange(next)
  }

  return (
    <details
      id={panelId}
      className={cn(
        'group overflow-hidden rounded-md border border-border bg-surface',
        className,
      )}
      open={isControlled ? open : defaultOpen}
      onToggle={isControlled ? handleToggle : undefined}
    >
      <summary
        className={cn(
          'flex cursor-pointer list-none items-center gap-2 px-4 py-3',
          'text-sm font-medium text-primary',
          'transition-colors duration-fast hover:bg-surface-subtle',
          '[&::-webkit-details-marker]:hidden',
        )}
      >
        <ChevronDown
          size={16}
          strokeWidth={1.5}
          aria-hidden="true"
          className="shrink-0 text-muted transition-transform duration-base group-open:rotate-180"
        />
        <span className="shrink-0">{title}</span>
        {description ? (
          <span className="min-w-0 truncate text-sm font-normal text-muted">
            {description}
          </span>
        ) : null}
      </summary>
      <div className="border-t border-border-subtle px-4 py-4">{children}</div>
    </details>
  )
}
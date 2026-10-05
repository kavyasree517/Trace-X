/**
 * Empty state.
 *
 * An empty result is a legitimate finding, not a failure, so this never uses
 * error styling or alarm wording. P3 requires the approved abstention phrasing
 * to appear verbatim in the empty case, which is why the text comes from the
 * copy deck rather than being written inline.
 */

import type { ReactNode } from 'react'
import { Inbox } from 'lucide-react'
import { copy } from '@/lib/copy'
import { cn } from '@/lib/cn'

interface EmptyStateProps {
  title?: string
  detail?: string
  children?: ReactNode
  className?: string
}

export function EmptyState({
  title = copy.feedback.empty.title,
  detail,
  children,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'rounded-md border border-dashed border-border bg-surface-subtle px-5 py-8 text-center',
        className,
      )}
    >
      <Inbox size={20} strokeWidth={1.5} aria-hidden="true" className="mx-auto mb-3 text-muted" />
      <p className="text-sm font-medium text-primary">{title}</p>
      {detail ? (
        <p className="mx-auto mt-1.5 max-w-prose text-sm leading-relaxed text-secondary">
          {detail}
        </p>
      ) : null}
      {children ? <div className="mt-4 flex justify-center">{children}</div> : null}
    </div>
  )
}
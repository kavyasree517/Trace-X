/**
 * Bordered content panel.
 *
 * One panel component so spacing, heading rhythm and border treatment stay
 * identical across every section of a result. The optional numeric index is
 * what lets a reader cite a section in correspondence ("section 7") and gives
 * the page a document-like spine, which is the register this product needs.
 */

import type { ReactNode } from 'react'
import { cn } from '@/lib/cn'

interface PanelProps {
  children: ReactNode
  /** Section number shown before the title, for reference in correspondence. */
  index?: number
  title: string
  /** One or two sentences of framing. Kept above the content, never inside it. */
  lead?: string
  /** Controls or badges shown on the heading row. */
  actions?: ReactNode
  className?: string
  bodyClassName?: string
  /** Accessible name when the visible title is not sufficient on its own. */
  headingId?: string
}

export function Panel({
  children,
  index,
  title,
  lead,
  actions,
  className,
  bodyClassName,
  headingId,
}: PanelProps) {
  return (
    <section className={cn('panel animate-fade-in scroll-mt-20', className)} aria-labelledby={headingId}>
      <div className="panel-heading">
        <div className="min-w-0">
          <h2 id={headingId} className="panel-title flex items-baseline gap-2">
            {typeof index === 'number' ? (
              <span className="panel-index" aria-hidden="true">
                {String(index).padStart(2, '0')}
              </span>
            ) : null}
            <span>{title}</span>
          </h2>
        </div>
        {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
      </div>

      <div className={cn('panel-body', bodyClassName)}>
        {lead ? <p className="mb-5 max-w-prose text-sm text-secondary">{lead}</p> : null}
        {children}
      </div>
    </section>
  )
}
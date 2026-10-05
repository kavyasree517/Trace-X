/**
 * Partial data notice and loading skeletons.
 *
 * Partial results are shown with the findings that exist plus an explicit
 * statement of what is missing. Presenting incomplete data as though it were
 * complete would be the worst failure this interface could make, so the notice
 * sits above the content rather than below it.
 */

import { AlertTriangle } from 'lucide-react'
import { copy } from '@/lib/copy'
import { cn } from '@/lib/cn'

interface PartialDataNoticeProps {
  detail?: string
  className?: string
}

export function PartialDataNotice({ detail, className }: PartialDataNoticeProps) {
  return (
    <div
      role="status"
      className={cn(
        'mb-5 flex items-start gap-2.5 rounded-md border border-status-attention-border',
        'bg-status-attention-bg px-3.5 py-3',
        className,
      )}
    >
      <AlertTriangle
        size={16}
        strokeWidth={1.5}
        aria-hidden="true"
        className="mt-0.5 shrink-0 text-status-attention-fg"
      />
      <div className="min-w-0">
        <p className="text-sm font-medium text-status-attention-fg">
          {copy.feedback.partial.title}
        </p>
        <p className="mt-1 max-w-prose text-sm leading-relaxed text-status-attention-fg">
          {detail ?? copy.feedback.partial.detail}
        </p>
      </div>
    </div>
  )
}

interface SkeletonBlockProps {
  /** Number of placeholder rows. */
  rows?: number
  label?: string
  className?: string
}

export function SkeletonBlock({ rows = 3, label, className }: SkeletonBlockProps) {
  return (
    <div className={cn('space-y-3', className)} role="status" aria-live="polite">
      <span className="sr-only">{label ?? copy.feedback.loading}</span>
      {Array.from({ length: rows }, (_, index) => (
        <div key={index} className="skeleton h-4" aria-hidden="true" />
      ))}
    </div>
  )
}

interface PanelSkeletonProps {
  title: string
  rows?: number
}

export function PanelSkeleton({ title, rows = 3 }: PanelSkeletonProps) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2 className="panel-title">{title}</h2>
      </div>
      <div className="panel-body">
        <SkeletonBlock rows={rows} />
      </div>
    </section>
  )
}
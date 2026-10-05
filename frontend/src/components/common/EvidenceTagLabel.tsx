/**
 * Evidence provenance tag.
 *
 * P1 requires every data point to declare whether it was observed, derived or
 * inferred. The tag is text only: no dot, no colour-only encoding, so the
 * distinction survives greyscale, high contrast mode and colour vision
 * deficiency. The definition is on the accessible description as well as the
 * tooltip, because a tooltip is unreachable by keyboard and touch.
 */

import type { EvidenceTag } from '@/lib/types'
import { copy } from '@/lib/copy'
import { cn } from '@/lib/cn'

interface EvidenceTagLabelProps {
  tag: EvidenceTag
  /** Set false in dense tables where the definition is already established. */
  showDefinition?: boolean
  className?: string
}

export function EvidenceTagLabel({
  tag,
  showDefinition = true,
  className,
}: EvidenceTagLabelProps) {
  const label = copy.evidence.tags[tag]
  const definition = copy.evidence.tags.tooltip[tag]

  return (
    <span
      className={cn('evidence-tag', className)}
      title={showDefinition ? definition : undefined}
    >
      {label}
      {showDefinition ? <span className="sr-only">: {definition}</span> : null}
    </span>
  )
}
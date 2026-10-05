/**
 * Neutral status badge.
 *
 * Colour is never the only cue. Every badge carries its state as text, which
 * satisfies the accessibility requirement and, more importantly, satisfies the
 * product rule that a state must never read as a verdict: there is no red and no
 * green anywhere in this component, and the tones are neutral, attention and
 * information only.
 */

import { copy } from '@/lib/copy'
import { cn } from '@/lib/cn'
import type { CaseStatus, HeadlineState } from '@/lib/types'

type BadgeTone = 'neutral' | 'attention' | 'info'

interface StatusBadgeProps {
  /** A headline state takes precedence over a lifecycle status. */
  state?: HeadlineState | CaseStatus
  size?: 'sm' | 'md'
  className?: string
}

function toneFor(state: string): BadgeTone {
  switch (state) {
    case 'verified_label_match':
    case 'potential_association':
      return 'info'
    case 'partial':
    case 'failed':
    case 'insufficient_data':
    case 'no_paths_found':
      return 'attention'
    default:
      return 'neutral'
  }
}

/**
 * Headline states reach the label table through an explicit map.
 *
 * The alternative, indexing the table with the raw vocabulary value, needed the
 * table keys to repeat the snake case vocabulary and forced a cast because the
 * lookup key is a runtime string. Naming the keys here keeps the mapping checked
 * by the compiler, so a new headline state that is not covered fails to build
 * rather than silently rendering a de-snake-cased placeholder.
 */
const HEADLINE_LABEL_KEY = {
  failed: 'failed',
  no_paths_found: 'noPaths',
  verified_label_match: 'verified',
  potential_association: 'potential',
  insufficient_data: 'insufficientData',
  no_match_in_current_references: 'noMatch',
} as const satisfies Record<HeadlineState, keyof typeof copy.result.statusBadge>

function labelFor(state: string): string {
  if (state in HEADLINE_LABEL_KEY) {
    const key = HEADLINE_LABEL_KEY[state as HeadlineState]
    return copy.result.statusBadge[key]
  }

  if (state in copy.result.statusBadge) {
    return copy.result.statusBadge[state as CaseStatus]
  }

  return state.replace(/_/g, ' ')
}

export function StatusBadge({ state, size = 'md', className }: StatusBadgeProps) {
  if (!state) return null

  const tone = toneFor(state)

  return (
    <span
      className={cn(
        'badge',
        tone === 'neutral' && 'badge-neutral',
        tone === 'attention' && 'badge-attention',
        tone === 'info' && 'badge-info',
        size === 'sm' && 'text-[0.6875rem]',
        className,
      )}
    >
      {labelFor(state)}
    </span>
  )
}
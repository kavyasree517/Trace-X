/**
 * Analysis stage progress.
 *
 * The six stages are shown as an ordered list rather than a bar, because a bar
 * would imply a measurable proportion of completion and the backend reports
 * stage states only. Each stage states its own outcome in words, and the whole
 * list is a polite live region so a screen reader user learns that analysis
 * finished without having to go looking for the change.
 *
 * The connector line is decorative; the ordering is carried by the list
 * semantics, so removing the visual treatment loses nothing.
 */

import { Check, CircleDashed, CircleSlash, Loader } from 'lucide-react'
import { STAGE_ORDER, type ProgressStages, type StageState } from '@/lib/types'
import { copy } from '@/lib/copy'
import { cn } from '@/lib/cn'

interface ProgressStagesProps {
  stages: ProgressStages
  className?: string
}

const STAGE_LABELS: Record<keyof ProgressStages, string> = {
  retrieval: copy.result.stages.retrieval,
  graph: copy.result.stages.graph,
  attribution: copy.result.stages.attribution,
  behavior: copy.result.stages.behavior,
  corroboration: copy.result.stages.corroboration,
  assembly: copy.result.stages.assembly,
}

function StageIcon({ state }: { state: StageState }) {
  if (state === 'completed') return <Check size={16} strokeWidth={2} aria-hidden="true" />
  if (state === 'failed') return <CircleSlash size={16} strokeWidth={1.5} aria-hidden="true" />
  if (state === 'running') {
    return <Loader size={16} strokeWidth={1.5} aria-hidden="true" className="animate-spin" />
  }
  return <CircleDashed size={16} strokeWidth={1.5} aria-hidden="true" />
}

function stateText(state: StageState): string {
  return copy.result.stages.states[state]
}

export function ProgressStages({ stages, className }: ProgressStagesProps) {
  const active = STAGE_ORDER.find((stage) => stages[stage] === 'running')
  const hasFailure = STAGE_ORDER.some((stage) => stages[stage] === 'failed')

  return (
    <div className={className}>
      {active ? (
        <p aria-live="polite" className="mb-4 text-sm text-secondary">
          {copy.result.stages.running}{' '}
          <span className="font-medium text-primary">
            {STAGE_LABELS[active]} ({stateText(stages[active]).toLowerCase()})
          </span>
        </p>
      ) : null}

      <ol className="grid grid-cols-1 gap-px overflow-hidden rounded-md border border-border bg-border sm:grid-cols-2 lg:grid-cols-3">
        {STAGE_ORDER.map((stage) => {
          const state = stages[stage]
          return (
            <li
              key={stage}
              className={cn(
                'flex items-center gap-3 bg-surface px-4 py-3',
                state === 'running' && 'bg-accent-subtle',
                state === 'failed' && 'bg-status-attention-bg',
              )}
            >
              <span
                className={cn(
                  'shrink-0',
                  state === 'completed' && 'text-accent',
                  state === 'running' && 'text-accent',
                  state === 'failed' && 'text-status-attention-fg',
                  state === 'pending' && 'text-muted',
                )}
              >
                <StageIcon state={state} />
              </span>
              <span className="min-w-0">
                <span className="block text-sm font-medium text-primary">
                  {STAGE_LABELS[stage]}
                </span>
                <span className="block text-xs text-muted">{stateText(state)}</span>
              </span>
            </li>
          )
        })}
      </ol>

      {hasFailure ? (
        <p role="alert" className="mt-4 text-sm text-status-attention-fg">
          {copy.feedback.failed.detail}
        </p>
      ) : null}
    </div>
  )
}
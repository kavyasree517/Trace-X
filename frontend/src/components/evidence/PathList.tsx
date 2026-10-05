/**
 * Ranked fund movement list.
 *
 * The list is a set of disclosure panels rather than a card grid: exactly one
 * path is open at a time, which keeps a long trace scannable and makes the
 * expanded state unambiguous. Each panel itemises every ranking criterion,
 * because the ranking exists only to order display and must be reproducible by
 * the reader from the values shown. No total, weight or position score appears
 * anywhere in this component.
 */

import { useState } from 'react'
import type { PathItem, PathResponse } from '@/lib/types'
import { EvidenceTagLabel } from '@/components/common/EvidenceTagLabel'
import { ExpandablePanel } from '@/components/common/ExpandablePanel'
import { PathGraph } from '@/components/graph/PathGraph'
import { EdgeTable } from '@/components/evidence/EdgeTable'
import { EmptyState } from '@/components/feedback/EmptyState'
import { copy, vocabularyLabel } from '@/lib/copy'
import { formatAssetAmount, formatDuration, formatRatio, pluralise } from '@/lib/format'

interface PathListProps {
  paths: PathResponse
  /** Path to open initially. Defaults to the first, which is the top ranked. */
  initialPathIndex?: number
}

interface CriterionRow {
  key: keyof PathItem['relevance_criteria']
  label: string
  value: string
}

function criteriaRows(path: PathItem): CriterionRow[] {
  const criteria = path.relevance_criteria
  const yes = copy.evidence.paths.truthy
  const no = copy.evidence.paths.falsy

  return [
    {
      key: 'anchored_to_reported_tx',
      label: copy.evidence.paths.criteria.anchored_to_reported_tx,
      value: criteria.anchored_to_reported_tx ? yes : no,
    },
    {
      key: 'continuity_ratio',
      label: copy.evidence.paths.criteria.continuity_ratio,
      value: formatRatio(criteria.continuity_ratio),
    },
    {
      key: 'time_proximity_hours',
      label: copy.evidence.paths.criteria.time_proximity_hours,
      value:
        criteria.time_proximity_hours < 1
          ? `${Math.round(criteria.time_proximity_hours * 60)} minutes`
          : `${criteria.time_proximity_hours.toFixed(1)} hours`,
    },
    {
      key: 'hop_count',
      label: copy.evidence.paths.criteria.hop_count,
      value: String(criteria.hop_count),
    },
    {
      key: 'terminal_labelled',
      label: copy.evidence.paths.criteria.terminal_labelled,
      value: criteria.terminal_labelled ? yes : no,
    },
  ]
}

export function PathList({ paths, initialPathIndex }: PathListProps) {
  const [openPathIndex, setOpenPathIndex] = useState<number | null>(
    paths.paths.length > 0 ? (initialPathIndex ?? paths.paths[0].path_index) : null,
  )

  if (paths.paths.length === 0) {
    return <EmptyState detail={copy.evidence.paths.emptyState} />
  }

  return (
    <div className="space-y-3">
      {paths.paths.map((path) => {
        const isOpen = openPathIndex === path.path_index

        return (
          <ExpandablePanel
            key={path.path_index}
            title={`Path ${path.path_index} of ${paths.paths.length}`}
            description={`${pluralise(path.hop_count, 'transfer')} to ${path.end_address.slice(0, 6)}...${path.end_address.slice(-4)}`}
            open={isOpen}
            onOpenChange={(next) => setOpenPathIndex(next ? path.path_index : null)}
            className={isOpen ? 'border-accent-border' : undefined}
          >
            <div className="space-y-5">
              <dl className="grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-4">
                <div>
                  <dt className="eyebrow mb-1">Traced value</dt>
                  <dd className="text-sm font-medium text-primary">
                    {formatAssetAmount(path.traced_value_amount, path.traced_value_asset)}
                  </dd>
                </div>
                <div>
                  <dt className="eyebrow mb-1">Continuity</dt>
                  <dd className="text-sm text-secondary">
                    {formatRatio(path.value_continuity_ratio)}
                  </dd>
                </div>
                <div>
                  <dt className="eyebrow mb-1">Elapsed</dt>
                  <dd className="text-sm text-secondary">
                    {formatDuration(path.elapsed_seconds)}
                  </dd>
                </div>
                <div>
                  <dt className="eyebrow mb-1">Tracing method</dt>
                  <dd className="text-sm text-secondary">
                    {vocabularyLabel('tracingMethod', path.tracing_method)}
                  </dd>
                </div>
              </dl>

              <div className="flex flex-wrap items-center gap-2">
                <EvidenceTagLabel tag={path.evidence_tag} />
                {path.has_break && path.break_reason ? (
                  <span className="badge badge-attention">
                    Trace stops: {vocabularyLabel('breakReason', path.break_reason)}
                  </span>
                ) : null}
              </div>

              <div>
                <p className="eyebrow mb-2">{copy.evidence.paths.criteriaTitle}</p>
                <dl className="grid grid-cols-1 gap-px overflow-hidden rounded-md border border-border bg-border sm:grid-cols-2">
                  {criteriaRows(path).map((row) => (
                    <div
                      key={row.key}
                      className="flex items-baseline justify-between gap-4 bg-surface px-3 py-2"
                    >
                      <dt className="text-sm text-secondary">{row.label}</dt>
                      <dd className="font-mono text-sm text-primary">{row.value}</dd>
                    </div>
                  ))}
                </dl>
              </div>

              <div>
                <p className="eyebrow mb-2">{copy.evidence.paths.graphTitle}</p>
                <PathGraph path={path} />
              </div>

              <div>
                <p className="eyebrow mb-2">{copy.evidence.paths.tableTitle}</p>
                <EdgeTable edges={path.edges} showEndpoints />
              </div>
            </div>
          </ExpandablePanel>
        )
      })}

      {paths.omitted_count > 0 ? (
        <p className="rounded-md border border-border bg-surface-subtle px-3.5 py-3 text-sm text-secondary">
          {copy.evidence.paths.omitted(paths.omitted_count)}
        </p>
      ) : null}

      <p className="max-w-prose text-xs leading-relaxed text-muted">
        {copy.evidence.paths.traceDisclaimer}
      </p>
    </div>
  )
}
/**
 * Limitations list.
 *
 * P10 requires a limitations block on every result. Notes are grouped so the
 * standing statement reads as a conclusion rather than as one item among many,
 * and the analysis timestamp and snapshot identifier are shown as recorded facts
 * because reproducibility depends on the reader knowing which snapshot they are
 * looking at.
 */

import type { LimitationsBlock } from '@/lib/types'
import { copy } from '@/lib/copy'
import { Timestamp } from '@/components/common/Timestamp'

interface LimitationsPanelProps {
  limitations: LimitationsBlock
  /** Extra notes contributed by the individual panel, for example a break. */
  extraNotes?: string[]
}

export function LimitationsPanel({ limitations, extraNotes = [] }: LimitationsPanelProps) {
  const notes = [...limitations.notes, ...extraNotes]

  return (
    <div className="space-y-5">
      <dl className="grid grid-cols-1 gap-x-8 gap-y-3 border-b border-border-subtle pb-4 sm:grid-cols-2">
        <div>
          <dt className="eyebrow mb-1">{copy.evidence.limitations.analysisTimestamp}</dt>
          <dd>
            <Timestamp value={limitations.analysis_timestamp} showToggle />
          </dd>
        </div>
        <div>
          <dt className="eyebrow mb-1">{copy.evidence.limitations.dataSnapshot}</dt>
          <dd className="font-mono text-sm text-secondary">
            {limitations.data_snapshot_id ?? copy.evidence.limitations.dataSnapshotMissing}
          </dd>
        </div>
      </dl>

      {notes.length > 0 ? (
        <div>
          <p className="eyebrow mb-3">What this result does not cover</p>
          <ul className="max-w-prose space-y-2.5">
            {notes.map((note, index) => (
              <li key={`${index}-${note.slice(0, 24)}`} className="flex gap-3 text-sm leading-relaxed text-secondary">
                <span aria-hidden="true" className="mt-2 h-1 w-1 shrink-0 rounded-full bg-border-strong" />
                <span>{note}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="text-sm text-secondary">{copy.feedback.empty.detail}</p>
      )}

      <p className="rounded-md border border-border bg-surface-subtle p-4 text-sm leading-relaxed text-primary">
        {limitations.standing_statement}
      </p>
    </div>
  )
}
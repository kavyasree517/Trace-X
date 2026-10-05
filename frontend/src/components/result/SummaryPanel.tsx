/**
 * Summary panel: the headline state and the narrative behind it.
 *
 * Order is deliberate. The state is announced first as a badge, then the
 * reported address as the subject of the check, then the narrative, then the
 * standing statement. The standing statement sits inside the panel rather than
 * only in the footer because a reader who screenshots this panel must carry the
 * caveat with the image.
 */

import { StatusBadge } from './StatusBadge'
import { DemoNotice } from './DemoNotice'
import { MonoText } from '@/components/common/MonoText'
import { Timestamp } from '@/components/common/Timestamp'
import { copy } from '@/lib/copy'
import type { CaseSummaryResponse } from '@/lib/types'

interface SummaryPanelProps {
  summary: CaseSummaryResponse
}

export function SummaryPanel({ summary }: SummaryPanelProps) {
  return (
    <div className="space-y-5">
      {summary.demo_notice ? <DemoNotice text={summary.demo_notice} /> : null}

      <div className="flex flex-wrap items-center gap-3">
        <StatusBadge state={summary.headline_state} />
        <span className="text-sm text-muted">
          {copy.result.chainLabel}: {summary.chain}
        </span>
      </div>

      <dl className="grid grid-cols-1 gap-x-8 gap-y-4 sm:grid-cols-2">
        <div className="min-w-0">
          <dt className="eyebrow mb-1">Reported address</dt>
          <dd className="min-w-0">
            <MonoText
              value={summary.reported_address}
              copyLabel="reported wallet address"
              alwaysFull={false}
            />
          </dd>
        </div>
        <div className="min-w-0">
          <dt className="eyebrow mb-1">{copy.result.caseLabel}</dt>
          <dd className="font-mono text-sm text-secondary">{summary.case_reference}</dd>
        </div>
        <div className="min-w-0">
          <dt className="eyebrow mb-1">{copy.result.analysedLabel}</dt>
          <dd>
            <Timestamp value={summary.limitations.analysis_timestamp} showToggle />
          </dd>
        </div>
        <div className="min-w-0">
          <dt className="eyebrow mb-1">{copy.evidence.limitations.dataSnapshot}</dt>
          <dd className="font-mono text-sm text-secondary">
            {summary.limitations.data_snapshot_id ?? copy.evidence.limitations.dataSnapshotMissing}
          </dd>
        </div>
      </dl>

      <div className="rounded-md border border-border-subtle bg-surface-subtle p-4">
        <p className="max-w-prose text-base leading-relaxed text-primary">
          {summary.summary_text}
        </p>
      </div>

      <p className="max-w-prose border-t border-border-subtle pt-4 text-xs leading-relaxed text-muted">
        {summary.limitations.standing_statement}
      </p>
    </div>
  )
}
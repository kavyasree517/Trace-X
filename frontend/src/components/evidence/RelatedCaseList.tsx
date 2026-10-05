/**
 * Related report list.
 *
 * Privacy constraints shape this component as much as the visual ones. Another
 * reporter's narrative, contact reference and reported amount are never present
 * here and are not fetched, so there is nothing to leak: only the case reference,
 * the strength, and the shared chain evidence itself. When a case has not
 * consented to being listed, the backend returns an aggregate count and no
 * reference, and this component shows the count without inventing a way to reach
 * the other report.
 *
 * The mandatory caution is rendered once above the list and again on any entry
 * whose only overlap is shared infrastructure, because that is the specific
 * situation in which a reader is most likely to over-read the connection.
 */

import type { CorroborationResponse } from '@/lib/types'
import { MonoText } from '@/components/common/MonoText'
import { EvidenceTagLabel } from '@/components/common/EvidenceTagLabel'
import { ExpandablePanel } from '@/components/common/ExpandablePanel'
import { EmptyState } from '@/components/feedback/EmptyState'
import { copy, vocabularyLabel } from '@/lib/copy'

interface RelatedCaseListProps {
  corroboration: CorroborationResponse
}

export function RelatedCaseList({ corroboration }: RelatedCaseListProps) {
  const { related_cases: relatedCases, total_matches: totalMatches, mandatory_caution: caution } =
    corroboration

  if (relatedCases.length === 0) {
    return (
      <div className="space-y-4">
        <EmptyState detail={copy.evidence.related.emptyState} />
        <p className="max-w-prose text-xs leading-relaxed text-muted">{caution}</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <p className="rounded-md border border-border bg-surface-subtle px-3.5 py-3 text-sm leading-relaxed text-secondary">
        {caution}
      </p>

      <ul className="space-y-3">
        {relatedCases.map((related) => (
          <li key={related.case_reference}>
            <ExpandablePanel
              title={related.case_reference}
              description={`${copy.evidence.related.strength}: ${vocabularyLabel('corroborationStrength', related.strength)}`}
              defaultOpen={related.strength === 'strong'}
              className={related.strength === 'strong' ? 'border-accent-border' : undefined}
            >
              <div className="space-y-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={
                      related.strength === 'none' ? 'badge badge-neutral' : 'badge badge-info'
                    }
                  >
                    {copy.evidence.related.strength}:{' '}
                    {vocabularyLabel('corroborationStrength', related.strength)}
                  </span>
                  <EvidenceTagLabel tag={related.evidence_tag} />
                  {related.shared_infrastructure_flag ? (
                    <span className="badge badge-neutral">
                      Shared infrastructure
                    </span>
                  ) : null}
                </div>

                {related.shared_infrastructure_flag ? (
                  <p className="rounded-md border border-status-attention-border bg-status-attention-bg px-3 py-2.5 text-sm leading-relaxed text-status-attention-fg">
                    {related.caution_notice}
                  </p>
                ) : null}

                <dl className="space-y-4">
                  {related.shared_addresses.length > 0 ? (
                    <div>
                      <dt className="eyebrow mb-2">
                        {copy.evidence.related.sharedAddresses} ({related.shared_addresses.length})
                      </dt>
                      <dd className="space-y-1.5">
                        {related.shared_addresses.map((address) => (
                          <div key={address} className="flex items-center gap-1">
                            <MonoText
                              value={address}
                              copyLabel="shared address"
                              alwaysFull={false}
                            />
                          </div>
                        ))}
                      </dd>
                    </div>
                  ) : null}

                  {related.shared_transactions.length > 0 ? (
                    <div>
                      <dt className="eyebrow mb-2">
                        {copy.evidence.related.sharedTransactions} (
                        {related.shared_transactions.length})
                      </dt>
                      <dd className="space-y-1.5">
                        {related.shared_transactions.map((hash) => (
                          <div key={hash} className="flex items-center gap-1">
                            <MonoText
                              value={hash}
                              variant="hash"
                              copyLabel="shared transaction hash"
                            />
                          </div>
                        ))}
                      </dd>
                    </div>
                  ) : null}

                  {related.shared_path_segments.length > 0 ? (
                    <div>
                      <dt className="eyebrow mb-2">
                        {copy.evidence.related.sharedSegments} (
                        {related.shared_path_segments.length})
                      </dt>
                      <dd className="space-y-1.5">
                        {related.shared_path_segments.map((segment) => (
                          <p
                            key={segment}
                            className="break-all font-mono text-xs text-secondary"
                          >
                            {segment}
                          </p>
                        ))}
                      </dd>
                    </div>
                  ) : null}

                  {related.temporal_notes ? (
                    <div>
                      <dt className="eyebrow mb-1">{copy.evidence.related.temporalNotes}</dt>
                      <dd className="text-sm text-secondary">{related.temporal_notes}</dd>
                    </div>
                  ) : null}
                </dl>
              </div>
            </ExpandablePanel>
          </li>
        ))}
      </ul>

      {totalMatches > relatedCases.length ? (
        <p className="rounded-md border border-border bg-surface-subtle px-3.5 py-3 text-sm text-secondary">
          {copy.evidence.related.aggregateOnly}
        </p>
      ) : null}
    </div>
  )
}
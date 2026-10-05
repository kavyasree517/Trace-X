/**
 * Attribution card for one labelled destination.
 *
 * Order inside the card is fixed by what a reader needs in order to judge it:
 * what was concluded, how the trace reached it, how well the label is supported,
 * then the full provenance, then the reasoning. The disclaimers sit inside the
 * card because a card is the unit a reader screenshots or forwards, and P4
 * requires that the absence of an inference travels with the claim.
 */

import type { AttributionItem, AttributionResponse } from '@/lib/types'
import { EvidenceTagLabel } from '@/components/common/EvidenceTagLabel'
import { ExpandablePanel } from '@/components/common/ExpandablePanel'
import { LabelProvenanceTable } from '@/components/evidence/LabelProvenanceTable'
import { EmptyState } from '@/components/feedback/EmptyState'
import { copy, vocabularyLabel } from '@/lib/copy'

interface AttributionListProps {
  attributions: AttributionResponse
}

export function AttributionList({ attributions }: AttributionListProps) {
  if (attributions.attributions.length === 0) {
    return (
      <div className="space-y-3">
        <EmptyState
          title={copy.evidence.attribution.emptyState}
          detail={copy.evidence.attribution.emptyStateDetail}
        />
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {attributions.attributions.map((attribution, index) => (
        <AttributionCard
          key={`${attribution.label.address}-${index}`}
          attribution={attribution}
        />
      ))}

      <p className="max-w-prose rounded-md border border-border bg-surface-subtle px-3.5 py-3 text-sm leading-relaxed text-secondary">
        {copy.evidence.attribution.disclaimer}
      </p>
    </div>
  )
}

interface AttributionCardProps {
  attribution: AttributionItem
}

function AttributionCard({ attribution }: AttributionCardProps) {
  const { label, confidence_factors: factors } = attribution

  const factorRows: Array<{ term: string; value: React.ReactNode }> = [
    {
      term: copy.evidence.attribution.factors.verification_level,
      value: vocabularyLabel('verificationLevel', factors.verification_level),
    },
    {
      term: copy.evidence.attribution.factors.label_origin,
      value: vocabularyLabel('labelOrigin', factors.label_origin),
    },
    {
      term: copy.evidence.attribution.factors.label_is_stale,
      value: factors.label_is_stale ? copy.common.yes : copy.common.no,
    },
    {
      term: copy.evidence.attribution.factors.scope_match,
      value: factors.scope_match ? copy.common.yes : copy.common.no,
    },
    {
      term: copy.evidence.attribution.factors.independent_source_count,
      value: copy.evidence.attribution.sourceCount(factors.independent_source_count),
    },
    {
      term: copy.evidence.attribution.factors.connection_type,
      value: vocabularyLabel('connectionType', factors.connection_type),
    },
    {
      term: copy.evidence.attribution.factors.path_intact,
      value: factors.path_intact ? copy.common.yes : copy.common.no,
    },
  ]

  return (
    <ExpandablePanel
      title={label.entity_name}
      description={`${vocabularyLabel('attributionState', attribution.attribution_state)} - ${vocabularyLabel('connectionType', attribution.connection_type)}`}
      defaultOpen
    >
      <div className="space-y-5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="badge badge-info">
            {vocabularyLabel('attributionState', attribution.attribution_state)}
          </span>
          <span className="badge badge-neutral">
            {copy.evidence.attribution.connection}: {vocabularyLabel('connectionType', attribution.connection_type)}
          </span>
          <span className="badge badge-neutral">
            {copy.evidence.attribution.confidence}: {vocabularyLabel('signalLevel', confidenceLevelToSignal(attribution.confidence_level))}
          </span>
          <EvidenceTagLabel tag={attribution.evidence_tag} />
        </div>

        <p className="max-w-prose text-sm leading-relaxed text-secondary">
          {attribution.explanation}
        </p>

        {attribution.label_is_stale ? (
          <p className="flex items-start gap-2 rounded-md border border-status-attention-border bg-status-attention-bg px-3 py-2.5 text-sm text-status-attention-fg">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-status-attention-fg" aria-hidden="true" />
            {copy.evidence.attribution.staleNote}
          </p>
        ) : null}

        {attribution.shared_infrastructure_flag ? (
          <div className="rounded-md border border-border bg-surface-subtle px-3.5 py-3">
            <p className="badge badge-neutral mb-2">
              {copy.evidence.attribution.sharedInfrastructure}
            </p>
            <p className="max-w-prose text-sm leading-relaxed text-secondary">
              {copy.evidence.attribution.sharedInfrastructureNote}
            </p>
          </div>
        ) : null}

        <div>
          <p className="eyebrow mb-2">{copy.evidence.attribution.factorsTitle}</p>
          <dl className="grid grid-cols-1 gap-px overflow-hidden rounded-md border border-border bg-border sm:grid-cols-2">
            {factorRows.map((row) => (
              <div
                key={row.term}
                className="flex items-baseline justify-between gap-4 bg-surface px-3 py-2"
              >
                <dt className="text-sm text-secondary">{row.term}</dt>
                <dd className="text-sm text-primary">{row.value}</dd>
              </div>
            ))}
          </dl>
        </div>

        <LabelProvenanceTable label={label} isStale={attribution.label_is_stale} />
      </div>
    </ExpandablePanel>
  )
}

/**
 * Map an attribution confidence level onto the signal level vocabulary so the
 * two do not need two parallel sets of wording on screen.
 */
function confidenceLevelToSignal(level: AttributionItem['confidence_level']) {
  switch (level) {
    case 'high':
      return 'observed_high'
    case 'medium':
      return 'observed_moderate'
    case 'low':
      return 'observed_low'
    default:
      return 'not_observed'
  }
}
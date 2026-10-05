/**
 * Label provenance table.
 *
 * P7 requires a label to carry its full provenance, and this table is where that
 * becomes auditable: source, reference link, verification level and both dates
 * are shown together, and a stale label is marked in text. Only the fields the
 * backend actually returns are rendered, so the table cannot imply provenance
 * that was not recorded.
 */

import type { LabelProvenance } from '@/lib/types'
import { MonoText } from '@/components/common/MonoText'
import { ExternalLink } from '@/components/common/ExternalLink'
import { copy, vocabularyLabel } from '@/lib/copy'
import { formatDateOnly } from '@/lib/format'

interface LabelProvenanceTableProps {
  label: LabelProvenance
  /** Marks the label as outside the freshness window. */
  isStale?: boolean
}

export function LabelProvenanceTable({ label, isStale = false }: LabelProvenanceTableProps) {
  const rows: Array<{ term: string; value: React.ReactNode }> = [
    {
      term: copy.evidence.attribution.provenance.entity_name,
      value: <span className="font-medium text-primary">{label.entity_name}</span>,
    },
    {
      term: copy.evidence.attribution.provenance.entity_type,
      value: vocabularyLabel('entityType', label.entity_type),
    },
    {
      term: copy.evidence.attribution.provenance.address,
      value: (
        <MonoText
          value={label.address}
          alwaysFull
          showCopy={false}
          className="break-all"
        />
      ),
    },
    {
      term: copy.evidence.attribution.provenance.label_origin,
      value: vocabularyLabel('labelOrigin', label.label_origin),
    },
    {
      term: copy.evidence.attribution.provenance.source_name,
      value: <span className="text-primary">{label.source_name}</span>,
    },
    {
      term: copy.evidence.attribution.provenance.source_type,
      value: vocabularyLabel('sourceType', label.source_type),
    },
    {
      term: copy.evidence.attribution.provenance.source_reference,
      value: (
        <ExternalLink
          href={label.source_reference}
          accessibleName={`${copy.evidence.attribution.provenance.source_reference}: ${label.source_name}`}
        >
          {label.source_reference.replace(/^https?:\/\//, '').slice(0, 60)}
        </ExternalLink>
      ),
    },
    {
      term: copy.evidence.attribution.provenance.verification_level,
      value: (
        <span
          className={
            label.verification_level === 'level_0_synthetic' ? 'badge badge-attention' : 'badge badge-info'
          }
        >
          {vocabularyLabel('verificationLevel', label.verification_level)}
        </span>
      ),
    },
    {
      term: copy.evidence.attribution.provenance.observed_at,
      value: formatDateOnly(label.observed_at),
    },
    {
      term: copy.evidence.attribution.provenance.last_verified_at,
      value: (
        <span className={isStale ? 'text-status-attention-fg' : undefined}>
          {formatDateOnly(label.last_verified_at)}
        </span>
      ),
    },
  ]

  if (label.scope_notes) {
    rows.push({
      term: copy.evidence.attribution.provenance.scope_notes,
      value: <span className="text-secondary">{label.scope_notes}</span>,
    })
  }

  if (label.cluster_id) {
    rows.push({
      term: copy.evidence.attribution.provenance.cluster_id,
      value: <span className="font-mono text-sm">{label.cluster_id}</span>,
    })
  }

  if (label.notes) {
    rows.push({
      term: copy.evidence.attribution.provenance.notes,
      value: <span className="text-secondary">{label.notes}</span>,
    })
  }

  rows.push({
    term: copy.evidence.attribution.provenance.is_active,
    value: label.is_active ? copy.common.yes : copy.common.no,
  })

  return (
    <div className="table-scroll rounded-md border border-border">
      <table className="data-table">
        <caption className="px-3 pt-3">{copy.evidence.attribution.provenanceTitle}</caption>
        <tbody>
          {rows.map((row) => (
            <tr key={row.term}>
              <th scope="row" className="w-48 align-top normal-case tracking-normal normal-case">
                <span className="text-sm font-normal normal-case tracking-normal text-secondary">
                  {row.term}
                </span>
              </th>
              <td className="text-sm text-secondary">{row.value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
/**
 * Observed transfer table.
 *
 * This is both a primary view and the permanent accessible alternative to the
 * path graph. It stays available regardless of which view is showing, because a
 * graph is unusable with a screen reader and awkward on a narrow screen, and the
 * table carries strictly more information than the diagram does.
 *
 * Every column is a P6 field, so a reader can re-check any single transfer
 * against an independent source without leaving the page.
 */

import { ExternalLink as ExternalLinkIcon } from 'lucide-react'
import type { TransactionItem } from '@/lib/types'
import { MonoText } from '@/components/common/MonoText'
import { ExternalLink } from '@/components/common/ExternalLink'
import { EvidenceTagLabel } from '@/components/common/EvidenceTagLabel'
import { Timestamp } from '@/components/common/Timestamp'
import { formatAssetAmount } from '@/lib/format'
import { copy, vocabularyLabel } from '@/lib/copy'
import { txPath } from '@/lib/explorer'

interface EdgeTableProps {
  edges: TransactionItem[]
  /** Highlights the first and last row, marking the ends of the path. */
  showEndpoints?: boolean
}

export function EdgeTable({ edges, showEndpoints = false }: EdgeTableProps) {
  if (edges.length === 0) {
    return <p className="text-sm text-muted">{copy.common.none}</p>
  }

  return (
    <div className="table-scroll rounded-md border border-border">
      <table className="data-table">
        <caption className="px-3 pt-3">{copy.evidence.edgeTable.caption}</caption>
        <thead>
          <tr>
            <th scope="col">#</th>
            <th scope="col">{copy.evidence.edgeTable.time}</th>
            <th scope="col">{copy.evidence.edgeTable.from}</th>
            <th scope="col">{copy.evidence.edgeTable.to}</th>
            <th scope="col">{copy.evidence.edgeTable.amount}</th>
            <th scope="col">{copy.evidence.edgeTable.kind}</th>
            <th scope="col">{copy.evidence.edgeTable.transaction}</th>
            <th scope="col">{copy.evidence.edgeTable.block}</th>
            <th scope="col">Status</th>
          </tr>
        </thead>
        <tbody>
          {edges.map((edge, index) => {
            const isFailed = edge.status !== 'success'
            return (
              <tr key={`${edge.tx_hash}-${edge.log_index}`}>
                <td className="font-mono text-xs text-muted">
                  {index + 1}
                  {showEndpoints && index === 0 ? (
                    <span className="ml-1 text-accent">(start)</span>
                  ) : null}
                  {showEndpoints && index === edges.length - 1 && edges.length > 1 ? (
                    <span className="ml-1 text-accent">(end)</span>
                  ) : null}
                </td>
                <td className="whitespace-nowrap">
                  <Timestamp value={edge.block_timestamp} />
                  {isFailed ? (
                    <p className="mt-1 max-w-[22ch] text-xs text-status-attention-fg">
                      {copy.evidence.edgeTable.failedNote}
                    </p>
                  ) : null}
                </td>
                <td>
                  <MonoText value={edge.sender} copyLabel="sender address" />
                </td>
                <td>
                  <MonoText value={edge.receiver} copyLabel="receiver address" />
                </td>
                <td className="whitespace-nowrap font-medium text-primary">
                  {formatAssetAmount(edge.amount_decimal, edge.asset_symbol)}
                </td>
                <td className="whitespace-nowrap text-xs">
                  {vocabularyLabel('transferKind', edge.transfer_kind)}
                </td>
                <td>
                  <div className="flex items-center gap-1">
                    <MonoText value={edge.tx_hash} variant="hash" copyLabel="transaction hash" />
                    <ExternalLink
                      href={txPath(edge.tx_hash)}
                      accessibleName={`${copy.common.onExplorer}: transaction ${edge.tx_hash}`}
                      showIcon={false}
                      className="shrink-0 px-1"
                    >
                      <ExternalLinkIcon size={14} strokeWidth={1.5} aria-hidden="true" />
                    </ExternalLink>
                  </div>
                  <p className="mt-1 font-mono text-xs text-muted">
                    log {edge.log_index} &middot; {edge.source}
                  </p>
                  <div className="mt-1">
                    <EvidenceTagLabel tag={edge.evidence_tag} showDefinition={false} />
                  </div>
                </td>
                <td className="whitespace-nowrap font-mono text-xs">{edge.block_number}</td>
                <td className="whitespace-nowrap">
                  <span
                    className={
                      isFailed
                        ? 'badge badge-attention'
                        : 'badge badge-neutral'
                    }
                  >
                    {edge.status}
                  </span>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
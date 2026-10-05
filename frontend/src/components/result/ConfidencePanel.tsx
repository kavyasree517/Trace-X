/**
 * Confidence panel: four independent assessments.
 *
 * P2 forbids a single combined score, a percentage or a probability, so this
 * panel is structurally incapable of producing one. The four entries are four
 * separate `div`s rather than a list whose values could be summed, no progress
 * bar or meter is rendered, and no visual weighting is applied that would imply
 * the entries trade off against each other. Every entry is plain prose from the
 * backend, which is why the layout has room for a sentence per row.
 *
 * Each row is a definition pair so the term and its explanation are announced
 * together, and each carries a hint describing what the entry does and does not
 * measure.
 */

import type { ConfidencePanel as ConfidencePanelData } from '@/lib/types'
import { copy } from '@/lib/copy'

interface ConfidencePanelProps {
  panel: ConfidencePanelData
}

interface Row {
  key: keyof ConfidencePanelData
  label: string
  hint: string
}

const ROWS: Row[] = [
  {
    key: 'path_evidence',
    label: copy.result.confidencePanel.pathEvidence,
    hint: copy.result.confidencePanel.pathEvidenceHint,
  },
  {
    key: 'attribution_confidence',
    label: copy.result.confidencePanel.attributionConfidence,
    hint: copy.result.confidencePanel.attributionConfidenceHint,
  },
  {
    key: 'behavioral_signals',
    label: copy.result.confidencePanel.behavioralSignals,
    hint: copy.result.confidencePanel.behavioralSignalsHint,
  },
  {
    key: 'corroboration_strength',
    label: copy.result.confidencePanel.corroborationStrength,
    hint: copy.result.confidencePanel.corroborationStrengthHint,
  },
]

export function ConfidencePanel({ panel }: ConfidencePanelProps) {
  return (
    <div>
      <p className="mb-4 max-w-prose text-sm text-secondary">
        {copy.result.confidencePanel.lead}
      </p>

      <dl className="grid grid-cols-1 gap-px overflow-hidden rounded-md border border-border bg-border sm:grid-cols-2">
        {ROWS.map((row) => (
          <div key={row.key} className="bg-surface p-4">
            <dt className="flex items-baseline gap-2 text-sm font-medium text-primary">
              <span
                aria-hidden="true"
                className="font-mono text-xs text-muted"
              >
                {String(ROWS.indexOf(row) + 1).padStart(2, '0')}
              </span>
              {row.label}
            </dt>
            <dd className="mt-2">
              <p className="text-sm leading-relaxed text-secondary">{panel[row.key]}</p>
              <p className="mt-2 text-xs leading-normal text-muted">{row.hint}</p>
            </dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
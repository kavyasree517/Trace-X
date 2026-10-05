/**
 * Behavioural signal list.
 *
 * Every signal carries the fixed limitation note, which is rendered as part of
 * the row rather than once at the top of the panel. Repeating it is deliberate:
 * a reader who screenshots a single signal, or arrives at one via an anchor,
 * must still see the caveat that a pattern can result from legitimate activity.
 *
 * Levels are stated in words. No meter, bar or percentage appears, because a
 * signal level describes pattern strength and must never read as a likelihood.
 */

import type { SignalItem, SignalResponse } from '@/lib/types'
import { EvidenceTagLabel } from '@/components/common/EvidenceTagLabel'
import { ExpandablePanel } from '@/components/common/ExpandablePanel'
import { EmptyState } from '@/components/feedback/EmptyState'
import { copy, humanise, vocabularyLabel } from '@/lib/copy'
import { cn } from '@/lib/cn'

interface SignalListProps {
  signals: SignalResponse
}

/** Signals that were actually observed, ordered strongest first. */
function observedOnly(signals: SignalItem[]): SignalItem[] {
  const order: Record<string, number> = {
    observed_high: 0,
    observed_moderate: 1,
    observed_low: 2,
    not_observed: 3,
  }
  return [...signals].sort((a, b) => (order[a.level] ?? 9) - (order[b.level] ?? 9))
}

function levelTone(level: SignalItem['level']): 'neutral' | 'info' | 'attention' {
  if (level === 'observed_high') return 'attention'
  if (level === 'observed_moderate') return 'info'
  return 'neutral'
}

function featureLabel(key: string): string {
  return humanise(key.replace(/_/g, ' '))
}

function featureValue(value: unknown): string {
  if (value === null || value === undefined) return copy.common.notRecorded
  if (typeof value === 'boolean') return value ? copy.common.yes : copy.common.no
  if (typeof value === 'number') return value.toLocaleString('en-GB')
  if (Array.isArray(value)) return value.join(', ')
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

export function SignalList({ signals }: SignalListProps) {
  if (signals.signals.length === 0) {
    return <EmptyState detail={copy.evidence.signals.emptyState} />
  }

  const ordered = observedOnly(signals.signals)
  const observedCount = ordered.filter((signal) => signal.level !== 'not_observed').length

  return (
    <div className="space-y-4">
      <p className="text-sm text-secondary">
        {observedCount} of {signals.total} checks observed a pattern.{' '}
        {copy.evidence.signals.note}
      </p>

      <ul className="space-y-3">
        {ordered.map((signal) => (
          <li key={signal.signal_key}>
            <ExpandablePanel
              title={vocabularyLabel('signalKey', signal.signal_key)}
              description={undefined}
              className={cn(
                signal.level !== 'not_observed' && signal.level !== 'observed_low'
                  ? 'border-accent-border'
                  : undefined,
              )}
            >
              <div className="space-y-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={cn(
                      'badge',
                      levelTone(signal.level) === 'attention' && 'badge-attention',
                      levelTone(signal.level) === 'info' && 'badge-info',
                      levelTone(signal.level) === 'neutral' && 'badge-neutral',
                    )}
                  >
                    {vocabularyLabel('signalLevel', signal.level)}
                  </span>
                  <EvidenceTagLabel tag={signal.evidence_tag} />
                </div>

                <p className="max-w-prose text-sm leading-relaxed text-secondary">
                  {signal.explanation}
                </p>

                {Object.keys(signal.feature_values).length > 0 ? (
                  <div>
                    <p className="eyebrow mb-2">{copy.evidence.signals.featuresTitle}</p>
                    <dl className="grid grid-cols-1 gap-px overflow-hidden rounded-md border border-border bg-border sm:grid-cols-2">
                      {Object.entries(signal.feature_values).map(([key, value]) => (
                        <div
                          key={key}
                          className="flex items-baseline justify-between gap-4 bg-surface px-3 py-2"
                        >
                          <dt className="text-sm text-secondary">{featureLabel(key)}</dt>
                          <dd className="font-mono text-sm text-primary">{featureValue(value)}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                ) : null}

                <p className="rounded-md border border-border-subtle bg-surface-subtle px-3 py-2.5 text-xs leading-relaxed text-secondary">
                  {signal.limitation_note}
                </p>
              </div>
            </ExpandablePanel>
          </li>
        ))}
      </ul>
    </div>
  )
}
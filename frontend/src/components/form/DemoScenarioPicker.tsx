/**
 * Demonstration scenario picker.
 *
 * Rendered only when the local demonstration dataset is active. Every outcome the
 * result page has to handle is one click away here, which is what makes the state
 * coverage reviewable in a browser rather than only in tests.
 *
 * Choosing a scenario fills the address field rather than navigating directly, so
 * the normal submit path is still the one being exercised and the reference the
 * browser ends up on reflects what a reporter would actually get.
 */

import { FlaskConical } from 'lucide-react'
import { MonoText } from '@/components/common/MonoText'
import { copy } from '@/lib/copy'
import { cn } from '@/lib/cn'

export interface DemoScenarioEntry {
  id: string
  title: string
  description: string
  address: string
}

interface DemoScenarioPickerProps {
  scenarios: DemoScenarioEntry[]
  onSelect: (entry: DemoScenarioEntry) => void
  selectedId?: string
  /** Arms a one-shot injected failure, so the error states are reachable. */
  onSimulateError?: (kind: ErrorSimulationKind) => void
}

export type ErrorSimulationKind = 'rate_limited' | 'upstream_unavailable'

const ERROR_SIMULATIONS: Array<{ kind: ErrorSimulationKind; label: string; detail: string }> = [
  {
    kind: 'rate_limited',
    label: 'Rate limited',
    detail: 'Fails the next request with 429 and a Retry-After of 30 seconds.',
  },
  {
    kind: 'upstream_unavailable',
    label: 'Chain data unavailable',
    detail: 'Fails the next request as an upstream error.',
  },
]

export function DemoScenarioPicker({
  scenarios,
  onSelect,
  selectedId,
  onSimulateError,
}: DemoScenarioPickerProps) {
  if (scenarios.length === 0) return null

  return (
    <section className="panel border-status-attention-border">
      <div className="panel-heading border-status-attention-border bg-status-attention-bg">
        <div className="flex items-center gap-2">
          <FlaskConical
            size={16}
            strokeWidth={1.5}
            aria-hidden="true"
            className="shrink-0 text-status-attention-fg"
          />
          <h2 className="panel-title text-status-attention-fg">Demonstration states</h2>
        </div>
        <span className="badge badge-neutral">{scenarios.length} available</span>
      </div>

      <div className="panel-body">
        <p className="mb-4 max-w-prose text-sm text-secondary">
          Every outcome the result page handles, including the abstention and error
          states. Selecting one fills the address field above. All data is synthetic.
        </p>

        <ul className="grid grid-cols-1 gap-px overflow-hidden rounded-md border border-border bg-border sm:grid-cols-2">
          {scenarios.map((entry) => (
            <li key={entry.id}>
              <button
                type="button"
                onClick={() => onSelect(entry)}
                aria-pressed={selectedId === entry.id}
                className={cn(
                  'flex h-full w-full flex-col gap-1.5 px-4 py-3 text-left',
                  'transition-colors duration-fast hover:bg-accent-subtle',
                  selectedId === entry.id && 'bg-accent-subtle',
                )}
              >
                <span className="flex items-baseline justify-between gap-3">
                  <span className="text-sm font-medium text-primary">{entry.title}</span>
                  {selectedId === entry.id ? (
                    <span className="badge badge-info">Selected</span>
                  ) : null}
                </span>
                <span className="text-xs leading-relaxed text-secondary">
                  {entry.description}
                </span>
                <MonoText
                  value={entry.address}
                  copyLabel={`address for ${entry.title}`}
                  showCopy={false}
                  className="mt-1"
                />
              </button>
            </li>
          ))}
        </ul>

        <p className="mt-4 text-xs text-muted">{copy.home.demo.notice}</p>

        {onSimulateError ? (
          <div className="mt-4 border-t border-border-subtle pt-4">
            <p className="eyebrow mb-2">Simulate a service error on the next request</p>
            <div className="flex flex-wrap gap-2">
              {ERROR_SIMULATIONS.map((simulation) => (
                <button
                  key={simulation.kind}
                  type="button"
                  onClick={() => onSimulateError(simulation.kind)}
                  title={simulation.detail}
                  className="btn btn-secondary"
                >
                  {simulation.label}
                </button>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </section>
  )
}
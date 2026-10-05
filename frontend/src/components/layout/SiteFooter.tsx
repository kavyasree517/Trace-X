/**
 * Site footer.
 *
 * Carries the standing statement on every page rather than only on results,
 * because the sentence constrains how any output of this tool may be read and
 * that constraint should not depend on which route the reader landed on.
 */

import { copy } from '@/lib/copy'

export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-border bg-surface">
      <div className="mx-auto w-full max-w-content px-4 py-8 sm:px-6">
        <p className="eyebrow mb-2">{copy.app.name}</p>
        <p className="prose-block text-sm text-secondary">
          {copy.result.standingStatement}
        </p>
        <p className="mt-3 text-xs text-muted">
          Ethereum mainnet. All timestamps are UTC. Every finding carries an
          evidence tag describing how it was produced.
        </p>
      </div>
    </footer>
  )
}
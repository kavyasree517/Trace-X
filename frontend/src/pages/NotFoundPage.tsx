/**
 * Not found page.
 *
 * Reached for any unmatched path, including a mistyped case reference. Since a
 * case reference is the access token for a result, the likely cause of landing
 * here is a truncated link, so the page shows the expected format rather than a
 * bare error.
 */

import { Link, useLocation } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { copy } from '@/lib/copy'

export function NotFoundPage() {
  const location = useLocation()

  return (
    <AppShell>
      <div className="panel">
        <div className="panel-body max-w-prose space-y-4">
          <p className="eyebrow">Error 404</p>
          <h1
            tabIndex={-1}
            className="text-2xl font-semibold tracking-tight text-primary outline-none"
          >
            {copy.notFound.title}
          </h1>
          <p className="text-base leading-relaxed text-secondary">{copy.notFound.body}</p>

          <div className="rounded-md border border-border bg-surface-subtle px-3.5 py-3">
            <p className="text-xs font-medium text-muted">Requested path</p>
            <p className="mt-1 break-all font-mono text-sm text-primary">{location.pathname}</p>
          </div>

          <p className="text-sm text-secondary">{copy.notFound.referenceFormat}</p>

          <Link to="/" className="btn btn-primary">
            {copy.feedback.backHome}
          </Link>
        </div>
      </div>
    </AppShell>
  )
}
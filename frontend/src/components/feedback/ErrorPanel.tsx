/**
 * Error panel.
 *
 * Errors are typed by cause, not by message text, because the backend supplies a
 * machine readable code and every one of these codes needs different wording and
 * a different recovery affordance. A rate limit must state the retry interval; a
 * missing case is terminal and offering a retry would be misleading.
 */

import { AlertCircle, Clock, PlugZap, RefreshCw } from 'lucide-react'
import { ApiRequestError } from '@/lib/api'
import { copy } from '@/lib/copy'

interface ErrorPanelProps {
  error: ApiRequestError | Error
  onRetry?: () => void
  /** Rendered below the message, for example a link back to the form. */
  children?: React.ReactNode
}

interface Presentation {
  title: string
  detail: string
  tone: 'attention' | 'neutral'
  retryable: boolean
}

function present(error: ApiRequestError | Error): Presentation {
  const code = error instanceof ApiRequestError ? error.code : 'internal_error'

  switch (code) {
    case 'rate_limited':
      return {
        title: copy.feedback.rateLimited.title,
        detail: copy.feedback.rateLimited.detail,
        tone: 'attention',
        retryable: true,
      }
    case 'upstream_unavailable':
    case 'upstream_timeout':
      return {
        title: copy.feedback.upstreamUnavailable.title,
        detail: copy.feedback.upstreamUnavailable.detail,
        tone: 'attention',
        retryable: true,
      }
    case 'case_not_found':
      return {
        title: copy.feedback.notFound.title,
        detail: copy.feedback.notFound.detail,
        tone: 'neutral',
        retryable: false,
      }
    case 'network_unreachable':
      return {
        title: copy.feedback.offline.title,
        detail: copy.feedback.offline.detail,
        tone: 'neutral',
        retryable: true,
      }
    default:
      return {
        title: copy.feedback.failed.title,
        detail: error.message || copy.feedback.failed.detail,
        tone: 'attention',
        retryable: true,
      }
  }
}

export function ErrorPanel({ error, onRetry, children }: ErrorPanelProps) {
  const view = present(error)
  const retryAfter = error instanceof ApiRequestError ? error.retryAfterSeconds : undefined
  const requestId = error instanceof ApiRequestError ? error.requestId : undefined

  const Icon =
    error instanceof ApiRequestError && error.code === 'network_unreachable' ? PlugZap : AlertCircle

  return (
    <div
      role="alert"
      className={
        view.tone === 'attention'
          ? 'panel border-status-attention-border bg-status-attention-bg p-5'
          : 'panel p-5'
      }
    >
      <div className="flex items-start gap-3">
        <Icon
          size={18}
          strokeWidth={1.5}
          aria-hidden="true"
          className={
            view.tone === 'attention'
              ? 'mt-0.5 shrink-0 text-status-attention-fg'
              : 'mt-0.5 shrink-0 text-muted'
          }
        />
        <div className="min-w-0 flex-1">
          <h2 className="text-lg font-semibold text-primary">{view.title}</h2>
          <p
            className={
              view.tone === 'attention'
                ? 'mt-1.5 max-w-prose text-sm leading-relaxed text-status-attention-fg'
                : 'mt-1.5 max-w-prose text-sm leading-relaxed text-secondary'
            }
          >
            {view.detail}
          </p>

          {retryAfter !== undefined ? (
            <p className="mt-3 inline-flex items-center gap-1.5 rounded-sm border border-border bg-surface px-2 py-1 font-mono text-xs text-secondary">
              <Clock size={13} strokeWidth={1.5} aria-hidden="true" />
              {copy.feedback.rateLimited.retryAfter}: {retryAfter}s
            </p>
          ) : null}

          {requestId ? (
            <p className="mt-3 font-mono text-xs text-muted">request_id: {requestId}</p>
          ) : null}

          <div className="mt-4 flex flex-wrap items-center gap-2">
            {view.retryable && onRetry ? (
              <button type="button" onClick={onRetry} className="btn btn-secondary">
                <RefreshCw size={16} strokeWidth={1.5} aria-hidden="true" />
                {copy.feedback.retry}
              </button>
            ) : null}
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}
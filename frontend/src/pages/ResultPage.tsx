/**
 * Result page.
 *
 * Panel order is fixed by the specification and by reading order: what happened,
 * how confident we are, where the funds went, who received them, what patterns
 * were seen, what other reports share evidence, what is not covered, how to
 * export. A reader who stops after the first two panels still has the headline
 * and the caveats, which are the two things that must never be separated.
 *
 * Sections are numbered because a result is a document that gets cited. The
 * numbers are also the scroll anchors, so a link into section 7 survives a
 * reload.
 */

import { useCallback, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Download, RefreshCw } from 'lucide-react'
import { AppShell } from '@/components/layout/AppShell'
import { Panel } from '@/components/common/Panel'
import { CopyButton } from '@/components/common/CopyButton'
import { SummaryPanel } from '@/components/result/SummaryPanel'
import { ConfidencePanel } from '@/components/result/ConfidencePanel'
import { LimitationsPanel } from '@/components/result/LimitationsPanel'
import { PathList } from '@/components/evidence/PathList'
import { AttributionList } from '@/components/evidence/AttributionList'
import { SignalList } from '@/components/evidence/SignalList'
import { RelatedCaseList } from '@/components/evidence/RelatedCaseList'
import { ProgressStages } from '@/components/feedback/ProgressStages'
import { ErrorPanel } from '@/components/feedback/ErrorPanel'
import { PanelSkeleton } from '@/components/feedback/PartialDataNotice'
import { PartialDataNotice } from '@/components/feedback/PartialDataNotice'
import { useCase } from '@/lib/useCase'
import { ApiRequestError, getTransport } from '@/lib/api'
import { copy } from '@/lib/copy'

export function ResultPage() {
  const { caseReference } = useParams<{ caseReference: string }>()
  const state = useCase(caseReference)
  const [refreshing, setRefreshing] = useState(false)

  const handleRefresh = useCallback(async () => {
    if (!caseReference) return
    setRefreshing(true)
    try {
      const transport = await getTransport()
      await transport.refreshCase(caseReference)
      state.refresh()
    } catch {
      // The polling loop owns error display; a failed refresh is covered by the
      // next poll and does not need a second error surface here.
    } finally {
      setRefreshing(false)
    }
  }, [caseReference, state])

  const { summary } = state

  const actions = summary ? (
    <>
      <button
        type="button"
        onClick={() => void handleRefresh()}
        disabled={refreshing || state.isPolling}
        className="btn btn-secondary"
      >
        <RefreshCw
          size={16}
          strokeWidth={1.5}
          aria-hidden="true"
          className={refreshing ? 'animate-spin' : undefined}
        />
        <span className="hidden sm:inline">{copy.result.export.refresh}</span>
        <span className="sm:hidden">Refresh</span>
      </button>
      <a href={`/api/v1/cases/${caseReference}/report.pdf`} className="btn btn-secondary">
        <Download size={16} strokeWidth={1.5} aria-hidden="true" />
        <span className="hidden sm:inline">{copy.result.export.pdf}</span>
        <span className="sm:hidden">PDF</span>
      </a>
    </>
  ) : null

  if (state.error) {
    return (
      <AppShell>
        <div className="space-y-6">
          <PageHeading caseReference={caseReference} />
          <ErrorPanel error={state.error as ApiRequestError}>
            <Link to="/" className="btn btn-primary">
              {copy.feedback.backHome}
            </Link>
          </ErrorPanel>
        </div>
      </AppShell>
    )
  }

  if (state.isLoading && !summary) {
    return (
      <AppShell>
        <div className="space-y-panel">
          <PageHeading caseReference={caseReference} />
          <PanelSkeleton title={copy.feedback.stagesSkeleton} rows={6} />
        </div>
      </AppShell>
    )
  }

  if (!summary) {
    return (
      <AppShell>
        <ErrorPanel error={new ApiRequestError('internal_error', copy.feedback.empty.detail, 500)}>
          <Link to="/" className="btn btn-primary">
            {copy.feedback.backHome}
          </Link>
        </ErrorPanel>
      </AppShell>
    )
  }

  const isRunning = state.isPolling || summary.status === 'pending' || summary.status === 'running'
  const isFailed = summary.status === 'failed'
  const isPartial = summary.status === 'partial'
  const hasSubResourceFailures = Object.keys(state.partialErrors).length > 0

  return (
    <AppShell actions={actions}>
      <div className="space-y-panel">
        <PageHeading caseReference={summary.case_reference} chain={summary.chain} />

        {isRunning ? (
          <Panel
            index={1}
            title={copy.result.stages.title}
            headingId="stage-progress"
          >
            <ProgressStages stages={summary.stages} />
          </Panel>
        ) : null}

        {isFailed ? (
          <ErrorPanel error={new ApiRequestError('upstream_unavailable', copy.feedback.failed.detail, 502)} onRetry={() => void handleRefresh()}>
            <Link to="/" className="btn btn-secondary">
              {copy.feedback.backHome}
            </Link>
          </ErrorPanel>
        ) : null}

        <Panel
          index={isRunning ? undefined : 1}
          title="Summary"
          headingId="section-summary"
        >
          {isPartial ? <PartialDataNotice className="mb-5" /> : null}
          {hasSubResourceFailures ? (
            <div className="mb-5 rounded-md border border-border bg-surface-subtle px-3.5 py-3 text-sm text-secondary">
              Some evidence sections could not be loaded:{' '}
              {Object.entries(state.partialErrors)
                .map(([name, message]) => `${name}: ${message}`)
                .join('; ')}
            </div>
          ) : null}
          <SummaryPanel summary={summary} />
        </Panel>

        <Panel
          index={isRunning ? undefined : 2}
          title={copy.result.confidencePanel.title}
          headingId="section-confidence"
        >
          <ConfidencePanel panel={summary.confidence_panel} />
        </Panel>

        <Panel
          index={isRunning ? undefined : 3}
          title={copy.evidence.paths.title}
          lead={copy.evidence.paths.lead}
          headingId="section-paths"
        >
          {state.paths ? (
            <PathList paths={state.paths} />
          ) : (
            <PanelSkeletonTitle title={copy.evidence.paths.title} />
          )}
        </Panel>

        <Panel
          index={isRunning ? undefined : 4}
          title={copy.evidence.attribution.title}
          lead={copy.evidence.attribution.lead}
          headingId="section-attribution"
        >
          {state.attributions ? (
            <AttributionList attributions={state.attributions} />
          ) : (
            <PanelSkeletonTitle title={copy.evidence.attribution.title} />
          )}
        </Panel>

        <Panel
          index={isRunning ? undefined : 5}
          title={copy.evidence.signals.title}
          lead={copy.evidence.signals.lead}
          headingId="section-signals"
        >
          {state.signals ? (
            <SignalList signals={state.signals} />
          ) : (
            <PanelSkeletonTitle title={copy.evidence.signals.title} />
          )}
        </Panel>

        <Panel
          index={isRunning ? undefined : 6}
          title={copy.evidence.related.title}
          lead={copy.evidence.related.lead}
          headingId="section-related"
        >
          {state.corroboration ? (
            <RelatedCaseList corroboration={state.corroboration} />
          ) : (
            <PanelSkeletonTitle title={copy.evidence.related.title} />
          )}
        </Panel>

        <Panel
          index={isRunning ? undefined : 7}
          title={copy.evidence.limitations.title}
          lead={copy.evidence.limitations.lead}
          headingId="section-limitations"
        >
          <LimitationsPanel limitations={summary.limitations} />
        </Panel>

        <Panel index={isRunning ? undefined : 8} title={copy.result.export.title} headingId="section-export">
          <ExportSection caseReference={summary.case_reference} reportReady={state.paths !== null && !isRunning} />
        </Panel>
      </div>
    </AppShell>
  )
}

function PageHeading({
  caseReference,
  chain,
}: {
  caseReference?: string
  chain?: string
}) {
  return (
    <header>
      <p className="eyebrow mb-2">Case result</p>
      <div className="flex flex-wrap items-baseline gap-x-4 gap-y-2">
        <h1
          tabIndex={-1}
          className="font-mono text-2xl font-semibold tracking-tight text-primary outline-none"
        >
          {caseReference ?? copy.feedback.empty.title}
        </h1>
        {chain ? <span className="text-sm text-muted">{copy.result.chainLabel}: {chain}</span> : null}
        {caseReference ? (
          <span className="inline-flex items-center">
            <CopyButton value={caseReference} label={copy.result.caseLabel} />
          </span>
        ) : null}
      </div>
    </header>
  )
}

function ExportSection({
  caseReference,
  reportReady,
}: {
  caseReference: string
  reportReady: boolean
}) {
  const [copied, setCopied] = useState(false)

  return (
    <div className="space-y-4">
      <p className="max-w-prose text-sm text-secondary">
        The PDF report repeats these findings with full label provenance, the complete
        audit trail and the limitations block, and records the SHA-256 of the file it
        produced.
      </p>

      <div className="flex flex-wrap items-center gap-2">
        <a
          href={`/api/v1/cases/${caseReference}/report.pdf`}
          aria-disabled={!reportReady}
          className={
            reportReady
              ? 'btn btn-primary'
              : 'btn btn-primary pointer-events-none opacity-55'
          }
          onClick={(event) => {
            if (!reportReady) event.preventDefault()
          }}
        >
          <Download size={16} strokeWidth={1.5} aria-hidden="true" />
          {copy.result.export.pdf}
        </a>

        <button
          type="button"
          onClick={() => {
            void navigator.clipboard?.writeText(caseReference)
            setCopied(true)
            window.setTimeout(() => setCopied(false), 2000)
          }}
          className="btn btn-secondary"
        >
          {copied ? copy.result.export.copied : copy.result.export.copyRef}
        </button>

        <span role="status" aria-live="polite" className="sr-only">
          {copied ? copy.result.export.copied : ''}
        </span>
      </div>

      {!reportReady ? (
        <p className="text-sm text-muted">
          The report becomes available once the analysis completes.
        </p>
      ) : null}
    </div>
  )
}

function PanelSkeletonTitle({ title }: { title: string }) {
  return <PanelSkeleton title={title} rows={3} />
}
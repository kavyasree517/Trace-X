/**
 * Home page.
 *
 * Layout intent: the address field is the task, so it gets the visual weight and
 * sits in the first panel without scrolling. Everything that qualifies the tool
 * sits below it in a two column block that collapses to one on a narrow screen.
 * The wording on this page is the first thing a reporter reads, so it states what
 * the tool will and will not establish before asking for an address, not after.
 */

import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { CircleCheck, CircleSlash } from 'lucide-react'
import { AppShell } from '@/components/layout/AppShell'
import { FormField } from '@/components/form/FormField'
import { AddressInput } from '@/components/form/AddressInput'
import { OptionalDetails, type OptionalDetailsValues } from '@/components/form/OptionalDetails'
import { SubmitButton } from '@/components/form/SubmitButton'
import { ErrorPanel } from '@/components/feedback/ErrorPanel'
import {
  DemoScenarioPicker,
  type DemoScenarioEntry,
  type ErrorSimulationKind,
} from '@/components/form/DemoScenarioPicker'
import { useCreateCase } from '@/lib/useCase'
import {
  canonicalizeAddressInput,
  validateAddress,
  validateAmount,
  validateIncidentDate,
  validateTxHash,
} from '@/lib/validation'
import { ApiRequestError, usingMockData } from '@/lib/api'
import { copy } from '@/lib/copy'
import type { IncidentDatePrecision } from '@/lib/types'

const INITIAL_DETAILS: OptionalDetailsValues = {
  txHash: '',
  incidentDate: '',
  datePrecision: 'unknown',
  amount: '',
  asset: '',
}

/** Stable id so the scenario picker can move focus to the address field. */
const ADDRESS_FIELD_ID = 'reported-address'

export function HomePage() {
  const navigate = useNavigate()
  const { create, isSubmitting, error, reset } = useCreateCase()

  const [address, setAddress] = useState('')
  const [addressError, setAddressError] = useState<string | undefined>()
  const [details, setDetails] = useState<OptionalDetailsValues>(INITIAL_DETAILS)
  const [detailErrors, setDetailErrors] = useState<{
    txHash?: string
    incidentDate?: string
    amount?: string
  }>({})

  const [demoScenarios, setDemoScenarios] = useState<DemoScenarioEntry[]>([])
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | undefined>()

  // The demonstration dataset is split into its own chunk, so it is only fetched
  // when the mock flag is set. A production build never loads it.
  useEffect(() => {
    if (!usingMockData) return
    let cancelled = false
    void import('@/lib/api/mock').then((module) => {
      if (!cancelled) setDemoScenarios(module.demoScenarios)
    })
    return () => {
      cancelled = true
    }
  }, [])

  const handleScenarioSelect = (entry: DemoScenarioEntry) => {
    setAddress(entry.address)
    setAddressError(undefined)
    setSelectedScenarioId(entry.id)
    document.getElementById(ADDRESS_FIELD_ID)?.focus()
  }

  const handleSimulateError = (kind: ErrorSimulationKind) => {
    void import('@/lib/api/mock').then((module) => {
      if (kind === 'rate_limited') {
        module.failNext(
          'rate_limited',
          'Rate limit exceeded. Please try again later.',
          429,
          30,
        )
      } else {
        module.failNext(
          'upstream_unavailable',
          'The chain data source is not responding.',
          503,
        )
      }
    })
  }

  const updateDetail = (field: keyof OptionalDetailsValues, value: string) => {
    setDetails((current) => ({ ...current, [field]: value }))
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    reset()

    const addressResult = validateAddress(address)
    const addressMessage =
      addressResult.code === 'ok' ? undefined : addressErrorMessageFor(addressResult.code)
    setAddressError(addressMessage)

    const nextDetailErrors: typeof detailErrors = {}

    if (details.txHash.trim().length > 0) {
      const txResult = validateTxHash(details.txHash)
      if (txResult !== 'ok') nextDetailErrors.txHash = copy.home.form.errors.invalidTxHash
    }

    const dateResult = validateIncidentDate(details.incidentDate)
    if (dateResult === 'future') {
      nextDetailErrors.incidentDate = copy.home.form.errors.futureDate
    } else if (dateResult === 'invalid') {
      nextDetailErrors.incidentDate = copy.home.form.errors.invalidDate
    }

    const amountResult = validateAmount(details.amount)
    if (amountResult === 'invalid') {
      nextDetailErrors.amount = copy.home.form.errors.invalidAmount
    } else if (amountResult === 'negative') {
      nextDetailErrors.amount = copy.home.form.errors.negativeAmount
    }

    setDetailErrors(nextDetailErrors)

    if (addressMessage || Object.keys(nextDetailErrors).length > 0) {
      // Move focus to the first offending control so a keyboard or screen reader
      // user is not left at the bottom of the form wondering what happened.
      const firstInvalid = document.querySelector<HTMLElement>('[aria-invalid="true"]')
      firstInvalid?.focus()
      return
    }

    try {
      const created = await create({
        address: canonicalizeAddressInput(address),
        chain: 'ethereum',
        tx_hash: details.txHash.trim() || null,
        incident_date: details.incidentDate
          ? new Date(`${details.incidentDate}T00:00:00Z`).toISOString()
          : null,
        incident_date_precision: details.datePrecision as IncidentDatePrecision,
        reported_amount: details.amount.trim() || null,
        reported_asset: details.asset.trim() || null,
        consent_for_narrative_storage: false,
      })

      navigate(`/cases/${created.case_reference}`)
    } catch {
      // The error is rendered below; nothing further to do here.
    }
  }

  const requestError = error as ApiRequestError | null

  return (
    <AppShell>
      <div className="space-y-panel">
        <header className="max-w-prose">
          <p className="eyebrow mb-3">{copy.app.tagline}</p>
          <h1
            tabIndex={-1}
            className="text-3xl font-semibold leading-tight tracking-tight text-primary outline-none"
          >
            {copy.home.title}
          </h1>
          <p className="mt-4 text-base leading-relaxed text-secondary">
            {copy.home.subtitle}
          </p>
        </header>

        <form onSubmit={handleSubmit} noValidate className="panel">
          <div className="panel-body space-y-5">
            <FormField
              label={copy.home.form.addressLabel}
              hint={copy.home.form.addressHint}
              error={addressError}
              required
            >
              {(fieldProps) => (
                <AddressInput
                  id={ADDRESS_FIELD_ID}
                  aria-describedby={fieldProps['aria-describedby']}
                  value={address}
                  onChange={setAddress}
                  onValidate={setAddressError}
                  invalid={Boolean(addressError)}
                  disabled={isSubmitting}
                />
              )}
            </FormField>

            <FormField label={copy.home.form.chainLabel} hint={copy.home.form.chainScopeNote}>
              {(fieldProps) => (
                <select
                  id={fieldProps.id}
                  aria-describedby={fieldProps['aria-describedby']}
                  disabled
                  value="ethereum"
                  className="control sm:max-w-xs"
                >
                  <option value="ethereum">{copy.home.form.chainEthereum}</option>
                </select>
              )}
            </FormField>

            <OptionalDetails
              values={details}
              errors={detailErrors}
              onChange={updateDetail}
              disabled={isSubmitting}
            />

            {error ? (
              <ErrorPanel
                error={requestError ?? error}
                onRetry={() => {
                  reset()
                  setAddressError(undefined)
                  setDetailErrors({})
                }}
              />
            ) : null}

            <div className="flex flex-col gap-3 border-t border-border-subtle pt-5 sm:flex-row sm:items-center">
              <SubmitButton isSubmitting={isSubmitting} />
              <p className="text-sm text-muted">
                {copy.home.form.note}
              </p>
            </div>
          </div>
        </form>

        {usingMockData ? (
          <DemoScenarioPicker
            scenarios={demoScenarios}
            onSelect={handleScenarioSelect}
            selectedId={selectedScenarioId}
            onSimulateError={handleSimulateError}
          />
        ) : null}

        <div className="grid grid-cols-1 gap-panel lg:grid-cols-2">
          <ScopeCard
            tone="positive"
            title={copy.home.does.title}
            items={copy.home.does.items}
          />
          <ScopeCard
            tone="negative"
            title={copy.home.doesNot.title}
            items={copy.home.doesNot.items}
          />
        </div>
      </div>
    </AppShell>
  )
}

function addressErrorMessageFor(code: string): string {
  switch (code) {
    case 'required':
      return copy.home.form.errors.addressRequired
    case 'bad_checksum':
      return copy.home.form.errors.mixedCaseAddress
    default:
      return copy.home.form.errors.invalidAddress
  }
}

interface ScopeCardProps {
  title: string
  items: readonly string[]
  tone: 'positive' | 'negative'
}

/**
 * What the tool does and does not establish.
 *
 * The two cards are balanced deliberately: an interface that only lists
 * capabilities overstates them, and one that only lists limits undersells what
 * the trace actually produced. Neither card uses a tick or a cross icon as its
 * primary cue, because the heading already carries the distinction and colour
 * alone must never be the signal.
 */
function ScopeCard({ title, items, tone }: ScopeCardProps) {
  return (
    <section className="panel">
      <div className="panel-body">
        <div className="mb-4 flex items-center gap-2">
          {tone === 'positive' ? (
            <CircleCheck size={18} strokeWidth={1.5} aria-hidden="true" className="text-accent" />
          ) : (
            <CircleSlash size={18} strokeWidth={1.5} aria-hidden="true" className="text-muted" />
          )}
          <h2 className="panel-title">{title}</h2>
        </div>
        <ul className="space-y-2.5">
          {items.map((item) => (
            <li key={item} className="flex gap-3 text-sm leading-relaxed text-secondary">
              <span
                aria-hidden="true"
                className="mt-2 h-1 w-1 shrink-0 rounded-full bg-border-strong"
              />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
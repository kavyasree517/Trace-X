/**
 * Optional detail fields, collapsed by default.
 *
 * A disclosure rather than always-visible fields because each one is genuinely
 * optional and the primary task is the address alone. Native details is used so
 * keyboard operation and the expanded state need no JavaScript. The summary
 * states how many fields are inside, so a collapsed section is not mistaken for
 * an empty one.
 */

import type { IncidentDatePrecision } from '@/lib/types'
import { FormField } from './FormField'
import { copy } from '@/lib/copy'

export interface OptionalDetailsValues {
  txHash: string
  incidentDate: string
  datePrecision: IncidentDatePrecision
  amount: string
  asset: string
}

export interface OptionalDetailsErrors {
  txHash?: string
  incidentDate?: string
  amount?: string
}

interface OptionalDetailsProps {
  values: OptionalDetailsValues
  errors: OptionalDetailsErrors
  onChange: (field: keyof OptionalDetailsValues, value: string) => void
  disabled?: boolean
  defaultOpen?: boolean
}

const PRECISION_OPTIONS: Array<{ value: IncidentDatePrecision; label: string }> = [
  { value: 'unknown', label: 'Not stated' },
  { value: 'approximate', label: 'Approximate' },
  { value: 'day', label: 'Day only' },
  { value: 'exact', label: 'Exact' },
]

export function OptionalDetails({
  values,
  errors,
  onChange,
  disabled = false,
  defaultOpen = false,
}: OptionalDetailsProps) {
  return (
    <details
      open={defaultOpen}
      className="group rounded-md border border-border bg-surface-subtle"
    >
      <summary
        className="flex cursor-pointer list-none flex-col gap-0.5 px-4 py-3 text-sm transition-colors duration-fast hover:bg-surface [&::-webkit-details-marker]:hidden"
      >
        <span className="font-medium">{copy.home.form.additionalDetails}</span>
        <span className="text-sm font-normal text-muted">
          {copy.home.form.additionalDetailsHint}
        </span>
      </summary>

      <div className="space-y-5 border-t border-border-subtle px-4 py-4">
        <FormField
          label={copy.home.form.txHashLabel}
          hint={copy.home.form.txHashHint}
          error={errors.txHash}
        >
          {(fieldProps) => (
            <input
              {...fieldProps}
              type="text"
              inputMode="text"
              autoComplete="off"
              spellCheck={false}
              disabled={disabled}
              value={values.txHash}
              placeholder="0x"
              onChange={(event) => onChange('txHash', event.target.value)}
              className="control font-mono"
            />
          )}
        </FormField>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <FormField
            label={copy.home.form.incidentDateLabel}
            error={errors.incidentDate}
          >
            {(fieldProps) => (
              <input
                {...fieldProps}
                type="date"
                autoComplete="off"
                disabled={disabled}
                value={values.incidentDate}
                max={new Date().toISOString().slice(0, 10)}
                onChange={(event) => onChange('incidentDate', event.target.value)}
                className="control"
              />
            )}
          </FormField>

          <FormField label={copy.home.form.datePrecisionLabel}>
            {(fieldProps) => (
              <select
                {...fieldProps}
                disabled={disabled}
                value={values.datePrecision}
                onChange={(event) =>
                  onChange('datePrecision', event.target.value as IncidentDatePrecision)
                }
                className="control"
              >
                {PRECISION_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            )}
          </FormField>
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <FormField
            label={copy.home.form.reportedAmountLabel}
            hint={copy.home.form.reportedAmountHint}
            error={errors.amount}
          >
            {(fieldProps) => (
              <input
                {...fieldProps}
                type="text"
                inputMode="decimal"
                autoComplete="off"
                disabled={disabled}
                value={values.amount}
                placeholder="1.25"
                onChange={(event) => onChange('amount', event.target.value)}
                className="control font-mono"
              />
            )}
          </FormField>

          <FormField
            label={copy.home.form.reportedAssetLabel}
            hint={copy.home.form.reportedAssetHint}
          >
            {(fieldProps) => (
              <input
                {...fieldProps}
                type="text"
                autoComplete="off"
                spellCheck={false}
                disabled={disabled}
                value={values.asset}
                placeholder="ETH"
                onChange={(event) => onChange('asset', event.target.value)}
                className="control font-mono"
              />
            )}
          </FormField>
        </div>
      </div>
    </details>
  )
}
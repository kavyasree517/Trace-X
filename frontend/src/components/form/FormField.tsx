/**
 * Labelled form control.
 *
 * All accessibility wiring lives here so no field can ship without it: the label
 * is associated through `htmlFor`, the hint and error are referenced by
 * `aria-describedby`, and invalid state is exposed through `aria-invalid`
 * rather than through colour alone. Because the error message is referenced
 * before it exists, the id is reserved on mount and only populated when there is
 * something to say, which stops assistive technology announcing an empty string.
 */

import { useId, type ReactNode } from 'react'
import { AlertCircle } from 'lucide-react'
import { cn } from '@/lib/cn'

interface FormFieldProps {
  label: string
  children: (props: {
    id: string
    'aria-describedby': string | undefined
    'aria-invalid': boolean
  }) => ReactNode
  hint?: string
  error?: string
  className?: string
  /** Marks the control as required for assistive technology. */
  required?: boolean
}

export function FormField({
  label,
  children,
  hint,
  error,
  className,
  required = false,
}: FormFieldProps) {
  const fieldId = useId()
  const hintId = `${fieldId}-hint`
  const errorId = `${fieldId}-error`

  const describedBy =
    [hint ? hintId : null, error ? errorId : null].filter(Boolean).join(' ') || undefined

  return (
    <div className={cn('min-w-0', className)}>
      <label htmlFor={fieldId} className="field-label">
        {label}
        {required ? (
          <>
            <span aria-hidden="true" className="ml-1 text-status-attention-fg">
              *
            </span>
            <span className="sr-only"> (required)</span>
          </>
        ) : null}
      </label>

      {children({
        id: fieldId,
        'aria-describedby': describedBy,
        'aria-invalid': Boolean(error),
      })}

      {hint ? (
        <p id={hintId} className="field-hint">
          {hint}
        </p>
      ) : null}

      {error ? (
        <p id={errorId} className="field-error">
          <AlertCircle size={14} strokeWidth={1.5} aria-hidden="true" className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </p>
      ) : null}
    </div>
  )
}
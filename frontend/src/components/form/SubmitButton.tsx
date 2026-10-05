/**
 * Submit control.
 *
 * The label changes while a request is in flight and the control is disabled and
 * marked busy, so a slow retrieval never looks like a failed click. `aria-busy`
 * plus a live region is what carries the progress to a screen reader; the spinner
 * is decorative and hidden.
 */

import { Loader } from 'lucide-react'
import { copy } from '@/lib/copy'
import { cn } from '@/lib/cn'

interface SubmitButtonProps {
  isSubmitting: boolean
  disabled?: boolean
  className?: string
}

export function SubmitButton({ isSubmitting, disabled = false, className }: SubmitButtonProps) {
  const isDisabled = disabled || isSubmitting

  return (
    <>
      <button
        type="submit"
        disabled={isDisabled}
        aria-busy={isSubmitting}
        className={cn('btn btn-primary w-full sm:w-auto sm:min-w-[13rem]', className)}
      >
        {isSubmitting ? (
          <Loader size={16} strokeWidth={1.5} aria-hidden="true" className="animate-spin" />
        ) : null}
        {isSubmitting ? copy.home.form.submitting : copy.home.form.submit}
      </button>

      <span role="status" aria-live="polite" className="sr-only">
        {isSubmitting ? copy.home.form.submittingHint : ''}
      </span>
    </>
  )
}
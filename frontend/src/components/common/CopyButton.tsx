/**
 * Icon-only copy control.
 *
 * The icon is decorative and the accessible name comes from the label, so the
 * button announces "Copy transaction hash" rather than nothing. Confirmation is
 * a text swap, not a colour flash or icon animation, and the change is announced
 * through a polite live region.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { Check, Copy } from 'lucide-react'
import { copy } from '@/lib/copy'
import { cn } from '@/lib/cn'

interface CopyButtonProps {
  value: string
  /** Accessible name. Describes what is copied, not the control itself. */
  label: string
  className?: string
}

export function CopyButton({ value, label, className }: CopyButtonProps) {
  const [state, setState] = useState<'idle' | 'copied' | 'failed'>('idle')
  const timer = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => () => clearTimeout(timer.current), [])

  const handleCopy = useCallback(async () => {
    clearTimeout(timer.current)
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(value)
      } else {
        // Fallback for browsers without the async clipboard API, and for
        // insecure origins where it is unavailable.
        const field = document.createElement('textarea')
        field.value = value
        field.setAttribute('readonly', '')
        field.style.position = 'fixed'
        field.style.opacity = '0'
        document.body.appendChild(field)
        field.select()
        const copied = document.execCommand('copy')
        document.body.removeChild(field)
        if (!copied) throw new Error('Copy command rejected')
      }
      setState('copied')
    } catch {
      setState('failed')
    }
    timer.current = setTimeout(() => setState('idle'), 2000)
  }, [value])

  const Icon = state === 'copied' ? Check : Copy

  return (
    <>
      <button
        type="button"
        onClick={() => void handleCopy()}
        className={cn(
          'inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-sm',
          'text-muted transition-colors duration-fast hover:bg-surface-subtle hover:text-accent',
          className,
        )}
        aria-label={state === 'copied' ? `${copy.common.copied}: ${label}` : `${copy.common.copy}: ${label}`}
      >
        <Icon size={16} strokeWidth={1.5} aria-hidden="true" />
      </button>
      <span role="status" aria-live="polite" className="sr-only">
        {state === 'copied'
          ? `${copy.common.copied}: ${label}`
          : state === 'failed'
            ? copy.common.copyFailed
            : ''}
      </span>
    </>
  )
}
/**
 * UTC timestamp with an optional local-time reading.
 *
 * Chain evidence is recorded in UTC and the local reading is opt-in, because an
 * investigator comparing a block time against an incident report needs one
 * unambiguous reference. The two readings are both exposed to assistive
 * technology so the switch is not visual-only.
 */

import { useId, useState } from 'react'
import { formatTimestamp, formatTimestampLocal } from '@/lib/format'
import { copy } from '@/lib/copy'
import { cn } from '@/lib/cn'

interface TimestampProps {
  value: string | null | undefined
  /** Adds the local-time toggle. Leave off in dense tables. */
  showToggle?: boolean
  className?: string
}

export function Timestamp({ value, showToggle = false, className }: TimestampProps) {
  const [showLocal, setShowLocal] = useState(false)
  const regionId = useId()

  const utc = formatTimestamp(value)
  const local = formatTimestampLocal(value)

  if (!value) {
    return <span className={cn('text-muted', className)}>{copy.common.notRecorded}</span>
  }

  return (
    <span className={cn('inline-flex flex-wrap items-baseline gap-x-2 gap-y-0.5', className)}>
      <time dateTime={value} id={regionId} className="text-sm text-secondary">
        {showLocal ? local : utc}
      </time>

      {showToggle ? (
        <button
          type="button"
          onClick={() => setShowLocal((current) => !current)}
          className="rounded-sm text-xs text-accent underline decoration-accent-border underline-offset-2 transition-colors duration-fast hover:text-accent-hover"
          aria-pressed={showLocal}
          aria-describedby={regionId}
        >
          {showLocal ? copy.common.hideLocalTime : copy.common.showLocalTime}
        </button>
      ) : null}
    </span>
  )
}
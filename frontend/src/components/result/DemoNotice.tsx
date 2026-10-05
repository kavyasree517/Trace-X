/**
 * Demonstration mode notice.
 *
 * Shown whenever a result is marked demo, and stated as a property of the data
 * rather than as an apology. It is a `role="note"` so it is discoverable in the
 * accessibility tree without interrupting a screen reader mid-sentence.
 */

import { FlaskConical } from 'lucide-react'
import { copy } from '@/lib/copy'
import { cn } from '@/lib/cn'

interface DemoNoticeProps {
  text?: string
  className?: string
}

export function DemoNotice({ text, className }: DemoNoticeProps) {
  return (
    <div
      role="note"
      className={cn(
        'flex items-start gap-2.5 rounded-md border border-status-attention-border',
        'bg-status-attention-bg px-3.5 py-3',
        className,
      )}
    >
      <FlaskConical
        size={16}
        strokeWidth={1.5}
        aria-hidden="true"
        className="mt-0.5 shrink-0 text-status-attention-fg"
      />
      <p className="text-sm leading-normal text-status-attention-fg">
        {text ?? copy.result.demoNotice}
      </p>
    </div>
  )
}
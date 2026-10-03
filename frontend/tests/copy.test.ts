import { describe, it, expect } from 'vitest'
import { copy } from '../src/lib/copy'

describe('copy deck', () => {
  it('contains required headline states', () => {
    expect(copy.result.statusBadge.verified).toBe('Verified label match')
    expect(copy.result.statusBadge.potential).toBe('Potential association')
    expect(copy.result.statusBadge.noMatch).toBe('No match found in current references')
    expect(copy.result.statusBadge.insufficientData).toBe('Insufficient data')
  })

  it('has mandatory signal note', () => {
    expect(copy.evidence.signals.note).toContain('legitimate activity')
  })

  it('has standing statement', () => {
    expect(copy.result.standingStatement).toContain('investigative lead')
  })
})

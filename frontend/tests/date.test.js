/**
 * Tests for date/ISO-week helpers (src/lib/date.js).
 *
 * dateToWeekLabel drives which "week" the whole app operates on, and the ISO
 * week math is easy to get wrong at year boundaries — so we lock in a few
 * known cases (incl. 2027-01-01 belonging to 2026-W53) to catch regressions.
 */
import { describe, it, expect } from 'vitest'
import { todayIso, dateToWeekLabel, formatDateTime } from '../src/lib/date'

describe('todayIso', () => {
  it('returns a YYYY-MM-DD string', () => {
    expect(todayIso()).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })
})

describe('dateToWeekLabel', () => {
  it('computes ISO week labels', () => {
    // 2026-06-08 is a Monday in ISO week 24.
    expect(dateToWeekLabel('2026-06-08')).toBe('2026-W24')
  })

  it('pads single-digit weeks to two digits', () => {
    expect(dateToWeekLabel('2026-01-05')).toBe('2026-W02')
  })

  it('handles the year-boundary edge case', () => {
    // 2027-01-01 (Friday) belongs to ISO week 53 of 2026.
    expect(dateToWeekLabel('2027-01-01')).toBe('2026-W53')
  })
})

describe('formatDateTime', () => {
  it('returns an em dash for empty input', () => {
    expect(formatDateTime(null)).toBe('—')
    expect(formatDateTime(undefined)).toBe('—')
    expect(formatDateTime('')).toBe('—')
  })

  it('formats a timestamp into a non-empty string', () => {
    const out = formatDateTime('2026-06-08T14:30:00Z')
    expect(typeof out).toBe('string')
    expect(out).not.toBe('—')
  })
})

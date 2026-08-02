import { describe, it, expect } from 'vitest'
import { buildWeekSummary, findConflict } from '../src/lib/weekSummary'
import { DIRECTIONS } from '../src/lib/bias'

describe('findConflict', () => {
  it('returns null when directions do not oppose', () => {
    expect(
      findConflict([
        { id: 'a', label: 'Almanac', text: 'Bullish', tone: DIRECTIONS.BULLISH },
        { id: 'm', label: 'Macro', text: 'Mixed', tone: DIRECTIONS.NEUTRAL },
      ]),
    ).toBeNull()
  })

  it('names bullish vs bearish sources', () => {
    const conflict = findConflict([
      { id: 'macro', label: 'Macro', text: 'Bearish', tone: DIRECTIONS.BEARISH },
      { id: 'technical', label: 'Technical', text: 'Bullish', tone: DIRECTIONS.BULLISH },
    ])
    expect(conflict).toContain('Technical Bullish')
    expect(conflict).toContain('Macro Bearish')
    expect(conflict).toContain(' vs ')
  })
})

describe('buildWeekSummary', () => {
  it('pulls agent, LLM, and final biases', () => {
    const summary = buildWeekSummary({
      outputs: {
        almanac: {
          agent: 'Almanac',
          rawData: 'ALMANAC SEASONAL BIAS: Bullish.\nPATTERN CONFIDENCE: HIGH.',
          metrics: [],
        },
        macro: {
          agent: 'Macro',
          rawData: 'MACRO BIAS: Bearish.\nCONFIDENCE: Medium.',
          metrics: [],
        },
        llmComparison: { finalConsensus: 'Neutral' },
      },
      finalPrediction: { form: { regime: 'Bullish' } },
    })
    expect(summary.signals.map(s => s.id)).toEqual(['almanac', 'macro', 'llm', 'final'])
    expect(summary.conflict).toMatch(/Almanac|Final/)
    expect(summary.conflict).toMatch(/Macro/)
  })

  it('returns empty when nothing is loaded', () => {
    expect(buildWeekSummary({}).hasSignals).toBe(false)
  })
})

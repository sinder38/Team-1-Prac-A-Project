/**
 * Tests for market-direction classification (src/lib/bias.js).
 *
 * This is the logic that used to be fragile inline string-matching inside
 * components. It reduces free-form agent/LLM text (e.g. "Neutral-Bearish") to
 * bullish / bearish / neutral. We test the tricky cases: mixed text, empty /
 * null input, and counting how many models agree with the consensus.
 */
import { describe, it, expect } from 'vitest'
import {
  classifyBias,
  directionLabel,
  summarizeModelAgreement,
  DIRECTIONS,
} from '../src/lib/bias'

describe('classifyBias', () => {
  it('detects bullish text', () => {
    expect(classifyBias('Bullish')).toBe(DIRECTIONS.BULLISH)
    expect(classifyBias('strongly BULLISH into Q4')).toBe(DIRECTIONS.BULLISH)
  })

  it('detects bearish text', () => {
    expect(classifyBias('Bearish')).toBe(DIRECTIONS.BEARISH)
    expect(classifyBias('Neutral-Bearish')).toBe(DIRECTIONS.BEARISH)
  })

  it('returns neutral when neither or both appear', () => {
    expect(classifyBias('Neutral')).toBe(DIRECTIONS.NEUTRAL)
    expect(classifyBias('bullish then bearish')).toBe(DIRECTIONS.NEUTRAL)
  })

  it('handles empty / nullish input without throwing', () => {
    expect(classifyBias('')).toBe(DIRECTIONS.NEUTRAL)
    expect(classifyBias(null)).toBe(DIRECTIONS.NEUTRAL)
    expect(classifyBias(undefined)).toBe(DIRECTIONS.NEUTRAL)
  })
})

describe('directionLabel', () => {
  it('maps directions to labels', () => {
    expect(directionLabel(DIRECTIONS.BULLISH)).toBe('Bullish')
    expect(directionLabel(DIRECTIONS.BEARISH)).toBe('Bearish')
    expect(directionLabel(DIRECTIONS.NEUTRAL)).toBe('Mixed')
  })
})

describe('summarizeModelAgreement', () => {
  it('counts models matching the consensus direction', () => {
    const llm = {
      finalConsensus: 'Neutral-Bearish',
      models: [
        { consensus: 'Bearish' },
        { consensus: 'Neutral-Bearish' },
        { consensus: 'Bullish' },
        { consensus: 'Neutral' },
      ],
    }
    expect(summarizeModelAgreement(llm)).toBe('2 of 4 models bearish')
  })

  it('returns an em dash when there are no models', () => {
    expect(summarizeModelAgreement({ models: [] })).toBe('—')
    expect(summarizeModelAgreement(null)).toBe('—')
    expect(summarizeModelAgreement(undefined)).toBe('—')
  })
})

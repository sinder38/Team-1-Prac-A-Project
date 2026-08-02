/**
 * Tests for agent-card preparation (src/lib/agentDisplay.js).
 */
import { describe, it, expect } from 'vitest'
import { prepareAgentCard, biasBadgeClass, tokenizeHighlight } from '../src/lib/agentDisplay'
import { DIRECTIONS } from '../src/lib/bias'

describe('prepareAgentCard', () => {
  it('returns null when there is no data', () => {
    expect(prepareAgentCard('macro', null)).toBeNull()
  })

  it('parses bias and confidence out of raw text', () => {
    const card = prepareAgentCard('technical', {
      agent: 'Technical Agent',
      rawData: 'TECHNICAL BIAS: Bullish.\nCONFIDENCE: Medium.',
      metrics: [
        { label: 'Last Close', value: '7,554' },
        { label: 'EMA Condition', value: 'Zone 1 (Bullish)' },
      ],
    })
    expect(card.name).toBe('Technical Agent')
    expect(card.bias).toBe('Bullish')
    expect(card.biasTone).toBe(DIRECTIONS.BULLISH)
    expect(card.confidence).toBe('Medium')
    expect(card.headline.label).toBe('Last Close')
    expect(card.details).toHaveLength(1)
  })

  it('drops empty metrics and keeps up to ten', () => {
    const card = prepareAgentCard('macro', {
      agent: 'Macro Agent',
      rawData: '',
      metrics: [
        { label: 'A', value: '1' },
        { label: 'B', value: '' },
        { label: 'C', value: '3' },
        { label: 'D', value: '4' },
        { label: 'E', value: '5' },
        { label: 'F', value: '6' },
        { label: 'G', value: '7' },
      ],
    })
    // 'B' dropped (empty); six remain → headline + 5 details.
    expect(card.headline.label).toBe('A')
    expect(card.details).toHaveLength(5)
    expect(card.bias).toBeNull()
    expect(card.biasTone).toBe(DIRECTIONS.NEUTRAL)
  })
})

describe('tokenizeHighlight', () => {
  it('tags percentages and bias words only', () => {
    const tokens = tokenizeHighlight('SPX +1.2% Bullish Medium')
    const kinds = tokens.map(t => t.kind)
    expect(kinds).toContain('pct')
    expect(kinds).toContain('bias')
    expect(kinds).not.toContain('ticker')
    expect(kinds).not.toContain('conf')
    expect(tokens.find(t => t.kind === 'pct')?.text).toBe('+1.2%')
    expect(tokens.some(t => t.kind === 'text' && t.text.includes('SPX'))).toBe(true)
    expect(tokens.some(t => t.kind === 'text' && t.text.includes('Medium'))).toBe(true)
  })

  it('returns empty for blank input', () => {
    expect(tokenizeHighlight('')).toEqual([])
    expect(tokenizeHighlight(null)).toEqual([])
  })
})

describe('biasBadgeClass', () => {
  it('returns distinct classes per direction', () => {
    expect(biasBadgeClass(DIRECTIONS.BULLISH)).toContain('emerald')
    expect(biasBadgeClass(DIRECTIONS.BEARISH)).toContain('red')
    expect(biasBadgeClass(DIRECTIONS.NEUTRAL)).toContain('amber')
  })
})

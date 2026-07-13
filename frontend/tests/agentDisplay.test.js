/**
 * Tests for agent-card preparation (src/lib/agentDisplay.js).
 *
 * prepareAgentCard turns a raw agent API payload into the trimmed content the
 * card renders: parsed bias + confidence, a headline metric, and a capped list
 * of detail metrics. We verify parsing, the empty/no-data guard, and that empty
 * metrics are dropped and the list is capped.
 */
import { describe, it, expect } from 'vitest'
import { prepareAgentCard, biasBadgeClass } from '../src/lib/agentDisplay'
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

  it('drops empty metrics and caps the list', () => {
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
      ],
    })
    // 'B' dropped (empty), list capped at 4 → headline + 3 details.
    expect(card.details.length).toBeLessThanOrEqual(3)
    expect(card.bias).toBeNull()
    expect(card.biasTone).toBe(DIRECTIONS.NEUTRAL)
  })
})

describe('biasBadgeClass', () => {
  it('returns distinct classes per direction', () => {
    expect(biasBadgeClass(DIRECTIONS.BULLISH)).toContain('emerald')
    expect(biasBadgeClass(DIRECTIONS.BEARISH)).toContain('red')
    expect(biasBadgeClass(DIRECTIONS.NEUTRAL)).toContain('amber')
  })
})

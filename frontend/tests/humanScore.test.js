/**
 * Tests for Human Score report logic (src/lib/humanScore.js).
 *
 * This logic was moved out of the ReviewForm component so it can be tested:
 *  - aiSaidFor: the "AI said" summary per dimension (derived from agent output).
 *  - humanScoreTotal: sum of the five team scores, safe against missing fields.
 *  - buildHumanScoreMarkdown: the copy-as-Markdown export (W28 format).
 */
import { describe, it, expect } from 'vitest'
import {
  aiSaidFor,
  buildHumanScoreMarkdown,
  buildHumanScoreReport,
  formatConsensusHeading,
  humanScoreTotal,
  weekTitleLabel,
} from '../src/lib/humanScore'
import { exampleAgentOutputs, exampleHumanScoreFormForWeek } from '../src/lib/exampleData'
import { defaultReviewForm } from '../src/lib/defaults'

describe('aiSaidFor', () => {
  it('derives per-dimension bias from agent outputs', () => {
    const said = aiSaidFor(exampleAgentOutputs('2026-W24'))
    expect(said.almanac).toBe('Bearish')
    expect(said.technical).toBe('Bullish')
    expect(said.aiAgreement).toBe('3 of 4 models bearish')
    expect(said.wildCard).toBe('nothing specifically flagged')
  })

  it('falls back to em dashes with empty outputs', () => {
    const said = aiSaidFor({})
    expect(said.macro).toBe('—')
    expect(said.aiAgreement).toBe('—')
  })
})

describe('humanScoreTotal', () => {
  it('sums the five dimension scores', () => {
    const form = {
      scores: { macro: 2, technical: 1, almanac: -1, aiAgreement: 0, wildCard: 2 },
    }
    expect(humanScoreTotal(form)).toBe(4)
  })

  it('defaults missing scores to zero', () => {
    expect(humanScoreTotal(defaultReviewForm)).toBe(0)
    expect(humanScoreTotal({})).toBe(0)
    expect(humanScoreTotal(undefined)).toBe(0)
  })
})

describe('buildHumanScoreReport', () => {
  it('bundles form, week context, and derived fields', () => {
    const outputs = exampleAgentOutputs('2026-W24')
    const form = exampleHumanScoreFormForWeek('2026-W24')
    const report = buildHumanScoreReport(form, {
      week: '2026-W24',
      outputs,
      predictionDate: '2026-06-08',
    })
    expect(report.week).toBe('2026-W24')
    expect(report.predictionDate).toBe('2026-06-08')
    expect(report.total).toBe(2)
    expect(report.consensus).toBe(outputs.llmComparison.finalConsensus)
    expect(report.aiSaid.almanac).toBe('Bearish')
    expect(report.llmComparison).toBe(outputs.llmComparison)
  })

  it('returns null without a form', () => {
    expect(buildHumanScoreReport(null, { week: '2026-W24', outputs: {} })).toBeNull()
  })
})

describe('exampleHumanScoreFormForWeek', () => {
  it('relabels W24 copy for other example weeks', () => {
    const form = exampleHumanScoreFormForWeek('2026-W22')
    expect(form.overrideParagraph).toContain('Week 22')
    expect(form.overrideParagraph).not.toContain('Week 24')
  })
})

describe('weekTitleLabel', () => {
  it('formats ISO week labels as Week N', () => {
    expect(weekTitleLabel('2026-W28')).toBe('Week 28')
    expect(weekTitleLabel('W28')).toBe('Week 28')
  })
})

describe('formatConsensusHeading', () => {
  it('adds model agreement counts when available', () => {
    const llm = {
      finalConsensus: 'Neutral-Bullish',
      models: [
        { consensus: 'Neutral-Bullish' },
        { consensus: 'Neutral-Bullish' },
        { consensus: 'Neutral' },
      ],
    }
    expect(formatConsensusHeading('Neutral-Bullish', llm)).toBe(
      '**Neutral-Bullish (2 of 3 models)**',
    )
  })
})

describe('buildHumanScoreMarkdown', () => {
  it('renders the W28 analyst-output structure', () => {
    const md = buildHumanScoreMarkdown(defaultReviewForm, {
      week: '2026-W24',
      consensus: 'Neutral-Bearish',
      aiSaid: { macro: 'Binary-risk' },
      total: 3,
    })
    expect(md).toContain('# Human Score Analyst Output — Week 24')
    expect(md).toContain('**Neutral-Bearish**')
    expect(md).toContain('**+3**')
    expect(md).toContain('## Five-Dimension Judgement')
    expect(md).toContain('### 1. Macro / News Weight — Score: 0')
    expect(md).toContain('| **Macro / News Weight** |')
    expect(md).toContain('(Macro 0 + Technical 0 + Almanac 0 + AI Agreement 0 + Wild Card 0)')
    expect(md).toContain('* R3 Almanac Agent Output')
  })

  it('shows negative totals with a leading minus', () => {
    const md = buildHumanScoreMarkdown(defaultReviewForm, { total: -2 })
    expect(md).toContain('**-2**')
  })
})

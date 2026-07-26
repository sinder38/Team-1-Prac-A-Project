/**
 * Final prediction markdown must stay parseable by the delta engine table reader.
 */
import { describe, it, expect } from 'vitest'
import { defaultFinalPredictionForm } from '../src/lib/defaults'
import {
  buildFinalPredictionMarkdown,
  buildFinalPredictionReport,
  formatAssetRange,
  formatFiledDate,
  isFinalPredictionComplete,
} from '../src/lib/finalPrediction'

describe('formatFiledDate', () => {
  it('formats like the Team1 brief header', () => {
    expect(formatFiledDate('2026-07-17')).toBe('17 JUL 2026')
  })
})

describe('formatAssetRange', () => {
  it('formats percent moves with signs', () => {
    expect(formatAssetRange('spx', { rangeLow: -2.5, rangeHigh: 0.5 })).toBe('-2.5% to +0.5%')
  })

  it('formats yield levels without signs', () => {
    expect(formatAssetRange('yield10y', { rangeLow: 4.5, rangeHigh: 4.75 })).toBe(
      '4.50% to 4.75%',
    )
  })

  it('formats VIX as a level band', () => {
    expect(formatAssetRange('vix', { rangeLow: 17, rangeHigh: 28 })).toBe('17–28 range')
  })
})

describe('buildFinalPredictionMarkdown', () => {
  it('includes regime, asset table headers, and section titles from W29 brief', () => {
    const form = {
      ...defaultFinalPredictionForm,
      regime: 'Bearish with medium uncertainty.',
      assets: {
        ...defaultFinalPredictionForm.assets,
        spx: {
          direction: 'FLAT-DOWN',
          rangeLow: -2.5,
          rangeHigh: 0.5,
          confidence: 'MEDIUM',
        },
        ndx: { direction: 'DOWN', rangeLow: -4, rangeHigh: 0, confidence: 'MEDIUM' },
        iwm: {
          direction: 'FLAT-DOWN',
          rangeLow: -2,
          rangeHigh: 0.8,
          confidence: 'LOW-MEDIUM',
        },
      },
      leadingSector: '**Energy (XLE)** — relative strength.',
      laggingSector: '**Technology (XLK)** — worst sector print.',
      evidence1: 'NDX below 8 and 21 EMA.',
      evidence2: 'Hawkish Fed backdrop.',
      evidence3: 'Three of four models Bearish.',
      contradiction: 'Setup looks stretched.',
      wildCard: 'Relief bounce risk.',
      invalidation: 'Our Bearish thesis is wrong if NDX reclaims EMAs.',
    }

    const md = buildFinalPredictionMarkdown(form, {
      week: '2026-W29',
      filedDate: '2026-07-17',
    })

    expect(md).toContain('# TEAM 1 2026-W29 CONSENSUS BRIEF — FILED: 17 JUL 2026')
    expect(md).toContain('## REGIME')
    expect(md).toContain('| Asset')
    expect(md).toContain('S&P 500 (SPX)')
    expect(md).toContain('**FLAT-DOWN**')
    expect(md).toContain('-2.5% to +0.5%')
    expect(md).toContain('## LEADING SECTOR')
    expect(md).toContain('## LAGGING SECTOR')
    expect(md).toContain('## KEY EVIDENCE (3 points)')
    expect(md).toContain('## KEY CONTRADICTION')
    expect(md).toContain('## HUMAN OVERRIDE / WILD CARD')
    expect(md).toContain('## INVALIDATION CONDITIONS')
  })
})

describe('buildFinalPredictionReport', () => {
  it('bundles form with markdown', () => {
    const report = buildFinalPredictionReport(defaultFinalPredictionForm, {
      week: '2026-W30',
      predictionDate: '2026-07-20',
      runId: 'run-abc',
    })
    expect(report.week).toBe('2026-W30')
    expect(report.runId).toBe('run-abc')
    expect(report.markdown).toContain('2026-W30')
  })
})

describe('isFinalPredictionComplete', () => {
  it('requires regime and equity ranges', () => {
    expect(isFinalPredictionComplete(defaultFinalPredictionForm)).toBe(false)
    const form = {
      ...defaultFinalPredictionForm,
      regime: 'Bearish',
      assets: {
        ...defaultFinalPredictionForm.assets,
        spx: { direction: 'DOWN', rangeLow: -2, rangeHigh: 0.5, confidence: 'MEDIUM' },
        ndx: { direction: 'DOWN', rangeLow: -3, rangeHigh: 0, confidence: 'MEDIUM' },
        iwm: { direction: 'FLAT', rangeLow: -1, rangeHigh: 0.5, confidence: 'MEDIUM' },
      },
    }
    expect(isFinalPredictionComplete(form)).toBe(true)
  })
})

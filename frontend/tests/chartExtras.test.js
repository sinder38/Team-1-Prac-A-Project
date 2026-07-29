import { describe, it, expect } from 'vitest'
import {
  macroContext,
  parsePctRange,
  periodChangePct,
  predictedRangeForSymbol,
  rangeHit,
  rebaseCloses,
  technicalContext,
} from '../src/lib/chartExtras'

describe('chartExtras', () => {
  it('rebases closes to 100', () => {
    const series = rebaseCloses([
      { time: '2026-01-01', close: 100 },
      { time: '2026-01-02', close: 110 },
    ])
    expect(series[0].value).toBe(100)
    expect(series[1].value).toBe(110)
  })

  it('computes period change pct', () => {
    expect(periodChangePct([
      { close: 100 },
      { close: 105 },
    ])).toBe(5)
  })

  it('parses percent ranges', () => {
    expect(parsePctRange('-1.5% to 2%')).toEqual({ low: -1.5, high: 2 })
    expect(parsePctRange({ low: '-1', high: '1.5' })).toEqual({ low: -1, high: 1.5 })
    expect(parsePctRange({ low: '', high: '' })).toBeNull()
  })

  it('reads predicted range from final prediction only', () => {
    const pred = predictedRangeForSymbol('SPX', {
      finalPrediction: {
        form: { assets: { spx: { direction: 'DOWN', rangeLow: '-2', rangeHigh: '0.5' } } },
      },
    })
    expect(pred).toMatchObject({ low: -2, high: 0.5, direction: 'DOWN', source: 'Final Prediction' })
  })

  it('falls back to range text when rangeLow/High are empty', () => {
    const pred = predictedRangeForSymbol('SPX', {
      finalPrediction: {
        form: {
          assets: {
            spx: { direction: 'FLAT-DOWN', rangeLow: '', rangeHigh: '', range: '-2.5% to +0.5%' },
          },
        },
      },
    })
    expect(pred).toMatchObject({ low: -2.5, high: 0.5, source: 'Final Prediction' })
  })

  it('does not invent an LLM envelope when Final Prediction is missing', () => {
    expect(predictedRangeForSymbol('SPX', {
      llmComparison: { models: [{ spx: '-1% to 2%' }], finalConsensus: 'Bearish' },
    })).toBeNull()
  })

  it('checks range hit against weekly actual', () => {
    expect(rangeHit({ low: -2.5, high: 0.5 }, -1.55)).toBe(true)
    expect(rangeHit({ low: -2.5, high: 0.5 }, -3)).toBe(false)
  })

  it('reads technical context from instruments', () => {
    const ctx = technicalContext({
      instruments: { SPX: { last_close: 7500, trend_bias: 'Bullish', key_support: 7400, key_resistance: 7600 } },
    }, 'SPX')
    expect(ctx).toMatchObject({ lastClose: 7500, bias: 'Bullish', support: 7400, resistance: 7600 })
  })

  it('does not let technical bias regex eat the next section', () => {
    const ctx = technicalContext({
      rawData: [
        'INSTRUMENT: S&P 500 (SPX)',
        'LAST CLOSE: 7458.0',
        'TECHNICAL BIAS: Neutral',
        '',
        'PRIMARY DRIVER: something else',
        'Support 1: 7400',
        'Resistance 1: 7600',
      ].join('\n'),
    }, 'SPX')
    expect(ctx.bias).toBe('Neutral')
  })

  it('returns null technical context when symbol block is missing', () => {
    expect(technicalContext({
      metrics: [{ label: 'Technical Bias', value: 'Neutral' }],
      rawData: 'INSTRUMENT: S&P 500 (SPX)\nTECHNICAL BIAS: Neutral\n',
    }, 'NDX')).toBeNull()
  })

  it('builds macro tiles from live card fields', () => {
    const ctx = macroContext({
      macro_bias: 'Risk-On',
      fed_rate: '5.25-5.50%',
      yield_10y: 4.25,
      yield_10y_direction: 'Rising',
      dxy: { price: 104.2, weekly_change: -0.35, direction: 'Down' },
      wti_oil: { price: 72.1, weekly_change: 1.2, direction: 'Up' },
    })
    expect(ctx.bias).toBe('Risk-On')
    expect(ctx.yield10y).toMatchObject({ value: 4.25, unit: '%', direction: 'Rising' })
    expect(ctx.dxy).toMatchObject({ value: 104.2, change: -0.35 })
    expect(ctx.wti).toMatchObject({ value: 72.1, change: 1.2 })
  })

  it('parses archive macro metrics + raw markdown without eating bias', () => {
    const ctx = macroContext({
      metrics: [
        { label: 'Fed Rate', value: '3.50%-3.75%' },
        { label: '10Y Yield', value: '4.570%' },
        { label: 'Macro Bias', value: 'Binary-risk' },
      ],
      rawData: [
        'MACRO BIAS: Binary-risk',
        '',
        'PRIMARY DRIVER THIS WEEK: US Fed Interest Rate Decision event on June 18',
        '',
        'CONFIDENCE: Medium',
        '',
        '- WTI Crude Oil: 82.49, weekly change +15.52%, direction: rising',
        '- DXY (Dollar): 100.75, weekly change -0.22%, direction: falling',
      ].join('\n'),
    })
    expect(ctx.bias).toBe('Binary-risk')
    expect(ctx.yield10y.value).toBe(4.57)
    expect(ctx.dxy).toMatchObject({ value: 100.75, change: -0.22 })
    expect(ctx.wti).toMatchObject({ value: 82.49, change: 15.52 })
    expect(ctx.fedRate).toBe('3.50%-3.75%')
  })
})

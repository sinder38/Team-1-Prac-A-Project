/**
 * Final consensus brief fields — modelled on data/final prediction/prediction_*_Team1.md.
 *
 * rangeKind:
 *   percent — "-2.5% to +0.5%"
 *   yield   — "4.50% to 4.75%"
 *   level   — "17–28 range" (VIX)
 */

export const FINAL_PRED_ASSETS = [
  { key: 'spx', label: 'S&P 500 (SPX)', rangeKind: 'percent', step: 0.1 },
  { key: 'ndx', label: 'Nasdaq 100 (NDX)', rangeKind: 'percent', step: 0.1 },
  { key: 'iwm', label: 'Russell 2000 (IWM)', rangeKind: 'percent', step: 0.1 },
  { key: 'gold', label: 'Gold', rangeKind: 'percent', step: 0.1 },
  { key: 'wti', label: 'WTI Crude Oil', rangeKind: 'percent', step: 0.1 },
  { key: 'yield10y', label: '10-Year Yield', rangeKind: 'yield', step: 0.05 },
  { key: 'vix', label: 'VIX', rangeKind: 'level', step: 1 },
  { key: 'btc', label: 'Bitcoin', rangeKind: 'percent', step: 0.5 },
]

export const FINAL_PRED_DIRECTIONS = [
  'UP',
  'DOWN',
  'FLAT',
  'FLAT-UP',
  'FLAT-DOWN',
]

export const FINAL_PRED_CONFIDENCE = ['LOW', 'LOW-MEDIUM', 'MEDIUM', 'HIGH']

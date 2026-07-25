/**
 * Build / display helpers for the team final prediction brief
 * (data/final prediction/prediction_*_Team1.md).
 */
import { FINAL_PRED_ASSETS } from './constants/finalPrediction'

function emptyAssetRow() {
  return { direction: 'FLAT', rangeLow: '', rangeHigh: '', confidence: 'MEDIUM' }
}

function assetMeta(key) {
  return FINAL_PRED_ASSETS.find(a => a.key === key) || { rangeKind: 'percent' }
}

/** Format filed date like "17 JUL 2026". */
export function formatFiledDate(isoDate) {
  if (!isoDate) return '—'
  const d = new Date(`${isoDate}T12:00:00`)
  if (Number.isNaN(d.getTime())) return isoDate
  return d
    .toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
    .toUpperCase()
}

function parseBound(value) {
  if (value === '' || value == null) return null
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}

function formatSignedPercent(n) {
  const body = Math.abs(n).toFixed(1)
  if (n > 0) return `+${body}%`
  if (n < 0) return `-${body}%`
  return '+0.0%'
}

function formatYieldPercent(n) {
  return `${n.toFixed(2)}%`
}

/**
 * Build the markdown range cell from low/high numbers.
 * Falls back to a legacy free-text `range` if present.
 */
export function formatAssetRange(assetKey, row = {}) {
  if (typeof row.range === 'string' && row.range.trim() && row.rangeLow === undefined && row.rangeHigh === undefined) {
    return row.range.trim()
  }
  // Prefer low/high when either is set; otherwise keep legacy range string.
  const low = parseBound(row.rangeLow)
  const high = parseBound(row.rangeHigh)
  if (low == null && high == null) {
    return typeof row.range === 'string' && row.range.trim() ? row.range.trim() : ''
  }
  if (low == null || high == null) return ''

  const kind = assetMeta(assetKey).rangeKind || 'percent'
  if (kind === 'level') return `${low}–${high} range`
  if (kind === 'yield') return `${formatYieldPercent(low)} to ${formatYieldPercent(high)}`
  return `${formatSignedPercent(low)} to ${formatSignedPercent(high)}`
}

/**
 * Markdown matching the locked Team1 consensus brief layout.
 * Delta engine reads the asset table rows from this shape.
 */
export function buildFinalPredictionMarkdown(form, { week, filedDate } = {}) {
  const filed = formatFiledDate(filedDate)
  const weekLabel = week || '—'
  const lines = [
    `# TEAM 1 ${weekLabel} CONSENSUS BRIEF — FILED: ${filed}`,
    '',
    '## REGIME',
    '',
    form.regime?.trim() || '—',
    '',
    '| Asset              | Direction     | Range           | Confidence     |',
    '| ------------------ | ------------- | --------------- | -------------- |',
  ]

  for (const asset of FINAL_PRED_ASSETS) {
    const row = form.assets?.[asset.key] || emptyAssetRow()
    const direction = `**${row.direction || 'FLAT'}**`
    const confidence = `**${row.confidence || 'MEDIUM'}**`
    const range = formatAssetRange(asset.key, row) || '—'
    lines.push(
      `| ${asset.label.padEnd(18)} | ${direction.padEnd(13)} | ${range.padEnd(15)} | ${confidence.padEnd(14)} |`,
    )
  }

  lines.push(
    '',
    '## LEADING SECTOR',
    '',
    form.leadingSector?.trim() || '—',
    '',
    '## LAGGING SECTOR',
    '',
    form.laggingSector?.trim() || '—',
    '',
    '## KEY EVIDENCE (3 points)',
    '',
  )

  ;[form.evidence1, form.evidence2, form.evidence3].forEach((text, i) => {
    lines.push(`${i + 1}. ${(text || '').trim() || '—'}`)
    lines.push('')
  })

  lines.push(
    '## KEY CONTRADICTION (Why Confidence Is MEDIUM, Not HIGH)',
    '',
    form.contradiction?.trim() || '—',
    '',
    '## HUMAN OVERRIDE / WILD CARD',
    '',
    form.wildCard?.trim() || '—',
    '',
    '## INVALIDATION CONDITIONS',
    '',
    form.invalidation?.trim() || '—',
    '',
  )

  return lines.join('\n')
}

/** Regime + SPX/NDX/IWM ranges required before submit. */
export function isFinalPredictionComplete(form) {
  if (!form?.regime?.trim()) return false
  for (const key of ['spx', 'ndx', 'iwm']) {
    if (!formatAssetRange(key, form.assets?.[key] || {})) return false
  }
  return true
}

export function buildFinalPredictionReport(form, { week, predictionDate, runId } = {}) {
  if (!form) return null
  // Snapshot formatted ranges onto each asset so stored payload matches the brief.
  const assets = Object.fromEntries(
    FINAL_PRED_ASSETS.map(a => {
      const row = form.assets?.[a.key] || emptyAssetRow()
      return [a.key, { ...row, range: formatAssetRange(a.key, row) }]
    }),
  )
  const nextForm = { ...form, assets }
  return {
    form: nextForm,
    week,
    predictionDate,
    runId,
    filedDate: predictionDate,
    markdown: buildFinalPredictionMarkdown(nextForm, { week, filedDate: predictionDate }),
  }
}

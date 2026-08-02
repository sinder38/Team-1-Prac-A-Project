/**
 * Saved runs and agent outputs, read from the Flask backend's /artifacts/* routes.
 */
import { getJson } from './http'
import { DEFAULT_HORIZON_DAYS, getLlmModels } from './pipeline'
import { getFinalPrediction } from './finalPrediction'

const CONFIDENCE_SCORE = { Low: 40, 'Low-Medium': 55, Medium: 65, High: 85 }
const TECH_ORDER = ['SPX', 'NDX', 'IWM']

function commodityLine(c) {
  if (!c || c.price == null) return null
  const change = c.weekly_change != null ? ` (${c.weekly_change}% w/w)` : ''
  const dir = c.direction ? ` ${c.direction}` : ''
  return `${c.price}${change}${dir}`
}

function almanacCard(a) {
  const sectors = Array.isArray(a.sector_signals) ? a.sector_signals.slice(0, 5) : []
  const metrics = [
    { label: 'Thesis', value: a.thesis },
    { label: 'Seasonal Bias', value: a.seasonal_bias },
    { label: 'Monthly Bias', value: a.monthly_bias },
    { label: 'Confidence', value: a.confidence },
    a.weekly_pattern ? { label: 'Weekly Pattern', value: a.weekly_pattern } : null,
    ...sectors.map(s => ({
      label: s.sector,
      value: `${s.bias}${s.window ? ` — ${s.window}` : ''}`,
    })),
  ].filter(Boolean)

  return {
    agent: 'Almanac Agent',
    metrics,
    rawData: [
      `Almanac Agent Output — ${a.prediction_date}`,
      '',
      `ALMANAC THESIS: "${a.thesis || ''}"`,
      a.weekly_pattern ? `WEEKLY PATTERN: ${a.weekly_pattern}` : null,
      `ALMANAC SEASONAL BIAS: ${a.seasonal_bias}.`,
      `MONTHLY BIAS: ${a.monthly_bias}.`,
      `PATTERN CONFIDENCE: ${String(a.confidence || '').toUpperCase()}.`,
      ...(sectors.length
        ? ['', 'SECTOR SIGNALS:', ...sectors.map(s => `- ${s.sector}: ${s.bias} (${s.window || '—'})`)]
        : []),
    ]
      .filter(line => line != null)
      .join('\n'),
  }
}

function technicalCard(t) {
  const instruments = t.instruments || {}
  const keys = [
    ...TECH_ORDER.filter(k => instruments[k]),
    ...Object.keys(instruments).filter(k => !TECH_ORDER.includes(k)),
  ]
  const metrics = keys.flatMap(key => {
    const inst = instruments[key]
    return [
      { label: `${key} Close`, value: String(inst.last_close) },
      { label: `${key} Bias`, value: `${inst.trend_bias} (${inst.confidence})` },
      { label: `${key} EMA 8/21`, value: `${inst.ema_8} / ${inst.ema_21}` },
      { label: `${key} S/R`, value: `${inst.key_support} — ${inst.key_resistance}` },
    ]
  })

  const rawLines = ['Technical Agent Output', '']
  for (const key of keys) {
    const inst = instruments[key]
    rawLines.push(
      `INSTRUMENT: ${key}`,
      `LAST CLOSE: ${inst.last_close}`,
      `EMA (8/21): ${inst.ema_8} / ${inst.ema_21}`,
      `Support / Resistance: ${inst.key_support} — ${inst.key_resistance}`,
      `TECHNICAL BIAS: ${inst.trend_bias}.`,
      `CONFIDENCE: ${inst.confidence}.`,
      '',
    )
  }

  return {
    agent: 'Technical Agent',
    instruments,
    metrics,
    rawData: rawLines.join('\n').trim(),
  }
}

function macroCard(m) {
  const fomcBits = [
    m.next_fomc_date || null,
    m.hold_probability != null ? `hold ${m.hold_probability}%` : null,
    m.cut_probability != null ? `cut ${m.cut_probability}%` : null,
    m.fomc_direction && m.fomc_direction !== 'N/A' ? m.fomc_direction : null,
  ].filter(Boolean)

  const calendar = Array.isArray(m.week_ahead_calendar) ? m.week_ahead_calendar.slice(0, 8) : []
  const dxy = commodityLine(m.dxy)
  const wti = commodityLine(m.wti_oil)
  const gold = commodityLine(m.gold)
  const metrics = [
    { label: 'Primary Driver', value: m.primary_driver },
    { label: 'Macro Bias', value: m.macro_bias },
    { label: 'Fed Rate', value: m.fed_rate },
    {
      label: '10Y Yield',
      value: `${m.yield_10y}%${m.yield_10y_direction ? ` — ${m.yield_10y_direction}` : ''}`,
    },
    m.yield_2y != null ? { label: '2Y Yield', value: `${m.yield_2y}%` } : null,
    dxy ? { label: 'DXY', value: dxy } : null,
    wti ? { label: 'WTI Crude', value: wti } : null,
    gold ? { label: 'Gold', value: gold } : null,
    fomcBits.length ? { label: 'FOMC', value: fomcBits.join(' · ') } : null,
    m.invalidation ? { label: 'Invalidation', value: m.invalidation } : null,
  ].filter(Boolean)

  return {
    agent: 'Macro Agent',
    fed_rate: m.fed_rate,
    yield_10y: m.yield_10y,
    yield_10y_direction: m.yield_10y_direction,
    wti_oil: m.wti_oil,
    gold: m.gold,
    dxy: m.dxy,
    macro_bias: m.macro_bias,
    metrics,
    rawData: [
      `Macro Agent Output — ${m.prediction_date || ''}`,
      '',
      `Current Fed rate: ${m.fed_rate}`,
      fomcBits.length ? `Next FOMC: ${fomcBits.join('. ')}` : null,
      `2-year yield: ${m.yield_2y}%  10-year yield: ${m.yield_10y}%  30-year yield: ${m.yield_30y}%`,
      m.yield_curve ? `Yield curve: ${m.yield_curve}. 10-year direction: ${m.yield_10y_direction}` : null,
      '',
      `WTI Crude Oil: ${wti || '—'}`,
      `Gold: ${gold || '—'}`,
      `DXY (Dollar): ${dxy || '—'}`,
      '',
      ...(calendar.length
        ? [
            'WEEK-AHEAD CALENDAR:',
            ...calendar.map(
              e => `- ${e.date_label || ''}: ${e.name} [${e.impact}] exp ${e.expected ?? 'N/A'}`,
            ),
            '',
          ]
        : []),
      `MACRO BIAS: ${m.macro_bias}.`,
      `PRIMARY DRIVER THIS WEEK: ${m.primary_driver}`,
      `CONFIDENCE: ${m.confidence}.`,
      `INVALIDATION: ${m.invalidation || '—'}`,
    ]
      .filter(line => line != null)
      .join('\n'),
  }
}

function formatRange(range) {
  if (!range || range.low == null || range.high == null) return '—'
  return `${range.low}% to ${range.high}%`
}

function joinList(items) {
  if (!Array.isArray(items) || !items.length) return '—'
  return items.join('; ')
}

function buildLlmComparison(models) {
  const counts = {}
  for (const { data } of models) {
    counts[data.weekly_regime] = (counts[data.weekly_regime] || 0) + 1
  }
  const finalConsensus = Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'Uncertain'
  const agreeing = counts[finalConsensus] || 0
  const disagreementRatio = models.length
    ? Math.round(((models.length - agreeing) / models.length) * 100)
    : 0

  return {
    finalConsensus,
    disagreementRatio,
    models: models.map(({ name, data }) => ({
      name,
      consensus: data.weekly_regime,
      confidence: CONFIDENCE_SCORE[data.confidence] ?? 50,
      confidenceLabel: data.confidence || '—',
      spx: formatRange(data.spx_range),
      ndx: formatRange(data.ndx_range),
      iwm: formatRange(data.iwm_range),
      evidence: joinList(data.supporting_evidence),
      contradiction: joinList(data.contradictions),
      invalidation: data.invalidation || '—',
      plainEnglish: data.plain_english || '—',
    })),
  }
}

/**
 * List all weeks that have saved pipeline runs or archive markdown on disk.
 */
export async function getAvailableWeeks() {
  const data = await getJson('/artifacts/weeks')
  const weeks = (data.weeks || []).map(w => ({
    week: w.week,
    predictionDate: w.prediction_date,
    runId: w.run_id || null,
    stem: w.stem,
    source: w.source || (w.run_id ? 'run' : 'archive'),
    createdAt: w.created_at || null,
  }))
  return { weeks }
}

export async function getRunStatus(runId) {
  const data = await getJson(
    `/artifacts/run-status?run_id=${encodeURIComponent(runId)}`,
  )
  return {
    agentTypes: data.agent_types ?? [],
    hasLlmOutput: Boolean(data.has_llm_output),
    hasDeltaReport: Boolean(data.has_delta_report),
    hasHumanScore: Boolean(data.has_human_score),
  }
}

export async function getArchiveOutputs(stem) {
  const data = await getJson(`/artifacts/archive?stem=${encodeURIComponent(stem)}`)
  return {
    almanac: data.almanac || null,
    technical: data.technical || null,
    macro: data.macro || null,
    llmComparison: data.llmComparison || null,
    humanScoreReport: data.humanScoreReport || null,
    finalPrediction: data.finalPrediction || null,
  }
}

export async function getHumanScore({ stem, runId } = {}) {
  if (runId) {
    return getJson(`/artifacts/human-score?run_id=${encodeURIComponent(runId)}`)
  }
  if (!stem) throw new Error('stem or runId is required')
  return getJson(`/artifacts/human-score?stem=${encodeURIComponent(stem)}`)
}

/** Finviz PNGs for a week stem. */
export async function getEvidenceImages(stem) {
  if (!stem) return []
  const data = await getJson(`/artifacts/evidence-images?stem=${encodeURIComponent(stem)}`)
  return Array.isArray(data.images) ? data.images : []
}

/** Weekly moves from actuals_{stem}.md. */
export async function getActuals(stem) {
  if (!stem) return { stem: null, assets: {} }
  const data = await getJson(`/artifacts/actuals?stem=${encodeURIComponent(stem)}`)
  return {
    stem: data.stem || stem,
    assets: data.assets && typeof data.assets === 'object' ? data.assets : {},
  }
}

export async function getAgentOutputs({
  predictionDate,
  runId,
  horizonDays = DEFAULT_HORIZON_DAYS,
  includeLlm = true,
  allowPartial = false,
  stem,
  source,
}) {
  if (source === 'archive' || (source !== 'run' && !runId && stem)) {
    return getArchiveOutputs(stem)
  }

  const qs = `prediction_date=${predictionDate}&run_id=${runId}&horizon_days=${horizonDays}`
  const loadArtifact = async path => {
    if (!allowPartial) return getJson(path)
    try {
      return await getJson(path)
    } catch {
      return null
    }
  }

  const [almanac, technical, macro] = await Promise.all([
    loadArtifact(`/artifacts/almanac?${qs}`),
    loadArtifact(`/artifacts/technical?${qs}`),
    loadArtifact(`/artifacts/macro?${qs}`),
  ])

  let llmComparison = null
  if (includeLlm && runId) {
    try {
      const packed = await getJson(
        `/artifacts/llm-comparison?run_id=${encodeURIComponent(runId)}`,
      )
      if (packed.comparison) {
        llmComparison = packed.comparison
      } else if (Array.isArray(packed.models) && packed.models.length) {
        llmComparison = buildLlmComparison(packed.models)
      }
    } catch {
      // Fall back to per-model fetches (older servers / partial runs).
      const modelList = await getLlmModels()
      const models = []
      await Promise.all(
        modelList.map(async ({ key, name }) => {
          try {
            const data = await getJson(`/artifacts/llm?${qs}&model=${key}`)
            models.push({ name, data })
          } catch {
            // Skip models that failed or were not run.
          }
        }),
      )
      if (models.length) llmComparison = buildLlmComparison(models)
    }
  }

  let humanScoreReport = null
  let finalPrediction = null
  if (runId) {
    try {
      humanScoreReport = await getHumanScore({ runId })
    } catch {
      // No human score saved for this run yet.
    }
    try {
      finalPrediction = await getFinalPrediction(runId)
    } catch {
      // No final prediction for this run yet.
    }
  }

  return {
    almanac: almanac ? almanacCard(almanac) : null,
    technical: technical ? technicalCard(technical) : null,
    macro: macro ? macroCard(macro) : null,
    llmComparison,
    humanScoreReport,
    finalPrediction,
  }
}

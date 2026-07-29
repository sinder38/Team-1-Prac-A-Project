/**
 * Saved runs and agent outputs, read from the Flask backend's /artifacts/* routes.
 */
import { getJson } from './http'
import { DEFAULT_HORIZON_DAYS, getLlmModels } from './pipeline'
import { getFinalPrediction } from './finalPrediction'

const CONFIDENCE_SCORE = { Low: 40, 'Low-Medium': 55, Medium: 65, High: 85 }

function almanacCard(a) {
  return {
    agent: 'Almanac Agent',
    metrics: [
      { label: 'Monthly Bias', value: a.monthly_bias },
      { label: 'Seasonal Bias', value: a.seasonal_bias },
      { label: 'Thesis', value: a.thesis },
      ...(a.weekly_pattern ? [{ label: 'Weekly Pattern', value: a.weekly_pattern }] : []),
    ],
    rawData: [
      `Almanac Agent Output — ${a.prediction_date}`,
      '',
      a.thesis,
      '',
      `ALMANAC SEASONAL BIAS: ${a.seasonal_bias}.`,
      `PATTERN CONFIDENCE: ${String(a.confidence).toUpperCase()}.`,
    ].join('\n'),
  }
}

function technicalCard(t) {
  const inst = t.instruments?.SPX || Object.values(t.instruments || {})[0] || {}
  return {
    agent: 'Technical Agent',
    instruments: t.instruments || null,
    metrics: [
      { label: 'Instrument', value: 'S&P 500 (SPX)' },
      { label: 'Last Close', value: String(inst.last_close) },
      { label: 'EMA (8/21)', value: `${inst.ema_8} / ${inst.ema_21}` },
      { label: 'Support / Resistance', value: `${inst.key_support} - ${inst.key_resistance}` },
    ],
    rawData: [
      'Technical Agent Output',
      '',
      'INSTRUMENT: S&P 500 (SPX)',
      `LAST CLOSE: ${inst.last_close}`,
      '',
      `TECHNICAL BIAS: ${inst.trend_bias}.`,
      `CONFIDENCE: ${inst.confidence}.`,
    ].join('\n'),
  }
}

function macroCard(m) {
  return {
    agent: 'Macro Agent',
    fed_rate: m.fed_rate,
    yield_10y: m.yield_10y,
    yield_10y_direction: m.yield_10y_direction,
    wti_oil: m.wti_oil,
    gold: m.gold,
    dxy: m.dxy,
    macro_bias: m.macro_bias,
    metrics: [
      { label: 'Fed Rate', value: m.fed_rate },
      { label: '10Y Yield', value: `${m.yield_10y}% — ${m.yield_10y_direction}` },
      { label: 'WTI Crude', value: `${m.wti_oil?.price} (${m.wti_oil?.weekly_change}% w/w)` },
      { label: 'Gold', value: `${m.gold?.price} (${m.gold?.weekly_change}% w/w)` },
    ],
    rawData: [
      'Macro Agent Output',
      '',
      m.primary_driver,
      '',
      `MACRO BIAS: ${m.macro_bias}.`,
      `CONFIDENCE: ${m.confidence}.`,
    ].join('\n'),
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

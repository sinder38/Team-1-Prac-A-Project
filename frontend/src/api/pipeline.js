/**
 * Per-stage pipeline execution against the Flask backend (backend/server).
 * The human runs each stage manually (non-automatic), so there is no full-run
 * endpoint — the UI runs one stage at a time.
 *
 * UI stage -> backend call mapping:
 *   0 Data Fetching            -> no endpoint; data fetching happens inside each agent below
 *   1 Multi-Agent Processing   -> POST /stages/{almanac,technical,macro}
 *   2 LLM API Calls            -> POST /stages/evidence, then POST /stages/llm per model
 *   3 Delta Calibration Engine -> no endpoint yet
 */
import { postJson } from './http'
import { stageLogs } from '../lib/exampleData'

export const DEFAULT_HORIZON_DAYS = 7

export const LLM_MODELS = [
  { key: 'nemotron', name: 'NVIDIA Nemotron' },
  { key: 'hy3', name: 'Tencent HY3' },
  { key: 'gemma', name: 'Google Gemma' },
  { key: 'laguna', name: 'Poolside Laguna' },
]

export function getStageLogs(index) {
  return stageLogs(index)
}

function stageBody({ predictionDate, runId, horizonDays = DEFAULT_HORIZON_DAYS }) {
  return { prediction_date: predictionDate, run_id: runId, horizon_days: horizonDays }
}

/** Run a single pipeline stage. Resolves when that stage finishes. */
export async function runStage(index, run) {
  switch (index) {
    case 1:
      await Promise.all([
        postJson('/stages/almanac', stageBody(run)),
        postJson('/stages/technical', stageBody(run)),
        postJson('/stages/macro', stageBody(run)),
      ])
      return { failures: [] }
    case 2: {
      await postJson('/stages/evidence', {
        prediction_date: run.predictionDate,
        run_id: run.runId,
      })
      const failures = []
      for (const { key, name } of LLM_MODELS) {
        try {
          await postJson('/stages/llm', { ...stageBody(run), model: key })
        } catch (err) {
          failures.push(`${name}: ${err?.message || 'request failed'}`)
        }
      }
      if (failures.length === LLM_MODELS.length) {
        throw new Error(`All LLM models failed.\n${failures.join('\n')}`)
      }
      return { failures }
    }
    default:
      // Stage 0 (data fetching) and stage 3 (delta calibration) have no backend yet.
      return { failures: [] }
  }
}

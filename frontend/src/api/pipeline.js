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
import { getJson, postJson } from './http'
import { stageLogs } from '../lib/exampleData'

export const DEFAULT_HORIZON_DAYS = 7

/** Models enabled on the server (server.toml). Prefer this over a hardcoded list. */
export async function getLlmModels() {
  const data = await getJson('/stages/models')
  return (data.models || []).map(m => ({
    key: m.key,
    name: m.name || m.key,
  }))
}

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
      const models = await getLlmModels()
      if (!models.length) {
        throw new Error('No LLM models configured on the server (check server.toml).')
      }
      const failures = []
      for (const { key, name } of models) {
        try {
          await postJson('/stages/llm', { ...stageBody(run), model: key })
        } catch (err) {
          failures.push(`${name}: ${err?.message || 'request failed'}`)
        }
      }
      if (failures.length === models.length) {
        throw new Error(`All LLM models failed.\n${failures.join('\n')}`)
      }
      return { failures }
    }
    default:
      // Stage 0 (data fetching) and stage 3 (delta calibration) have no backend yet.
      return { failures: [] }
  }
}

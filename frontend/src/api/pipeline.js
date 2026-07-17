/**
 * Per-stage pipeline execution against the Flask backend (backend/server).
 * The human runs each stage manually (non-automatic), so there is no full-run
 * endpoint — the UI runs one stage at a time.
 *
 * UI stage -> backend call mapping:
 *   0 Data Fetching            -> no endpoint; data fetching happens inside each agent below
 *   1 Multi-Agent Processing   -> POST /stages/{almanac,technical,macro}
 *   2 LLM API Calls            -> POST /stages/evidence, then POST /stages/llm per model
 *   3 Previous Week Delta      -> POST /stages/delta
 */
import { postJson } from './http'
import { stageLogs } from '../lib/exampleData'

export const DEFAULT_HORIZON_DAYS = 7

export const LLM_MODELS = [
  { key: 'nemotron', name: 'NVIDIA Nemotron' },
  { key: 'gptoss', name: 'OpenAI gpt-oss' },
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
      return
    case 2:
      await postJson('/stages/evidence', {
        prediction_date: run.predictionDate,
        run_id: run.runId,
      })
      await Promise.all(
        LLM_MODELS.map(({ key }) =>
          postJson('/stages/llm', { ...stageBody(run), model: key }),
        ),
      )
      return
    case 3:
      await postJson('/stages/delta', {
        prediction_date: run.predictionDate,
        run_id: run.runId,
      })
      return
    default:
      // Stage 0 is represented by the data fetching inside the agent stages.
      return
  }
}

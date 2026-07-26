/**
 * Final consensus brief — persist / load by runtime run_id.
 */
import { getJson, postJson } from './http'

export async function getFinalPrediction(runId) {
  if (!runId) throw new Error('runId is required')
  return getJson(`/artifacts/final-prediction?run_id=${encodeURIComponent(runId)}`)
}

export async function submitFinalPrediction({ runId, report }) {
  if (!runId || !report) throw new Error('runId and report are required')
  return postJson('/artifacts/final-prediction', { run_id: runId, report })
}

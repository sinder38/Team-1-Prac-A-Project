/**
 * Pipeline status, logs, and per-stage execution.
 * The human runs each stage manually (non-automatic), so there is no full-run
 * endpoint — instead the UI runs one stage at a time.
 *
 * TODO (backend task): replace with real endpoints, e.g.
 *   GET  /api/pipeline/status
 *   GET  /api/pipeline/logs
 *   POST /api/pipeline/stage/{index}/run
 */
import { exampleIdlePipeline, stageLogs } from '../lib/exampleData'

const STAGE_DELAY_MS = 900

export async function getPipelineStatus() {
  // TODO: GET /api/pipeline/status
  return exampleIdlePipeline()
}

export async function getPipelineLogs() {
  // TODO: GET /api/pipeline/logs
  return { logs: [] }
}

export function getStageLogs(index) {
  return stageLogs(index)
}

/** Run a single pipeline stage. Resolves when that stage finishes. */
export function runStage(_index) {
  // TODO: POST /api/pipeline/stage/{index}/run
  return new Promise(resolve => setTimeout(resolve, STAGE_DELAY_MS))
}

/**
 * Per-stage pipeline execution. The human runs each stage manually (non-automatic),
 * so there is no full-run endpoint — the UI runs one stage at a time.
 *
 * TODO (backend task): replace with real endpoints, e.g.
 *   POST /api/pipeline/stage/{index}/run
 */
import { stageLogs } from '../lib/exampleData'

const STAGE_DELAY_MS = 900

export function getStageLogs(index) {
  return stageLogs(index)
}

/** Run a single pipeline stage. Resolves when that stage finishes. */
export function runStage(_index) {
  // TODO: POST /api/pipeline/stage/{index}/run
  return new Promise(resolve => setTimeout(resolve, STAGE_DELAY_MS))
}

/**
 * Human-score submit — persists on the runtime run in the DB.
 */
import { postJson } from './http'

/** Decision values accepted by the human-score endpoint. */
export const HUMAN_SCORE_DECISION = Object.freeze({
  SUBMITTED: 'submitted',
  DRAFT: 'draft',
})

export async function submitHumanScore({ runId, report }) {
  if (!runId || !report) {
    throw new Error('runId and report are required')
  }
  return postJson('/artifacts/human-score', { run_id: runId, report })
}

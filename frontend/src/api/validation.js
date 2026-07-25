/**
 * Human Score submit → POST /stages/human.
 * Sends the form JSON plus the run identity; the backend stores it in the DB and
 * can later export data/human/human_score_WXX.md via POST /export.
 */
import { postJson } from './http'
import { DEFAULT_HORIZON_DAYS } from './pipeline'

/** Decision values accepted by the human-score endpoint. */
export const HUMAN_SCORE_DECISION = Object.freeze({
  SUBMITTED: 'submitted',
  DRAFT: 'draft',
})

/**
 * Persist a finished Human Score report against a run.
 * @param {{ predictionDate: string, runId: string, horizonDays?: number,
 *           week?: string, form: object, consensus?: string, aiSaid?: object,
 *           total?: number }} payload
 * @param {string} decision
 */
export async function submitHumanScore(payload, decision = HUMAN_SCORE_DECISION.SUBMITTED) {
  if (decision !== HUMAN_SCORE_DECISION.SUBMITTED) {
    return { ok: true, draft: true }
  }
  const {
    predictionDate,
    runId,
    horizonDays = DEFAULT_HORIZON_DAYS,
    week,
    form,
    consensus,
    aiSaid,
    total,
  } = payload || {}
  if (!form || typeof form !== 'object') {
    throw new Error('Missing form for human score')
  }
  if (!predictionDate || !runId) {
    throw new Error('Missing run identity for human score')
  }
  return postJson('/stages/human', {
    prediction_date: predictionDate,
    run_id: runId,
    horizon_days: horizonDays,
    week,
    form,
    consensus,
    aiSaid,
    total,
  })
}

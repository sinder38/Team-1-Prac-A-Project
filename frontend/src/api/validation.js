/**
 * Human Score submit → POST /artifacts/human-score
 * Sends form JSON; backend stores JSON + builds data/human/human_score_WXX.md.
 */
import { postJson } from './http'

/** Decision values accepted by the human-score endpoint. */
export const HUMAN_SCORE_DECISION = Object.freeze({
  SUBMITTED: 'submitted',
  DRAFT: 'draft',
})

/**
 * Persist a finished Human Score report.
 * @param {{ week?: string, stem?: string, form: object, consensus?: string, aiSaid?: object, total?: number }} payload
 * @param {string} decision
 */
export async function submitHumanScore(payload, decision = HUMAN_SCORE_DECISION.SUBMITTED) {
  if (decision !== HUMAN_SCORE_DECISION.SUBMITTED) {
    return { ok: true, draft: true }
  }
  const { week, stem, form, consensus, aiSaid, total } = payload || {}
  if (!form || typeof form !== 'object') {
    throw new Error('Missing form for human score')
  }
  return postJson('/artifacts/human-score', {
    stem: stem || week,
    week,
    form,
    consensus,
    aiSaid,
    total,
  })
}

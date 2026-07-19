/**
 * Human Score submit → POST /artifacts/human-score
 * Writes data/human/human_score_WXX.md on the backend.
 */
import { postJson } from './http'

/** Decision values accepted by the human-score endpoint. */
export const HUMAN_SCORE_DECISION = Object.freeze({
  SUBMITTED: 'submitted',
  DRAFT: 'draft',
})

/**
 * Persist a finished Human Score report.
 * @param {{ week?: string, stem?: string, markdown: string }} payload
 * @param {string} decision
 */
export async function submitHumanScore(payload, decision = HUMAN_SCORE_DECISION.SUBMITTED) {
  if (decision !== HUMAN_SCORE_DECISION.SUBMITTED) {
    return { ok: true, draft: true }
  }
  const { week, stem, markdown } = payload || {}
  if (!markdown?.trim()) {
    throw new Error('Missing markdown for human score')
  }
  return postJson('/artifacts/human-score', {
    stem: stem || week,
    markdown,
  })
}

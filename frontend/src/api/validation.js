/**
 * TODO (backend task): Submit human review (R7).
 */

/** Decision values accepted by the human-score endpoint. */
export const HUMAN_SCORE_DECISION = Object.freeze({
  SUBMITTED: 'submitted',
  DRAFT: 'draft',
})

export async function submitHumanScore(_formData, _decision) {
  // TODO: POST /api/validation/human-score
  return { ok: true }
}

/**
 * Weeks list and agent outputs.
 * TODO (backend task): replace example data with GET /api/weeks and
 * GET /api/agents/outputs?week=... (see ../lib/exampleData.js).
 */
import {
  EXAMPLE_WEEKS,
  EXAMPLE_CURRENT_DATE,
  exampleAgentOutputs,
} from '../lib/exampleData'

export async function getAvailableWeeks() {
  // TODO: GET /api/weeks
  return { weeks: EXAMPLE_WEEKS, currentDate: EXAMPLE_CURRENT_DATE }
}

export async function getAgentOutputs(week) {
  // TODO: GET /api/agents/outputs?week=2026-W24
  return exampleAgentOutputs(week)
}

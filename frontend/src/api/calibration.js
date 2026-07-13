/**
 * Calibration scores.
 * TODO (backend task): replace example data with GET /api/calibration/accuracy-tracker.
 */
import { EXAMPLE_CALIBRATION } from '../lib/exampleData'

export async function getCalibrationScores() {
  // TODO: GET /api/calibration/accuracy-tracker
  return { ...EXAMPLE_CALIBRATION }
}

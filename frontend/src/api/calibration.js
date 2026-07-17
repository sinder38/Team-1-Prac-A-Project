import { getJson } from './http'

export async function getCalibrationScores() {
  return getJson('/calibration/accuracy-tracker')
}

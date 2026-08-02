/**
 * Backend API layer. Pipeline stages, artifacts, calibration, and market data
 * use Flask. Human-score and final-prediction submit persist by run_id.
 */
export { getStageLogs, getLlmModels, runStage, exportArtifacts, DEFAULT_HORIZON_DAYS } from './pipeline'

export {
  getAvailableWeeks,
  getAgentOutputs,
  getArchiveOutputs,
  getHumanScore,
  getRunStatus,
  getEvidenceImages,
  getActuals,
} from './agents'
export { getCalibrationScores } from './calibration'
export { submitHumanScore, HUMAN_SCORE_DECISION } from './validation'
export { getFinalPrediction, submitFinalPrediction } from './finalPrediction'
export { getInstruments, getMarketHistory } from './market'
export { getAuthStatus, login, logout } from './auth'

/**
 * Backend API layer. Pipeline stages, artifacts, and calibration use Flask;
 * human-score submission and market history still use local placeholders.
 */
export { getStageLogs, runStage, DEFAULT_HORIZON_DAYS } from './pipeline'

export { getAvailableWeeks, getAgentOutputs } from './agents'
export { getCalibrationScores } from './calibration'
export { submitHumanScore, HUMAN_SCORE_DECISION } from './validation'
export { getInstruments, getMarketHistory } from './market'

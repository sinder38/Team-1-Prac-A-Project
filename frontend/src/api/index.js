/**
 * Backend API layer — stubs until FastAPI integration (see each file for TODOs).
 */
export { getStageLogs, runStage } from './pipeline'

export { getAvailableWeeks, getAgentOutputs } from './agents'
export { getCalibrationScores } from './calibration'
export { submitHumanScore, HUMAN_SCORE_DECISION } from './validation'
export { getInstruments, getMarketHistory } from './market'

/**
 * Backend API layer — stubs until FastAPI integration (see each file for TODOs).
 */
export {
  getPipelineStatus,
  getPipelineLogs,
  getStageLogs,
  runStage,
} from './pipeline'

export { getAvailableWeeks, getAgentOutputs } from './agents'
export { getCalibrationScores } from './calibration'
export { submitHumanScore } from './validation'
export { getInstruments, getMarketHistory } from './market'

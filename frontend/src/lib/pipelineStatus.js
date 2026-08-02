import { PIPELINE_STAGE_IDS, stageCountThrough } from './exampleData'

const REQUIRED_AGENT_TYPES = ['almanac', 'macro', 'technical']

/** Infer pipeline progress from artifacts loaded from SQLite or an archive. */
export function completedStagesFromArtifacts(data = {}, runStatus = null) {
  const storedAgentTypes = runStatus?.agentTypes ?? REQUIRED_AGENT_TYPES.filter(type => data[type])
  const hasRequiredAgents = REQUIRED_AGENT_TYPES.every(type => storedAgentTypes.includes(type))
  const hasLlmOutput = runStatus?.hasLlmOutput ?? Boolean(data.llmComparison)
  const hasDeltaReport = runStatus?.hasDeltaReport ?? Boolean(data.deltaReport)
  const hasHumanScore = runStatus?.hasHumanScore ?? Boolean(data.humanScoreReport)
  const hasFinalPrediction = Boolean(data.finalPrediction)

  let lastCompletedStage = null
  if (hasRequiredAgents) lastCompletedStage = PIPELINE_STAGE_IDS.AGENTS
  if (hasLlmOutput) lastCompletedStage = PIPELINE_STAGE_IDS.LLM
  if (hasDeltaReport) lastCompletedStage = PIPELINE_STAGE_IDS.DELTA
  if (hasHumanScore) lastCompletedStage = PIPELINE_STAGE_IDS.HUMAN_SCORE
  if (hasFinalPrediction) lastCompletedStage = PIPELINE_STAGE_IDS.FINAL_PREDICTION

  return stageCountThrough(lastCompletedStage)
}

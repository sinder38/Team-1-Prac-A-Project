/** Infer saved archive progress when no runtime run ID is available. */
export function completedStagesFromArtifacts(data = {}) {
  if (data.humanScoreReport) return 5
  if (data.llmComparison) return 3
  if (data.almanac && data.macro && data.technical) return 2
  return 0
}

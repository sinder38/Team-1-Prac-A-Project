import { describe, expect, it } from 'vitest'

import { exampleSavedWeekPipeline } from '../src/lib/exampleData'
import { completedStagesFromArtifacts } from '../src/lib/pipelineStatus'

describe('completedStagesFromArtifacts', () => {
  it('keeps an agents-only archive run partially complete', () => {
    expect(
      completedStagesFromArtifacts({ almanac: {}, macro: {}, technical: {} }),
    ).toBe(2)
  })

  it('does not complete the agent stage when an agent is missing', () => {
    expect(completedStagesFromArtifacts({ almanac: {}, macro: {} })).toBe(0)
  })

  it('recognises later persisted artifacts', () => {
    expect(completedStagesFromArtifacts({ llmComparison: {} })).toBe(3)
    expect(completedStagesFromArtifacts({ humanScoreReport: {} })).toBe(5)
    expect(completedStagesFromArtifacts({ finalPrediction: {} })).toBe(6)
  })

  it('counts Human Score as 5 and Final Prediction as 6', () => {
    expect(
      completedStagesFromArtifacts({
        almanac: {},
        macro: {},
        technical: {},
        llmComparison: {},
        deltaReport: {},
        humanScoreReport: {},
      }),
    ).toBe(5)
    expect(
      completedStagesFromArtifacts({
        almanac: {},
        macro: {},
        technical: {},
        llmComparison: {},
        deltaReport: {},
        humanScoreReport: {},
        finalPrediction: {},
      }),
    ).toBe(6)
  })

  it('keeps an empty saved entry idle', () => {
    expect(completedStagesFromArtifacts({})).toBe(0)
  })
})

describe('exampleSavedWeekPipeline', () => {
  it('marks only persisted stages as successful', () => {
    const pipeline = exampleSavedWeekPipeline(
      '2026-W25',
      '2026-06-18',
      'run-1',
      { doneCount: 2 },
    )

    expect(pipeline.stages.map(stage => stage.status)).toEqual([
      'success',
      'success',
      'idle',
      'idle',
      'idle',
      'idle',
    ])
    expect(pipeline.accuracy).toBe(0)
  })
})

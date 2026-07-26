import { act, renderHook, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const api = vi.hoisted(() => ({
  exportArtifacts: vi.fn(),
  getAgentOutputs: vi.fn(),
  getAvailableWeeks: vi.fn(),
  getLlmModels: vi.fn(),
  getRunStatus: vi.fn(),
  getStageLogs: vi.fn(),
  runStage: vi.fn(),
  submitFinalPrediction: vi.fn(),
  submitHumanScore: vi.fn(),
}))

vi.mock('../src/api', () => ({
  ...api,
  DEFAULT_HORIZON_DAYS: 7,
}))

import { usePipeline } from '../src/hooks/usePipeline'

beforeEach(() => {
  vi.clearAllMocks()
  sessionStorage.clear()
  api.getAvailableWeeks.mockResolvedValue({ weeks: [] })
  api.getLlmModels.mockResolvedValue([])
  api.getStageLogs.mockReturnValue({ start: [], done: [] })
})

describe('usePipeline history restore', () => {
  it('keeps an agents-only runtime run in progress after reload', async () => {
    api.getAgentOutputs.mockResolvedValue({
      almanac: { agent: 'Almanac Agent' },
      macro: { agent: 'Macro Agent' },
      technical: { agent: 'Technical Agent' },
      llmComparison: null,
      humanScoreReport: null,
    })
    api.getRunStatus.mockResolvedValue({
      agentTypes: ['almanac', 'macro', 'technical'],
      hasLlmOutput: false,
      hasDeltaReport: false,
      hasHumanScore: false,
    })

    const { result } = renderHook(() => usePipeline())
    await waitFor(() => expect(api.getAvailableWeeks).toHaveBeenCalled())

    await act(async () => {
      await result.current.onWeekSelect({
        week: '2026-W25',
        predictionDate: '2026-06-18',
        runId: 'partial-run',
        source: 'run',
      })
    })

    expect(result.current.doneCount).toBe(2)
    expect(result.current.allDone).toBe(false)
    expect(result.current.pipeline.stages.map(stage => stage.status)).toEqual([
      'success',
      'success',
      'idle',
      'idle',
      'idle',
    ])
  })

  it('submits human score to the restored run after all AI stages', async () => {
    api.getAgentOutputs.mockResolvedValue({
      almanac: { agent: 'Almanac Agent' },
      macro: { agent: 'Macro Agent' },
      technical: { agent: 'Technical Agent' },
      llmComparison: null,
      humanScoreReport: null,
    })
    api.getRunStatus.mockResolvedValue({
      agentTypes: ['almanac', 'macro', 'technical'],
      hasLlmOutput: true,
      hasDeltaReport: true,
      hasHumanScore: false,
    })
    api.submitHumanScore.mockResolvedValue({ ok: true })

    const { result } = renderHook(() => usePipeline())
    await waitFor(() => expect(api.getAvailableWeeks).toHaveBeenCalled())

    await act(async () => {
      await result.current.onWeekSelect({
        week: '2026-W25',
        predictionDate: '2026-06-18',
        runId: 'restored-run',
        source: 'run',
      })
    })

    expect(result.current.doneCount).toBe(4)
    expect(result.current.aiComplete).toBe(true)

    await act(async () => {
      await result.current.completeReview({
        scores: {},
        reasoning: {},
        evidence: {},
      })
    })

    expect(api.submitHumanScore).toHaveBeenCalledWith(
      expect.objectContaining({ runId: 'restored-run' }),
    )
    expect(result.current.doneCount).toBe(5)
  })

  it('loads the week prediction owned by another run', async () => {
    api.getAgentOutputs.mockResolvedValue({
      almanac: { agent: 'Almanac Agent' },
      macro: { agent: 'Macro Agent' },
      technical: { agent: 'Technical Agent' },
      llmComparison: null,
      humanScoreReport: { week: '2026-W25' },
      finalPrediction: {
        week: '2026-W25',
        runId: 'prediction-owner',
        form: { regime: 'Neutral' },
      },
    })
    api.getRunStatus.mockResolvedValue({
      agentTypes: ['almanac', 'macro', 'technical'],
      hasLlmOutput: true,
      hasDeltaReport: true,
      hasHumanScore: true,
    })

    const { result } = renderHook(() => usePipeline())
    await waitFor(() => expect(api.getAvailableWeeks).toHaveBeenCalled())

    await act(async () => {
      await result.current.onWeekSelect({
        week: '2026-W25',
        predictionDate: '2026-06-18',
        runId: 'restored-run',
        source: 'run',
      })
    })

    expect(result.current.finalPrediction).toEqual(
      expect.objectContaining({ runId: 'prediction-owner' }),
    )
  })
})

import { afterEach, describe, expect, it, vi } from 'vitest'

import { getAgentOutputs, getRunStatus } from '../src/api/agents'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('saved runtime runs', () => {
  it('loads available agents without failing on missing agents', async () => {
    const fetchMock = vi.fn().mockImplementation(async url => {
      const found = url.startsWith('/artifacts/almanac?')
      return {
        ok: found,
        statusText: found ? 'OK' : 'Not Found',
        json: async () =>
          found
            ? {
                prediction_date: '2026-06-18',
                monthly_bias: 'Neutral',
                seasonal_bias: 'Neutral',
                thesis: 'Mixed conditions.',
                confidence: 'Medium',
              }
            : { error: 'Artifact not found' },
      }
    })
    vi.stubGlobal('fetch', fetchMock)

    const outputs = await getAgentOutputs({
      predictionDate: '2026-06-18',
      runId: 'partial-run',
      includeLlm: false,
      allowPartial: true,
      source: 'run',
    })

    expect(outputs.almanac).not.toBeNull()
    expect(outputs.technical).toBeNull()
    expect(outputs.macro).toBeNull()
  })

  it('maps the backend run status to frontend naming', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ completed_stages: 2 }),
      }),
    )

    await expect(getRunStatus('partial-run')).resolves.toEqual({
      completedStages: 2,
    })
  })
})

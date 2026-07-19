import { afterEach, describe, expect, it, vi } from 'vitest'

import { runStage } from '../src/api/pipeline'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('runStage', () => {
  it('runs the Delta Engine through the Flask backend', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ prediction_week: 'vW28' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await runStage(3, {
      predictionDate: '2026-07-13',
      runId: 'run1',
      horizonDays: 7,
    })

    expect(fetchMock).toHaveBeenCalledWith(
      '/stages/delta',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          prediction_date: '2026-07-13',
          run_id: 'run1',
        }),
      }),
    )
  })
})

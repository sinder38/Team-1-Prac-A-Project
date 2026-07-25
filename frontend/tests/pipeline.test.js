import { afterEach, describe, expect, it, vi } from 'vitest'

import { runStage, exportArtifacts } from '../src/api/pipeline'

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

describe('exportArtifacts', () => {
  it('posts a run_id for a runtime run', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ written: ['data/almanac/almanac_agent_W28.md'] }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const res = await exportArtifacts({ runId: 'run1' })

    expect(fetchMock).toHaveBeenCalledWith(
      '/export',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ run_id: 'run1', write: true }),
      }),
    )
    expect(res.written).toEqual(['data/almanac/almanac_agent_W28.md'])
  })

  it('posts a stem for an archive week', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ written: [] }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await exportArtifacts({ runId: 'ignored', stem: 'W25' })

    expect(fetchMock).toHaveBeenCalledWith(
      '/export',
      expect.objectContaining({
        body: JSON.stringify({ stem: 'W25', write: true }),
      }),
    )
  })
})

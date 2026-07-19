import { afterEach, describe, expect, it, vi } from 'vitest'

import { getCalibrationScores } from '../src/api/calibration'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('getCalibrationScores', () => {
  it('loads the real Delta Engine calibration endpoint', async () => {
    const payload = {
      currentAccuracy: 71.4,
      rangeAccuracy: 50,
      latestWeek: 'vW28',
    }
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => payload,
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(getCalibrationScores()).resolves.toEqual(payload)
    expect(fetchMock).toHaveBeenCalledWith(
      '/calibration/accuracy-tracker',
      undefined,
    )
  })
})

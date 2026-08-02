/**
 * Tests for ChartsPage error handling (src/pages/ChartsPage.jsx).
 *
 * What this covers:
 *  - When the market-history fetch fails, the page shows an error banner
 *    (previously such failures were invisible to the user).
 *  - Clicking "Retry" re-runs the fetch, and on success the error clears and
 *    the chart renders.
 *
 * Notes:
 *  - The api layer is mocked so we can force a failure then a success.
 *  - PriceChart is mocked because lightweight-charts needs a real canvas,
 *    which jsdom does not provide; we only care about ChartsPage behaviour here.
 *  - ChartsPage also fetches SPX/NDX/IWM for the compare panel, so the mock
 *    must always return a Promise (not undefined on later calls).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

vi.mock('../src/api', () => ({
  getInstruments: () => [{ symbol: 'SPX', name: 'S&P 500', yahoo: '^GSPC' }],
  getMarketHistory: vi.fn(),
  getEvidenceImages: vi.fn(() => Promise.resolve([])),
  getActuals: vi.fn(() => Promise.resolve({ stem: null, assets: {} })),
}))

vi.mock('../src/components/charts', () => ({
  PriceChart: () => <div data-testid="price-chart" />,
}))

import ChartsPage from '../src/pages/ChartsPage'
import { getMarketHistory } from '../src/api'

const SAMPLE = {
  symbol: 'SPX',
  name: 'S&P 500',
  yahoo: '^GSPC',
  decimals: 0,
  candles: [{ time: '2026-01-02', open: 1, high: 2, low: 1, close: 2 }],
  ema8: [],
  ema21: [],
  volume: [],
  stats: {
    last: 7554, change: 12, changePct: 0.16,
    periodHigh: 7600, periodLow: 7000, ema8: 7450, ema21: 7432, aboveEmas: true,
  },
}

describe('ChartsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows an error banner when the fetch fails', async () => {
    getMarketHistory.mockRejectedValue(new Error('network down'))
    render(<ChartsPage />)

    expect(await screen.findByText(/could not load spx/i)).toBeInTheDocument()
  })

  it('recovers and renders the chart after a successful retry', async () => {
    getMarketHistory
      .mockRejectedValueOnce(new Error('network down'))
      .mockResolvedValue(SAMPLE)

    render(<ChartsPage />)
    const retry = await screen.findByRole('button', { name: /retry/i })

    await userEvent.click(retry)

    await waitFor(() => {
      expect(screen.getByTestId('price-chart')).toBeInTheDocument()
    })
    expect(screen.queryByText(/could not load spx/i)).not.toBeInTheDocument()
  })

  it('refetches with the selected range days', async () => {
    getMarketHistory.mockResolvedValue(SAMPLE)
    render(<ChartsPage predictionDate="2026-07-13" />)

    await waitFor(() => expect(getMarketHistory).toHaveBeenCalled())
    getMarketHistory.mockClear()

    await userEvent.click(screen.getByRole('button', { name: '1M' }))

    await waitFor(() => {
      expect(getMarketHistory).toHaveBeenCalledWith(
        'SPX',
        expect.objectContaining({ days: 22, endDate: '2026-07-13' }),
      )
    })
  })
})

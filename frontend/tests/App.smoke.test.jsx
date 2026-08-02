/**
 * Boot smoke: catch merge-dropped imports / undefined refs in App shell.
 */
import { render, screen, waitFor } from '@testing-library/react'
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
  getAuthStatus: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  getInstruments: vi.fn(() => [{ symbol: 'SPX', name: 'S&P 500', yahoo: '^GSPC' }]),
  getMarketHistory: vi.fn(),
  getEvidenceImages: vi.fn(() => Promise.resolve([])),
  getActuals: vi.fn(() => Promise.resolve({ stem: null, assets: {} })),
  getCalibrationScores: vi.fn(() => Promise.resolve([])),
  getArchiveOutputs: vi.fn(),
  getHumanScore: vi.fn(),
  getFinalPrediction: vi.fn(),
}))

vi.mock('../src/api', () => ({
  ...api,
  DEFAULT_HORIZON_DAYS: 7,
}))

vi.mock('../src/components/charts', () => ({
  PriceChart: () => <div data-testid="price-chart" />,
}))

vi.mock('../src/api/auth', () => ({
  getAuthStatus: api.getAuthStatus,
  login: api.login,
  logout: api.logout,
}))

import App from '../src/app/App'

beforeEach(() => {
  vi.clearAllMocks()
  sessionStorage.clear()
  window.history.replaceState(null, '', '/')
  api.getAvailableWeeks.mockResolvedValue({ weeks: [] })
  api.getLlmModels.mockResolvedValue([])
  api.getStageLogs.mockReturnValue({ start: [], done: [] })
  api.getAuthStatus.mockResolvedValue({
    isAuthenticated: false,
    isConfigured: true,
    username: null,
  })
})

describe('App smoke', () => {
  it('boots the shell without throwing', async () => {
    render(<App />)
    await waitFor(() => {
      expect(screen.getByLabelText('Main navigation')).toBeInTheDocument()
    })
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument()
  })
})

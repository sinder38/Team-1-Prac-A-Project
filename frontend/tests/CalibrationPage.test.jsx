import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../src/api', () => ({
  getCalibrationScores: vi.fn(),
}))

import { getCalibrationScores } from '../src/api'
import CalibrationPage from '../src/pages/CalibrationPage'

const SCORES = {
  totalAccuracy: 60.7,
  currentAccuracy: 71.4,
  rangeAccuracy: 50,
  latestDirectionAccuracy: 75,
  latestRangeAccuracy: 66.7,
  latestWeek: 'vW28',
  sectorCoverage: 11,
  sectorTotal: 11,
  suggestedWeights: { technical: 30, human_score: 20 },
  weeklyTrend: [
    { week: 'W24', directionAccuracy: 66.7, rangeAccuracy: 33.3 },
    { week: 'W28', directionAccuracy: 75, rangeAccuracy: 66.7 },
  ],
  prescription: 'Review missed ranges before the next lock.',
  lastCalculated: '2026-07-17T20:30:00Z',
}

describe('CalibrationPage', () => {
  beforeEach(() => {
    getCalibrationScores.mockResolvedValue(SCORES)
  })

  it('shows latest week, cumulative scores, history, weights, and prescription', async () => {
    render(<CalibrationPage pipeline={{ lastRun: null }} />)

    expect(await screen.findByText('Latest scored week')).toBeInTheDocument()
    expect(screen.getByText('71.4%')).toBeInTheDocument()
    expect(screen.getByText('11 / 11')).toBeInTheDocument()
    expect(screen.getByText('Technical Agent')).toBeInTheDocument()
    expect(screen.getByText('Week by week')).toBeInTheDocument()
    expect(screen.getByText('Review missed ranges before the next lock.')).toBeInTheDocument()
  })
})

import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import LogsPage from '../src/pages/LogsPage'

const pipeline = {
  id: 'run-guest',
  isRunning: false,
  lastRun: null,
  accuracy: 0,
  stages: [
    { id: 'almanac', name: 'Almanac', status: 'success' },
    { id: 'technical', name: 'Technical', status: 'idle' },
  ],
  week: '2026-W31',
}

describe('LogsPage access', () => {
  it('shows an accurate read-only state for a visitor', () => {
    render(
      <LogsPage
        pipeline={pipeline}
        controls={{
          isRunning: false,
          allDone: false,
          aiStages: 4,
          doneCount: 1,
          runNext: vi.fn(),
          canEdit: false,
        }}
        week="2026-W31"
        predictionDate="2026-07-27"
      />,
    )

    expect(screen.getByText('Read only')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Run stage/ })).not.toBeInTheDocument()
  })
})

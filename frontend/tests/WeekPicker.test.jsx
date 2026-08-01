/**
 * WeekPicker lists every run per week as run_01 / run_02 and keeps a new-run option.
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import WeekPicker from '../src/components/pipeline/WeekPicker'

const t1 = '2026-07-16T10:05:00.000Z'
const t2 = '2026-07-16T14:30:00.000Z'

const savedWeeks = [
  { week: '2026-W28', predictionDate: '2026-07-06', source: 'archive', stem: 'W28' },
  {
    week: '2026-W29',
    predictionDate: '2026-07-13',
    source: 'run',
    stem: 'W29',
    runId: 'run-aaa',
    createdAt: t1,
  },
  {
    week: '2026-W29',
    predictionDate: '2026-07-13',
    source: 'run',
    stem: 'W29',
    runId: 'run-bbb',
    createdAt: t2,
  },
]

describe('WeekPicker', () => {
  it('lists multiple runs for the same week as run_01 / run_02', () => {
    render(
      <WeekPicker
        predictionDate="2026-07-13"
        selectedWeek="2026-W29"
        selectedRunId="run-bbb"
        savedWeeks={savedWeeks}
        mode="archive"
        newWeek="2026-W31"
        newPredictionDate="2026-07-27"
        onDateChange={() => {}}
        onWeekSelect={() => {}}
      />,
    )

    const runPicker = screen.getByLabelText('Saved run')
    const labels = within(runPicker).getAllByRole('option').map(o => o.textContent)
    expect(labels).toEqual([
      '2026-W28',
      '2026-W29 · run_01',
      '2026-W29 · run_02',
      '2026-W31 · new',
    ])
    expect(runPicker).toHaveValue('run:2026-W29:run-bbb')
    expect(screen.getByText('run_02')).toBeInTheDocument()
  })

  it('always keeps a new-run option even when that week already has runs', () => {
    render(
      <WeekPicker
        predictionDate="2026-07-20"
        selectedWeek="2026-W30"
        savedWeeks={[
          ...savedWeeks,
          {
            week: '2026-W30',
            predictionDate: '2026-07-20',
            source: 'run',
            stem: 'W30',
            runId: 'run-ms06533c',
            createdAt: '2026-07-20T09:00:00.000Z',
          },
        ]}
        mode="new"
        newWeek="2026-W30"
        newPredictionDate="2026-07-20"
        onDateChange={() => {}}
        onWeekSelect={() => {}}
      />,
    )

    const runPicker = screen.getByLabelText('Saved run')
    const labels = within(runPicker).getAllByRole('option').map(o => o.textContent)
    expect(labels).toContain('2026-W30 · run_01')
    expect(labels).toContain('2026-W30 · new')
    expect(runPicker).toHaveValue('new:2026-W30')
  })

  it('selecting the new week calls onDateChange, not onWeekSelect', async () => {
    const onDateChange = vi.fn()
    const onWeekSelect = vi.fn()

    render(
      <WeekPicker
        predictionDate="2026-07-13"
        selectedWeek="2026-W29"
        selectedRunId="run-aaa"
        savedWeeks={savedWeeks}
        mode="archive"
        newWeek="2026-W30"
        newPredictionDate="2026-07-20"
        onDateChange={onDateChange}
        onWeekSelect={onWeekSelect}
      />,
    )

    await userEvent.selectOptions(screen.getByLabelText('Saved run'), 'new:2026-W30')

    expect(onDateChange).toHaveBeenCalledWith('2026-07-20')
    expect(onWeekSelect).not.toHaveBeenCalled()
  })

  it('selecting a specific run calls onWeekSelect with that runId', async () => {
    const onWeekSelect = vi.fn()

    render(
      <WeekPicker
        predictionDate="2026-07-20"
        selectedWeek="2026-W30"
        savedWeeks={savedWeeks}
        mode="new"
        newWeek="2026-W30"
        newPredictionDate="2026-07-20"
        onDateChange={() => {}}
        onWeekSelect={onWeekSelect}
      />,
    )

    await userEvent.selectOptions(
      screen.getByLabelText('Saved run'),
      'run:2026-W29:run-aaa',
    )

    expect(onWeekSelect).toHaveBeenCalledWith(
      expect.objectContaining({ week: '2026-W29', runId: 'run-aaa' }),
    )
  })

  it('keeps saved runs available in read-only mode', async () => {
    const onDateChange = vi.fn()
    const onWeekSelect = vi.fn()

    render(
      <WeekPicker
        predictionDate="2026-07-20"
        selectedWeek="2026-W30"
        savedWeeks={savedWeeks}
        mode="new"
        newWeek="2026-W30"
        newPredictionDate="2026-07-20"
        onDateChange={onDateChange}
        onWeekSelect={onWeekSelect}
        readOnly
      />,
    )

    expect(screen.getByDisplayValue('2026-07-20')).toBeDisabled()
    expect(screen.getByLabelText('Prediction horizon')).toBeDisabled()
    expect(screen.getByRole('option', { name: '2026-W30 · new' })).toBeDisabled()

    await userEvent.selectOptions(
      screen.getByLabelText('Saved run'),
      'run:2026-W29:run-aaa',
    )
    expect(onWeekSelect).toHaveBeenCalledWith(
      expect.objectContaining({ runId: 'run-aaa' }),
    )
    expect(onDateChange).not.toHaveBeenCalled()
  })
})

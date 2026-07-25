/**
 * WeekPicker always keeps a "new" week option after viewing archives.
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import WeekPicker from '../src/components/pipeline/WeekPicker'

const savedWeeks = [
  { week: '2026-W28', predictionDate: '2026-07-06', source: 'archive', stem: 'W28' },
  { week: '2026-W29', predictionDate: '2026-07-13', source: 'archive', stem: 'W29' },
]

describe('WeekPicker', () => {
  it('keeps a calendar-chosen unrun week in the list while viewing an archive', () => {
    render(
      <WeekPicker
        predictionDate="2026-07-13"
        selectedWeek="2026-W29"
        savedWeeks={savedWeeks}
        mode="archive"
        newWeek="2026-W31"
        newPredictionDate="2026-07-27"
        onDateChange={() => {}}
        onWeekSelect={() => {}}
      />,
    )

    const labels = screen.getAllByRole('option').map(o => o.textContent)
    expect(labels).toEqual(['2026-W28', '2026-W29', '2026-W31'])
    expect(screen.getByText('Archive')).toBeInTheDocument()
    expect(screen.getByRole('combobox')).toHaveValue('archive:2026-W29')
  })

  it('does not duplicate a week that is both new and already saved', () => {
    render(
      <WeekPicker
        predictionDate="2026-07-20"
        selectedWeek="2026-W30"
        savedWeeks={[
          ...savedWeeks,
          { week: '2026-W30', predictionDate: '2026-07-20', source: 'archive', stem: 'W30' },
        ]}
        mode="new"
        newWeek="2026-W30"
        newPredictionDate="2026-07-20"
        onDateChange={() => {}}
        onWeekSelect={() => {}}
      />,
    )

    const labels = screen.getAllByRole('option').map(o => o.textContent)
    expect(labels).toEqual(['2026-W28', '2026-W29', '2026-W30'])
    expect(screen.getByRole('combobox')).toHaveValue('archive:2026-W30')
  })

  it('selecting the new week calls onDateChange, not onWeekSelect', async () => {
    const onDateChange = vi.fn()
    const onWeekSelect = vi.fn()

    render(
      <WeekPicker
        predictionDate="2026-07-13"
        selectedWeek="2026-W29"
        savedWeeks={savedWeeks}
        mode="archive"
        newWeek="2026-W30"
        newPredictionDate="2026-07-20"
        onDateChange={onDateChange}
        onWeekSelect={onWeekSelect}
      />,
    )

    await userEvent.selectOptions(screen.getByRole('combobox'), 'new:2026-W30')

    expect(onDateChange).toHaveBeenCalledWith('2026-07-20')
    expect(onWeekSelect).not.toHaveBeenCalled()
  })
})

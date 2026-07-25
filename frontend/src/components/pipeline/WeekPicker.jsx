/**
 * Pick a date or choose a saved/archive week. Keeps the calendar-chosen
 * (not-yet-run) week in the list after switching to a past archive.
 */
import { useMemo } from 'react'
import PropTypes from 'prop-types'
import { Calendar } from 'lucide-react'
import { dateToWeekLabel, todayIso } from '../../lib/date'

export default function WeekPicker({
  predictionDate,
  selectedWeek,
  savedWeeks = [],
  onDateChange,
  onWeekSelect,
  disabled,
  mode = 'new',
  newWeek: newWeekProp,
  newPredictionDate: newPredictionDateProp,
}) {
  const newPredictionDate = newPredictionDateProp || todayIso()
  const newWeek = newWeekProp || dateToWeekLabel(newPredictionDate)

  const options = useMemo(() => {
    const savedHasNew = savedWeeks.some(w => w.week === newWeek)
    const list = savedWeeks.map(w => ({
      week: w.week,
      value: `archive:${w.week}`,
      label: w.week,
      kind: 'archive',
      entry: w,
    }))
    // Only inject "new" when that week isn't already a saved/archive entry
    // (avoids two identical W30 rows after dropping (new)/(archive) labels).
    if (!savedHasNew) {
      list.push({
        week: newWeek,
        value: `new:${newWeek}`,
        label: newWeek,
        kind: 'new',
      })
    }
    return list.sort((a, b) => a.week.localeCompare(b.week))
  }, [savedWeeks, newWeek])

  const selectValue =
    mode === 'archive' && selectedWeek
      ? `archive:${selectedWeek}`
      : savedWeeks.some(w => w.week === newWeek)
        ? `archive:${newWeek}`
        : `new:${newWeek}`

  return (
    <div className="flex flex-col sm:flex-row gap-2 sm:items-center">
      <div className="flex items-center gap-2">
        <Calendar className="w-4 h-4 text-gray-400 shrink-0" />
        <input
          type="date"
          value={predictionDate}
          onChange={e => onDateChange(e.target.value)}
          disabled={disabled}
          className="px-2 py-1.5 text-sm border border-gray-200 rounded-md bg-white text-gray-900 focus:outline-none focus:border-gray-400 disabled:bg-gray-50 disabled:text-gray-400"
        />
      </div>

      <select
        value={selectValue}
        onChange={e => {
          const hit = options.find(o => o.value === e.target.value)
          if (!hit) return
          if (hit.kind === 'new') onDateChange(newPredictionDate)
          else onWeekSelect(hit.entry)
        }}
        disabled={disabled}
        className="px-2 py-1.5 text-sm border border-gray-200 rounded-md bg-white text-gray-900 focus:outline-none focus:border-gray-400 disabled:bg-gray-50 disabled:text-gray-400"
      >
        {options.map(o => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>

      <span className="text-xs text-gray-500 whitespace-nowrap">
        {mode === 'archive' ? 'Archive' : 'New run'}
      </span>
    </div>
  )
}

WeekPicker.propTypes = {
  predictionDate: PropTypes.string,
  selectedWeek: PropTypes.string,
  savedWeeks: PropTypes.array,
  onDateChange: PropTypes.func,
  onWeekSelect: PropTypes.func,
  disabled: PropTypes.bool,
  mode: PropTypes.oneOf(['new', 'archive']),
  newWeek: PropTypes.string,
  newPredictionDate: PropTypes.string,
}

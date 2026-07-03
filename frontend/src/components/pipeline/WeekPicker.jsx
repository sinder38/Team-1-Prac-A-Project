/**
 * Pick a date or choose a saved week.
 */
import PropTypes from 'prop-types'
import { Calendar } from 'lucide-react'

export default function WeekPicker({
  predictionDate,
  selectedWeek,
  savedWeeks = [],
  onDateChange,
  onWeekSelect,
  disabled,
}) {
  return (
    <div className="flex flex-col sm:flex-row gap-2 sm:items-center">
      <div className="flex items-center gap-2">
        <Calendar className="w-4 h-4 text-gray-400 shrink-0" />
        <input
          type="date"
          value={predictionDate}
          onChange={e => onDateChange(e.target.value)}
          disabled={disabled}
          className="px-2 py-1.5 text-sm border border-gray-200 rounded-md focus:outline-none focus:border-gray-400 disabled:bg-gray-50 disabled:text-gray-400"
        />
      </div>
      <span className="text-sm font-medium text-gray-900">{selectedWeek}</span>
      {savedWeeks.length > 0 && (
        <select
          value={selectedWeek}
          onChange={e => {
            const hit = savedWeeks.find(w => w.week === e.target.value)
            if (hit) onWeekSelect(hit)
          }}
          disabled={disabled}
          className="px-2 py-1.5 text-sm border border-gray-200 rounded-md focus:outline-none focus:border-gray-400 disabled:bg-gray-50"
        >
          {savedWeeks.map(w => (
            <option key={w.week} value={w.week}>
              {w.week}
            </option>
          ))}
        </select>
      )}
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
}

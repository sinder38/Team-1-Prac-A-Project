/**
 * Pick a date, start a new run, or open a saved run.
 * Multiple run_ids can exist for the same ISO week — each is its own option.
 * Labels use run_01 / run_02 (per week); opaque DB run_id stays in the value only.
 */
import { useMemo } from 'react'
import PropTypes from 'prop-types'
import { Calendar } from 'lucide-react'
import { dateToWeekLabel, todayIso } from '../../lib/date'

function optionValue(entry) {
  if (entry.runId) return `run:${entry.week}:${entry.runId}`
  return `archive:${entry.week}`
}

/** 1 → run_01, 12 → run_12 */
function runLabel(n) {
  return `run_${String(n).padStart(2, '0')}`
}

/**
 * Assign run_01… per week by createdAt (then runId). Archives keep week-only labels.
 */
function withDisplayLabels(savedWeeks) {
  const byWeek = new Map()
  for (const w of savedWeeks) {
    if (!w.runId) continue
    const list = byWeek.get(w.week) || []
    list.push(w)
    byWeek.set(w.week, list)
  }
  const labelByKey = new Map()
  for (const [week, runs] of byWeek) {
    runs
      .slice()
      .sort(
        (a, b) =>
          String(a.createdAt || '').localeCompare(String(b.createdAt || '')) ||
          String(a.runId).localeCompare(String(b.runId)),
      )
      .forEach((w, i) => {
        labelByKey.set(`${week}:${w.runId}`, runLabel(i + 1))
      })
  }
  return labelByKey
}

export default function WeekPicker({
  predictionDate,
  selectedWeek,
  selectedRunId = null,
  savedWeeks = [],
  onDateChange,
  onWeekSelect,
  horizonDays = 7,
  onHorizonChange,
  disabled,
  mode = 'new',
  newWeek: newWeekProp,
  newPredictionDate: newPredictionDateProp,
}) {
  const newPredictionDate = newPredictionDateProp || todayIso()
  const newWeek = newWeekProp || dateToWeekLabel(newPredictionDate)

  const displayLabels = useMemo(() => withDisplayLabels(savedWeeks), [savedWeeks])

  const options = useMemo(() => {
    const list = savedWeeks.map(w => {
      const display = w.runId ? displayLabels.get(`${w.week}:${w.runId}`) : null
      return {
        week: w.week,
        value: optionValue(w),
        label: display ? `${w.week} · ${display}` : w.week,
        kind: w.runId ? 'run' : 'archive',
        entry: w,
        display,
      }
    })
    list.push({
      week: newWeek,
      value: `new:${newWeek}`,
      label: `${newWeek} · new`,
      kind: 'new',
    })
    return list.sort((a, b) => {
      const weekCmp = a.week.localeCompare(b.week)
      if (weekCmp !== 0) return weekCmp
      if (a.kind === 'new') return 1
      if (b.kind === 'new') return -1
      const aAt = a.entry?.createdAt || ''
      const bAt = b.entry?.createdAt || ''
      return aAt.localeCompare(bAt) || a.label.localeCompare(b.label)
    })
  }, [savedWeeks, newWeek, displayLabels])

  const selectedDisplay =
    selectedWeek && selectedRunId
      ? displayLabels.get(`${selectedWeek}:${selectedRunId}`)
      : null

  const selectValue =
    mode === 'new'
      ? `new:${newWeek}`
      : selectedRunId && selectedWeek
        ? `run:${selectedWeek}:${selectedRunId}`
        : selectedWeek
          ? `archive:${selectedWeek}`
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
        value={horizonDays}
        onChange={e => onHorizonChange?.(Number(e.target.value))}
        disabled={disabled}
        aria-label="Prediction horizon"
        className="px-2 py-1.5 text-sm border border-gray-200 rounded-md bg-white text-gray-900 focus:outline-none focus:border-gray-400 disabled:bg-gray-50 disabled:text-gray-400"
      >
        <option value={7}>7 days</option>
        <option value={14}>14 days</option>
        <option value={21}>21 days</option>
        <option value={28}>28 days</option>
      </select>


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
        {mode === 'new'
          ? 'New run'
          : selectedDisplay
            ? selectedDisplay
            : selectedRunId
              ? 'Saved run'
              : 'Archive'}
      </span>
    </div>
  )
}

WeekPicker.propTypes = {
  predictionDate: PropTypes.string,
  selectedWeek: PropTypes.string,
  selectedRunId: PropTypes.string,
  savedWeeks: PropTypes.array,
  onDateChange: PropTypes.func,
  onWeekSelect: PropTypes.func,
  horizonDays: PropTypes.number,
  onHorizonChange: PropTypes.func,
  disabled: PropTypes.bool,
  mode: PropTypes.oneOf(['new', 'archive']),
  newWeek: PropTypes.string,
  newPredictionDate: PropTypes.string,
}

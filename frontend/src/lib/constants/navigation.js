/**
 * Menu labels and page names for sidebar and header.
 */
import { Home, CandlestickChart, ScrollText, BarChart3, Info } from 'lucide-react'

export const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: Home },
  { id: 'charts', label: 'Charts', icon: CandlestickChart },
  { id: 'logs', label: 'Logs', icon: ScrollText },
  { id: 'calibration', label: 'Calibration', icon: BarChart3 },
  { id: 'settings', label: 'About', icon: Info },
]

export const PAGE_TITLES = {
  dashboard: { section: 'Dashboard', page: 'Overview' },
  charts: { section: 'Charts', page: 'Market Charts' },
  logs: { section: 'Logs', page: 'Run status' },
  calibration: { section: 'Calibration', page: 'Accuracy Tracker' },
  settings: { section: 'About', page: 'About' },
}

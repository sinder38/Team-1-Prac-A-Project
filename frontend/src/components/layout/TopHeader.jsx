/**
 * Top bar showing the current page name.
 */
import { PAGE_TITLES } from '../../lib/constants'

export default function TopHeader({ page = 'dashboard' }) {
  const { section, page: title } = PAGE_TITLES[page] || PAGE_TITLES.dashboard

  return (
    <header className="h-12 bg-white border-b border-gray-200 px-4 md:px-6 flex items-center justify-between shrink-0">
      <div className="text-sm text-gray-500 min-w-0">
        <span className="hidden sm:inline">{section} / </span>
        <span className="text-gray-900 font-medium">{title}</span>
      </div>
      <span className="text-xs text-gray-400">Market Intelligence · Team 1</span>
    </header>
  )
}

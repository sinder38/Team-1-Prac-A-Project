/**
 * Top bar showing the current page name.
 */
import PropTypes from 'prop-types'
import { PAGE_TITLES } from '../../lib/constants'
import { AuthControl } from '../auth'

export default function TopHeader({ page = 'dashboard', auth }) {
  const { section, page: title } = PAGE_TITLES[page] || PAGE_TITLES.dashboard

  return (
    <header className="w-full h-12 rounded-2xl border border-gray-200 bg-white shadow-md px-4 md:px-6 flex items-center justify-between shrink-0">
      <div className="text-sm text-gray-500 min-w-0">
        <span className="hidden sm:inline">{section} / </span>
        <span className="text-gray-900 font-medium">{title}</span>
      </div>
      <div className="flex items-center gap-3 min-w-0">
        <span className="hidden md:inline text-xs text-gray-400">
          Market Intelligence · Team 1
        </span>
        {auth && <AuthControl auth={auth} />}
      </div>
    </header>
  )
}

TopHeader.propTypes = {
  page: PropTypes.string,
  auth: PropTypes.object,
}

/**
 * Left sidebar with icons to open each page.
 */
import { NAV_ITEMS } from '../../lib/constants'

export default function LeftNavigation({ active, onChange }) {
  return (
    <div className="w-14 md:w-16 bg-white border-r border-gray-200 flex flex-col items-center py-4 shrink-0">
      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => onChange(id)}
            title={label}
            className={`relative w-10 h-10 rounded-md flex items-center justify-center group ${
              active === id
                ? 'bg-gray-100 text-gray-900'
                : 'text-gray-400 hover:text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Icon className="w-5 h-5" />
            <span className="absolute left-12 bg-white text-gray-700 px-2 py-1 rounded text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none border border-gray-200 shadow-sm z-50">
              {label}
            </span>
          </button>
        ))}
      </nav>
    </div>
  )
}

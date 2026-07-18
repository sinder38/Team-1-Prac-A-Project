/**
 * Floating left nav — rounded, translucent pill in its own section.
 */
import PropTypes from 'prop-types'
import { NAV_ITEMS } from '../../lib/constants'

export default function LeftNavigation({ active, onChange }) {
  return (
    <section
      aria-label="Main navigation"
      className="rounded-2xl border border-gray-300/70 bg-white-200/85 backdrop-blur-md shadow-lg shadow-gray-400/25 px-2 py-8 min-h-[80vh] flex flex-col justify-center"
    >
      <nav className="flex flex-col gap-2">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => onChange(id)}
            title={label}
            className={`relative w-10 h-10 rounded-xl flex items-center justify-center group transition-colors ${
              active === id
                ? 'bg-gray-50 text-gray-900 shadow-sm ring-1 ring-gray-300/80'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-300/45'
            }`}
          >
            <Icon className="w-5 h-5" />
            <span className="absolute left-12 bg-white/90 backdrop-blur-sm text-gray-700 px-2 py-1 rounded-lg text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none border border-gray-200/70 shadow-md z-50">
              {label}
            </span>
          </button>
        ))}
      </nav>
    </section>
  )
}

LeftNavigation.propTypes = {
  active: PropTypes.string,
  onChange: PropTypes.func.isRequired,
}

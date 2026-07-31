/**
 * Floating left nav — rounded pill; gray palette in both themes.
 */
import PropTypes from 'prop-types'
import { Moon, Sun } from 'lucide-react'
import { NAV_ITEMS } from '../../lib/constants'

const tipClass =
  'absolute left-12 px-2 py-1 rounded-lg text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 group-focus-visible:opacity-100 pointer-events-none border shadow-md z-50 bg-white/90 backdrop-blur-sm text-gray-700 border-gray-200/70'

export default function LeftNavigation({ active, onChange, theme = 'light', onToggleTheme }) {
  const isDark = theme === 'dark'

  return (
    <section
      aria-label="Main navigation"
      className={`rounded-xl border backdrop-blur-md shadow-md px-2 py-6 min-h-[80vh] flex flex-col ${
        isDark
          ? 'border-gray-700/80 bg-gray-900/90 shadow-black/40'
          : 'border-gray-300/70 bg-white/85'
      }`}
    >
      <nav className="flex flex-col gap-2 flex-1 justify-center">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => {
          const selected = active === id
          return (
            <button
              key={id}
              type="button"
              onClick={() => onChange(id)}
              title={label}
              aria-label={label}
              aria-current={selected ? 'page' : undefined}
              className={`relative w-10 h-10 rounded-xl flex items-center justify-center group transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 ${
                selected
                  ? 'bg-gray-50 text-gray-900 shadow-sm ring-1 ring-gray-300/80'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-300/45'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className={tipClass}>{label}</span>
            </button>
          )
        })}
      </nav>

      {onToggleTheme && (
        <button
          type="button"
          onClick={onToggleTheme}
          title={isDark ? 'Light theme' : 'Dark theme'}
          aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
          className="relative w-10 h-10 mt-4 rounded-xl flex items-center justify-center group transition-colors text-gray-600 hover:text-gray-900 hover:bg-gray-300/45 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400"
        >
          {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          <span className={tipClass}>{isDark ? 'Light' : 'Dark'}</span>
        </button>
      )}
    </section>
  )
}

LeftNavigation.propTypes = {
  active: PropTypes.string,
  onChange: PropTypes.func.isRequired,
  theme: PropTypes.oneOf(['light', 'dark']),
  onToggleTheme: PropTypes.func,
}

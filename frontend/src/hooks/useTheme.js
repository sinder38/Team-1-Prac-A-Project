/**
 * Persist light/dark on <html data-theme>.
 * No saved choice → follow OS prefers-color-scheme.
 */
import { useEffect, useState } from 'react'

export const THEME_KEY = 'mi-theme'

function systemTheme() {
  try {
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark'
  } catch {
    /* ignore */
  }
  return 'light'
}

export function readTheme() {
  try {
    const saved = localStorage.getItem(THEME_KEY)
    if (saved === 'dark' || saved === 'light') return saved
  } catch {
    /* private mode / blocked storage */
  }
  return systemTheme()
}

export function applyTheme(theme) {
  const next = theme === 'dark' ? 'dark' : 'light'
  const root = document.documentElement
  root.dataset.theme = next
  root.classList.toggle('dark', next === 'dark')
  root.style.colorScheme = next
  return next
}

applyTheme(readTheme())

export function useTheme() {
  const [theme, setTheme] = useState(readTheme)

  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  function toggleTheme() {
    setTheme(prev => {
      const next = prev === 'dark' ? 'light' : 'dark'
      try {
        localStorage.setItem(THEME_KEY, next)
      } catch {
        /* ignore */
      }
      return next
    })
  }

  return { theme, toggleTheme }
}

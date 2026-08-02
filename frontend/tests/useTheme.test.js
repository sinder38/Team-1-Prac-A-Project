import { describe, it, expect, beforeEach } from 'vitest'
import { applyTheme } from '../src/hooks/useTheme'

describe('applyTheme', () => {
  beforeEach(() => {
    document.documentElement.classList.remove('dark')
    delete document.documentElement.dataset.theme
  })

  it('sets data-theme and clears dark styles for light', () => {
    applyTheme('dark')
    expect(document.documentElement.dataset.theme).toBe('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(document.documentElement.style.colorScheme).toBe('dark')

    applyTheme('light')
    expect(document.documentElement.dataset.theme).toBe('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
    expect(document.documentElement.style.colorScheme).toBe('light')
  })
})

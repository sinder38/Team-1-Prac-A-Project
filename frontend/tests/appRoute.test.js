import { describe, it, expect, beforeEach } from 'vitest'
import { readPageFromUrl, syncUrl } from '../src/lib/appRoute'

describe('appRoute', () => {
  beforeEach(() => {
    window.history.replaceState(null, '', '/')
  })

  it('defaults page to dashboard', () => {
    expect(readPageFromUrl()).toBe('dashboard')
  })

  it('reads a valid page from the query string', () => {
    window.history.replaceState(null, '', '/?page=charts')
    expect(readPageFromUrl()).toBe('charts')
  })

  it('ignores unknown pages', () => {
    window.history.replaceState(null, '', '/?page=nope')
    expect(readPageFromUrl()).toBe('dashboard')
  })

  it('writes page and week into the URL', () => {
    syncUrl({ page: 'logs', week: '2026-W29' })
    const params = new URLSearchParams(window.location.search)
    expect(params.get('page')).toBe('logs')
    expect(params.get('week')).toBe('2026-W29')
  })
})

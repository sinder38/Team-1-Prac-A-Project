import { afterEach, describe, expect, it, vi } from 'vitest'

import { getAuthStatus, login, logout } from '../src/api/auth'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('authentication API', () => {
  it('loads the current public authentication status', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        authenticated: false,
        configured: true,
        username: null,
      }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const status = await getAuthStatus()

    expect(fetchMock).toHaveBeenCalledWith('/auth/status', undefined)
    expect(status).toEqual({
      isAuthenticated: false,
      isConfigured: true,
      username: null,
    })
  })

  it('sends credentials only in the login request body', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ authenticated: true, username: 'admin' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const status = await login('admin', 'secret')

    expect(fetchMock).toHaveBeenCalledWith(
      '/auth/login',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ username: 'admin', password: 'secret' }),
      }),
    )
    expect(status.isAuthenticated).toBe(true)
    expect(status.username).toBe('admin')
  })

  it('clears the session through the logout endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ authenticated: false }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const status = await logout()

    expect(fetchMock).toHaveBeenCalledWith(
      '/auth/logout',
      expect.objectContaining({ method: 'POST' }),
    )
    expect(status.isAuthenticated).toBe(false)
  })
})

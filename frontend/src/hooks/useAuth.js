import { useEffect, useState } from 'react'
import { getAuthStatus, login as apiLogin, logout as apiLogout } from '../api/auth'

const INITIAL_STATE = {
  isAuthenticated: false,
  isConfigured: true,
  username: null,
}

export function useAuth() {
  const [auth, setAuth] = useState(INITIAL_STATE)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getAuthStatus()
      .then(setAuth)
      .catch(() => setError('Could not check sign-in status.'))
      .finally(() => setLoading(false))
  }, [])

  async function login(username, password) {
    setError(null)
    try {
      const next = await apiLogin(username, password)
      setAuth(next)
      return next
    } catch (err) {
      setError(err.message || 'Sign in failed.')
      throw err
    }
  }

  async function logout() {
    setError(null)
    try {
      setAuth(await apiLogout())
    } catch (err) {
      setError(err.message || 'Sign out failed.')
      throw err
    }
  }

  return { ...auth, loading, error, login, logout }
}

import { useState } from 'react'
import PropTypes from 'prop-types'
import { Lock, LogIn, LogOut, X } from 'lucide-react'

export default function AuthControl({ auth }) {
  const [open, setOpen] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function submit(event) {
    event.preventDefault()
    setSubmitting(true)
    try {
      await auth.login(username, password)
      setPassword('')
      setOpen(false)
    } catch {
      // useAuth exposes the server error below the form.
    } finally {
      setSubmitting(false)
    }
  }

  async function signOut() {
    try {
      await auth.logout()
    } catch {
      // useAuth keeps the current session state and records the error.
    }
  }

  if (auth.loading) {
    return (
      <span className="flex items-center gap-1.5 text-xs text-gray-400">
        <Lock className="w-3.5 h-3.5" /> Checking access
      </span>
    )
  }

  if (auth.isAuthenticated) {
    return (
      <button
        type="button"
        onClick={signOut}
        title="Sign out"
        className="flex items-center gap-1.5 px-2 py-1.5 text-xs text-gray-600 hover:text-gray-900"
      >
        <span className="hidden sm:inline max-w-32 truncate">{auth.username}</span>
        <LogOut className="w-4 h-4" />
      </button>
    )
  }

  if (!auth.isConfigured) {
    return (
      <span
        title="Administrator login is not configured on the server"
        className="flex items-center gap-1.5 text-xs text-gray-400"
      >
        <Lock className="w-3.5 h-3.5" /> Read only
      </span>
    )
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen(value => !value)}
        aria-expanded={open}
        className="flex items-center gap-1.5 px-2 py-1.5 text-xs font-medium text-gray-600 hover:text-gray-900"
      >
        <LogIn className="w-4 h-4" /> Sign in
      </button>

      {open && (
        <form
          onSubmit={submit}
          className="absolute right-0 top-9 z-50 w-72 rounded-md border border-gray-200 bg-white p-4 shadow-lg"
        >
          <div className="mb-3 flex items-center justify-between">
            <p className="text-sm font-medium text-gray-900">Administrator sign in</p>
            <button
              type="button"
              onClick={() => setOpen(false)}
              title="Close"
              className="p-1 text-gray-400 hover:text-gray-700"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <label className="block text-xs font-medium text-gray-600">
            Username
            <input
              type="text"
              value={username}
              onChange={event => setUsername(event.target.value)}
              autoComplete="username"
              required
              className="mt-1 w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-gray-400 focus:outline-none"
            />
          </label>
          <label className="mt-3 block text-xs font-medium text-gray-600">
            Password
            <input
              type="password"
              value={password}
              onChange={event => setPassword(event.target.value)}
              autoComplete="current-password"
              required
              className="mt-1 w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-gray-400 focus:outline-none"
            />
          </label>
          {auth.error && <p className="mt-2 text-xs text-red-600">{auth.error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-md bg-gray-900 px-3 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
          >
            <LogIn className="w-4 h-4" /> {submitting ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      )}
    </div>
  )
}

AuthControl.propTypes = {
  auth: PropTypes.shape({
    error: PropTypes.string,
    isAuthenticated: PropTypes.bool,
    isConfigured: PropTypes.bool,
    loading: PropTypes.bool,
    login: PropTypes.func.isRequired,
    logout: PropTypes.func.isRequired,
    username: PropTypes.string,
  }).isRequired,
}

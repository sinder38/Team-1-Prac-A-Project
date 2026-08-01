import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import AuthControl from '../src/components/auth/AuthControl'

function guestAuth(overrides = {}) {
  return {
    error: null,
    isAuthenticated: false,
    isConfigured: true,
    loading: false,
    login: vi.fn().mockResolvedValue({}),
    logout: vi.fn().mockResolvedValue({}),
    username: null,
    ...overrides,
  }
}

describe('AuthControl', () => {
  it('submits the administrator credentials', async () => {
    const auth = guestAuth()
    const user = userEvent.setup()
    render(<AuthControl auth={auth} />)

    await user.click(screen.getByRole('button', { name: 'Sign in' }))
    await user.type(screen.getByLabelText('Username'), 'admin')
    await user.type(screen.getByLabelText('Password'), 'secret')
    await user.click(screen.getAllByRole('button', { name: 'Sign in' })[1])

    expect(auth.login).toHaveBeenCalledWith('admin', 'secret')
  })

  it('shows read-only status when credentials are not configured', () => {
    render(<AuthControl auth={guestAuth({ isConfigured: false })} />)

    expect(screen.getByText('Read only')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Sign in' })).not.toBeInTheDocument()
  })
})

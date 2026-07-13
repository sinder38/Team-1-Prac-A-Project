/**
 * Tests for the shared ErrorBanner (src/components/common/ErrorBanner.jsx).
 *
 * What this covers:
 *  - Renders nothing when there is no message (so callers can render it
 *    unconditionally without an empty red box appearing).
 *  - Shows the message text when one is provided.
 *  - Fires the onRetry / onDismiss callbacks, and only shows those buttons
 *    when their handlers are supplied.
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ErrorBanner from '../src/components/common/ErrorBanner'

describe('ErrorBanner', () => {
  it('renders nothing when there is no message', () => {
    const { container } = render(<ErrorBanner message={null} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('shows the error message', () => {
    render(<ErrorBanner message="Could not load data" />)
    expect(screen.getByText('Could not load data')).toBeInTheDocument()
  })

  it('only renders Retry / Dismiss when handlers are given', () => {
    const { rerender } = render(<ErrorBanner message="oops" />)
    expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /dismiss/i })).not.toBeInTheDocument()

    rerender(<ErrorBanner message="oops" onRetry={() => {}} onDismiss={() => {}} />)
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /dismiss/i })).toBeInTheDocument()
  })

  it('calls onRetry and onDismiss when their buttons are clicked', async () => {
    const onRetry = vi.fn()
    const onDismiss = vi.fn()
    render(<ErrorBanner message="oops" onRetry={onRetry} onDismiss={onDismiss} />)

    await userEvent.click(screen.getByRole('button', { name: /retry/i }))
    await userEvent.click(screen.getByRole('button', { name: /dismiss/i }))

    expect(onRetry).toHaveBeenCalledTimes(1)
    expect(onDismiss).toHaveBeenCalledTimes(1)
  })
})

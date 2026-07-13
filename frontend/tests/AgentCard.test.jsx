/**
 * Tests for the AgentCard component (src/components/agents/AgentCard.jsx).
 *
 * A representative component test: it renders the agent name, the parsed bias
 * badge and confidence, only reveals the raw output when `open`, and calls
 * `onToggle` when the toggle button is clicked. Also checks the placeholder
 * (empty) card. Proves the lib parsing wires up correctly in the UI.
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AgentCard, { AgentCardPlaceholder } from '../src/components/agents/AgentCard'

const DATA = {
  agent: 'Technical Agent',
  rawData: 'TECHNICAL BIAS: Bullish.\nCONFIDENCE: Medium.\nraw details here',
  metrics: [
    { label: 'Last Close', value: '7,554' },
    { label: 'EMA Condition', value: 'Zone 1 (Bullish)' },
  ],
}

describe('AgentCard', () => {
  it('renders the agent name, bias badge and confidence', () => {
    render(<AgentCard id="technical" data={DATA} open={false} onToggle={() => {}} />)
    expect(screen.getByText('Technical Agent')).toBeInTheDocument()
    expect(screen.getByText('Bullish')).toBeInTheDocument()
    expect(screen.getByText(/Confidence · Medium/)).toBeInTheDocument()
  })

  it('reveals raw output only when open', () => {
    const { rerender } = render(
      <AgentCard id="technical" data={DATA} open={false} onToggle={() => {}} />,
    )
    expect(screen.queryByText(/raw details here/)).not.toBeInTheDocument()
    rerender(<AgentCard id="technical" data={DATA} open onToggle={() => {}} />)
    expect(screen.getByText(/raw details here/)).toBeInTheDocument()
  })

  it('calls onToggle when the raw-output button is clicked', async () => {
    const onToggle = vi.fn()
    render(<AgentCard id="technical" data={DATA} open={false} onToggle={onToggle} />)
    await userEvent.click(screen.getByRole('button', { name: /view raw output/i }))
    expect(onToggle).toHaveBeenCalledTimes(1)
  })
})

describe('AgentCardPlaceholder', () => {
  it('shows an empty state', () => {
    render(<AgentCardPlaceholder id="macro" />)
    expect(screen.getByText('No output yet')).toBeInTheDocument()
    expect(screen.getByText('Macro Agent')).toBeInTheDocument()
  })
})

import { describe, expect, it } from 'vitest'
import { inferProviderMode } from '../src/lib/llmProvider'

const REGISTRY = [
  { key: 'nemotron', name: 'Nemotron', provider: 'openrouter' },
  { key: 'hy3', name: 'Hy3', provider: 'openrouter' },
  { key: 'gemm26', name: 'Gemm26', provider: 'openrouter' },
  { key: 'laguna', name: 'Laguna', provider: 'openrouter' },
  { key: 'llama3.2-3b', name: 'Llama3.2 3B', provider: 'ollama' },
]

describe('inferProviderMode', () => {
  it('picks openrouter for W29-style archive columns', () => {
    const mode = inferProviderMode(
      {
        models: [
          { name: 'Nemotron 3 Super 120B A12B' },
          { name: 'Hy3' },
          { name: 'Gemma 4 26B A4B It:Free' },
          { name: 'Laguna M.1' },
        ],
      },
      REGISTRY,
    )
    expect(mode).toBe('openrouter')
  })

  it('picks ollama when only local model columns are present', () => {
    const mode = inferProviderMode(
      { models: [{ name: 'Llama3.2 3B' }] },
      REGISTRY,
    )
    expect(mode).toBe('ollama')
  })

  it('returns null when there is no consensus', () => {
    expect(inferProviderMode(null, REGISTRY)).toBeNull()
    expect(inferProviderMode({ models: [] }, REGISTRY)).toBeNull()
  })
})

/**
 * Infer Local (Ollama) vs Real API (OpenRouter) from loaded LLM consensus.
 */

function normalizeModelToken(value) {
  return String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, '')
}

/**
 * @param {{ models?: { name?: string }[] } | null | undefined} llmComparison
 * @param {{ key: string, name?: string, provider?: string }[]} availableModels
 * @returns {'ollama' | 'openrouter' | null}
 */
export function inferProviderMode(llmComparison, availableModels = []) {
  const names = (llmComparison?.models || []).map(m => m.name).filter(Boolean)
  if (!names.length) return null

  const providers = []
  for (const name of names) {
    const n = normalizeModelToken(name)
    const hit = availableModels.find(m => {
      const key = normalizeModelToken(m.key)
      const label = normalizeModelToken(m.name)
      return (
        (key && n.includes(key)) ||
        (label && (n.includes(label) || label.includes(n)))
      )
    })
    if (hit) providers.push(hit.provider || 'openrouter')
  }

  if (providers.length) {
    return providers.some(p => p === 'openrouter') ? 'openrouter' : 'ollama'
  }

  // No registry match: llama/ollama columns -> local; otherwise real API.
  return names.every(n => /llama|ollama/i.test(n)) ? 'ollama' : 'openrouter'
}

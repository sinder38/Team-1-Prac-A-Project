/**
 * TODO (backend task): HTTP helpers for the FastAPI backend.
 * Use fetch against API_BASE. In dev, proxy /api → localhost:8000 in vite.config.js.
 */
export const API_BASE = '/api'

// TODO: implement when backend is connected
export async function getJson(url, options) {
  const res = await fetch(url, options)
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail || res.statusText)
  }
  return res.json()
}

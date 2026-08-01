/**
 * HTTP helpers for the Flask backend (see backend/server). Dev requests hit
 * /stages/* and /artifacts/* directly, proxied to localhost:5000 by Vite.
 */

// Vite's base path (e.g. "/" in dev, "/market-intelligence/" in a subpath
// build). Prefixing absolute API paths with it lets the app be hosted under a
// sub-path without the backend needing to know its public mount point.
const BASE = import.meta.env.BASE_URL.replace(/\/+$/, '')

/** Prefix an absolute ("/…") API path with the app's base path. Relative or
 *  fully-qualified URLs are returned unchanged. */
export function apiUrl(path) {
  return path.startsWith('/') ? `${BASE}${path}` : path
}

export async function getJson(url, options) {
  const res = await fetch(apiUrl(url), options)
  const body = await res.json().catch(() => ({ error: res.statusText }))
  if (!res.ok) {
    throw new Error(body.error || res.statusText)
  }
  return body
}

export async function postJson(url, body) {
  return getJson(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

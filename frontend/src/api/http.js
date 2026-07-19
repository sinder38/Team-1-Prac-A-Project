/**
 * HTTP helpers for the Flask backend (see backend/server). Dev requests hit
 * /stages/* and /artifacts/* directly, proxied to localhost:5000 by Vite.
 */
export async function getJson(url, options) {
  const res = await fetch(url, options)
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

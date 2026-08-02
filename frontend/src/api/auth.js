import { getJson, postJson } from './http'

function authState(data) {
  return {
    isAuthenticated: Boolean(data.authenticated),
    isConfigured: Boolean(data.configured ?? true),
    username: data.username || null,
  }
}

export async function getAuthStatus() {
  return authState(await getJson('/auth/status'))
}

export async function login(username, password) {
  const data = await postJson('/auth/login', { username, password })
  return authState({ ...data, configured: true })
}

export async function logout() {
  await postJson('/auth/logout', {})
  return {
    isAuthenticated: false,
    isConfigured: true,
    username: null,
  }
}

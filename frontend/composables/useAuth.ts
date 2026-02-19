interface User {
  id: string
  username: string
  display_name: string | null
  email: string | null
  avatar_url: string | null
  is_admin: boolean
  last_login_at: string | null
}

interface OidcConfig {
  client_id: string
  redirect_uri: string
  scope: string
  flow_slug: string
}

const BRIDGE_URL = 'https://auth.namgun.or.kr/portal-bridge/'
const BRIDGE_ORIGIN = 'https://auth.namgun.or.kr'
const BRIDGE_CALLBACK = 'https://auth.namgun.or.kr/portal-bridge/callback'

function generateCodeVerifier(): string {
  const array = new Uint8Array(64)
  crypto.getRandomValues(array)
  return btoa(String.fromCharCode(...array))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/g, '')
}

async function generateCodeChallenge(verifier: string): Promise<string> {
  const data = new TextEncoder().encode(verifier)
  const digest = await crypto.subtle.digest('SHA-256', data)
  return btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/g, '')
}

function generateState(): string {
  const array = new Uint8Array(32)
  crypto.getRandomValues(array)
  return btoa(String.fromCharCode(...array))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/g, '')
}

export const useAuth = () => {
  const user = useState<User | null>('auth-user', () => null)
  const loading = useState<boolean>('auth-loading', () => true)

  const fetchUser = async () => {
    try {
      loading.value = true
      const data = await $fetch<User>('/api/auth/me', { credentials: 'include' })
      user.value = data
    } catch {
      user.value = null
    } finally {
      loading.value = false
    }
  }

  const nativeLogin = async (username: string, password: string): Promise<void> => {
    // 1. Set up bridge-ready listener BEFORE opening popup (avoid race condition)
    const bridgeReady = new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error('Bridge load timeout')), 15000)
      function onReady(event: MessageEvent) {
        if (event.origin !== BRIDGE_ORIGIN) return
        if (event.data?.type !== 'portal-bridge-ready') return
        clearTimeout(timeout)
        window.removeEventListener('message', onReady)
        resolve()
      }
      window.addEventListener('message', onReady)
    })

    // 2. Open popup SYNCHRONOUSLY (before any await) to avoid popup blockers
    //    Popup is top-level context → Authentik cookies are first-party → SSO works
    const popup = window.open(BRIDGE_URL, '_portal_auth', 'width=1,height=1,left=-100,top=-100')
    if (!popup) throw new Error('팝업이 차단되었습니다. 팝업을 허용해주세요.')

    try {
      // 3. Wait for bridge ready + fetch config concurrently
      const [, config] = await Promise.all([
        bridgeReady,
        $fetch<OidcConfig>('/api/auth/oidc-config'),
      ])

      // 4. Generate PKCE
      const codeVerifier = generateCodeVerifier()
      const codeChallenge = await generateCodeChallenge(codeVerifier)
      const state = generateState()

      const oauthParams = new URLSearchParams({
        response_type: 'code',
        client_id: config.client_id,
        redirect_uri: BRIDGE_CALLBACK,
        scope: config.scope,
        state,
        code_challenge: codeChallenge,
        code_challenge_method: 'S256',
      }).toString()

      // 5. Send credentials to popup bridge
      popup.postMessage({
        type: 'portal-login',
        username,
        password,
        oauthParams,
        flowSlug: config.flow_slug,
      }, BRIDGE_ORIGIN)

      // 6. Wait for response
      const result = await new Promise<{ code: string }>((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error('Login timeout')), 30000)
        function handler(event: MessageEvent) {
          if (event.origin !== BRIDGE_ORIGIN) return
          if (event.data?.type !== 'portal-login-result') return
          clearTimeout(timeout)
          window.removeEventListener('message', handler)
          if (event.data.success) {
            resolve({ code: event.data.code })
          } else {
            reject(new Error(event.data.error || 'Login failed'))
          }
        }
        window.addEventListener('message', handler)
      })

      // 7. Exchange code for portal session
      await $fetch('/api/auth/native-callback', {
        method: 'POST',
        body: {
          code: result.code,
          code_verifier: codeVerifier,
        },
      })

      // 8. Fetch user
      await fetchUser()

    } finally {
      popup.close()
    }
  }

  const logout = async () => {
    await $fetch('/api/auth/logout', { method: 'POST' })
    user.value = null
    navigateTo('/login')
  }

  return { user, loading, fetchUser, nativeLogin, logout }
}

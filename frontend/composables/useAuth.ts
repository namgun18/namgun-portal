interface User {
  id: string
  username: string
  display_name: string | null
  email: string | null
  avatar_url: string | null
  is_admin: boolean
  last_login_at: string | null
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
    await $fetch('/api/auth/login', {
      method: 'POST',
      body: { username, password },
    })
    await fetchUser()
  }

  const logout = async () => {
    await $fetch('/api/auth/logout', { method: 'POST' })
    user.value = null
    navigateTo('/login')
  }

  return { user, loading, fetchUser, nativeLogin, logout }
}

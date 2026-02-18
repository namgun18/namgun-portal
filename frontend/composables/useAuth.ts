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

  const login = () => {
    navigateTo('/api/auth/login', { external: true })
  }

  const logout = async () => {
    // POST to logout, then follow redirect
    navigateTo('/api/auth/logout', { external: true })
  }

  return { user, loading, fetchUser, login, logout }
}

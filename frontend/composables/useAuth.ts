interface User {
  id: string
  username: string
  display_name: string | null
  email: string | null
  avatar_url: string | null
  recovery_email: string | null
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

  const nativeLogin = async (username: string, password: string, rememberMe: boolean = false): Promise<void> => {
    await $fetch('/api/auth/login', {
      method: 'POST',
      body: { username, password, remember_me: rememberMe },
    })
    await fetchUser()
  }

  const logout = async () => {
    await $fetch('/api/auth/logout', { method: 'POST' })
    user.value = null
    navigateTo('/login')
  }

  const register = async (data: {
    username: string
    password: string
    display_name: string
    recovery_email: string
  }): Promise<{ message: string }> => {
    return await $fetch('/api/auth/register', {
      method: 'POST',
      body: data,
    })
  }

  const updateProfile = async (data: {
    display_name?: string
    recovery_email?: string
  }): Promise<void> => {
    await $fetch('/api/auth/profile', {
      method: 'PATCH',
      body: data,
    })
    await fetchUser()
  }

  const changePassword = async (
    currentPassword: string,
    newPassword: string
  ): Promise<void> => {
    await $fetch('/api/auth/change-password', {
      method: 'POST',
      body: { current_password: currentPassword, new_password: newPassword },
    })
  }

  const forgotPassword = async (username: string): Promise<{ message: string }> => {
    return await $fetch('/api/auth/forgot-password', {
      method: 'POST',
      body: { username },
    })
  }

  return {
    user,
    loading,
    fetchUser,
    nativeLogin,
    logout,
    register,
    updateProfile,
    changePassword,
    forgotPassword,
  }
}

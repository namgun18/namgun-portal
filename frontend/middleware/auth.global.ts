export default defineNuxtRouteMiddleware((to) => {
  // Demo mode: skip auth entirely
  const config = useRuntimeConfig()
  if (config.public.demoMode) return

  const { user, loading } = useAuth()

  // Allow public pages
  const publicPages = ['/login', '/register', '/forgot-password', '/reset-password', '/verify-email']
  if (publicPages.includes(to.path)) return

  // If not loading and no user, redirect to login
  if (!loading.value && !user.value) {
    return navigateTo('/login')
  }
})

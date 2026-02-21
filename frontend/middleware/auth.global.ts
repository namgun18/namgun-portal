export default defineNuxtRouteMiddleware((to) => {
  const { user, loading } = useAuth()

  // Allow public pages
  const publicPages = ['/login', '/callback', '/register', '/forgot-password']
  if (publicPages.includes(to.path)) return

  // If not loading and no user, redirect to login
  if (!loading.value && !user.value) {
    return navigateTo('/login')
  }
})

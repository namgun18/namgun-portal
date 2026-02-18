export default defineNuxtPlugin(async () => {
  const { fetchUser } = useAuth()
  // Hydrate user state on app init (SSR + client)
  await fetchUser()
})

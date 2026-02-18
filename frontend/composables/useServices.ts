interface ServiceStatus {
  name: string
  url: string | null
  status: 'ok' | 'down' | 'checking'
  response_ms: number | null
  internal_only: boolean
}

export const useServices = () => {
  const services = useState<ServiceStatus[]>('services', () => [])
  const loading = useState<boolean>('services-loading', () => true)

  const fetchServices = async () => {
    try {
      loading.value = true
      const data = await $fetch<ServiceStatus[]>('/api/services/status', {
        credentials: 'include',
      })
      services.value = data
    } catch {
      // Keep previous data on error
    } finally {
      loading.value = false
    }
  }

  return { services, loading, fetchServices }
}

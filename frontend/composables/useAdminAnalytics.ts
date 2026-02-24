export interface AnalyticsOverview {
  total_visits: number
  unique_ips: number
  authenticated_visits: number
  unauthenticated_visits: number
  avg_response_time_ms: number
}

export interface DailyVisit {
  date: string
  total: number
  authenticated: number
  unauthenticated: number
}

export interface TopPage {
  path: string
  count: number
}

export interface CountryStats {
  country_code: string | null
  country_name: string | null
  count: number
}

export interface ServiceUsage {
  service: string
  count: number
}

export interface ActiveUser {
  user_id: string
  username: string
  display_name: string | null
  path: string
  ip_address: string
  country_code: string | null
  last_seen: string
}

export interface RecentLogin {
  user_id: string
  username: string
  display_name: string | null
  ip_address: string
  country_code: string | null
  country_name: string | null
  login_at: string
}

export interface AccessLogEntry {
  id: string
  ip_address: string
  method: string
  path: string
  status_code: number
  response_time_ms: number
  browser: string | null
  os: string | null
  device: string | null
  country_code: string | null
  country_name: string | null
  user_id: string | null
  username: string | null
  service: string | null
  created_at: string
}

export interface AccessLogPage {
  logs: AccessLogEntry[]
  total: number
  page: number
  limit: number
}

export interface GitActivityItem {
  repo_name: string
  repo_full_name: string
  event_type: string
  title: string
  user: string
  created_at: string
}

export interface GitStats {
  total_repos: number
  total_users: number
  total_issues: number
  total_pulls: number
}

export function countryFlag(code: string | null): string {
  if (!code || code.length !== 2) return '\u{1F310}'
  return String.fromCodePoint(...[...code.toUpperCase()].map(c => 0x1F1E6 - 65 + c.charCodeAt(0)))
}

export function useAdminAnalytics() {
  const overview = ref<AnalyticsOverview | null>(null)
  const dailyVisits = ref<DailyVisit[]>([])
  const topPages = ref<TopPage[]>([])
  const countries = ref<CountryStats[]>([])
  const serviceUsage = ref<ServiceUsage[]>([])
  const activeUsers = ref<ActiveUser[]>([])
  const recentLogins = ref<RecentLogin[]>([])
  const accessLogs = ref<AccessLogPage | null>(null)
  const gitActivity = ref<GitActivityItem[]>([])
  const gitStats = ref<GitStats | null>(null)
  const loading = ref(false)

  async function fetchOverview(period = 'today') {
    try {
      overview.value = await $fetch<AnalyticsOverview>('/api/admin/analytics/overview', { params: { period } })
    } catch { overview.value = null }
  }

  async function fetchDailyVisits(days = 30) {
    try {
      dailyVisits.value = await $fetch<DailyVisit[]>('/api/admin/analytics/daily-visits', { params: { days } })
    } catch { dailyVisits.value = [] }
  }

  async function fetchTopPages(period = 'today', limit = 10) {
    try {
      topPages.value = await $fetch<TopPage[]>('/api/admin/analytics/top-pages', { params: { period, limit } })
    } catch { topPages.value = [] }
  }

  async function fetchCountries(period = 'today', limit = 15) {
    try {
      countries.value = await $fetch<CountryStats[]>('/api/admin/analytics/countries', { params: { period, limit } })
    } catch { countries.value = [] }
  }

  async function fetchServiceUsage(period = 'today') {
    try {
      serviceUsage.value = await $fetch<ServiceUsage[]>('/api/admin/analytics/service-usage', { params: { period } })
    } catch { serviceUsage.value = [] }
  }

  async function fetchActiveUsers() {
    try {
      activeUsers.value = await $fetch<ActiveUser[]>('/api/admin/analytics/active-users')
    } catch { activeUsers.value = [] }
  }

  async function fetchRecentLogins(limit = 20) {
    try {
      recentLogins.value = await $fetch<RecentLogin[]>('/api/admin/analytics/recent-logins', { params: { limit } })
    } catch { recentLogins.value = [] }
  }

  async function fetchAccessLogs(page = 1, limit = 50, service?: string, userId?: string) {
    try {
      const params: Record<string, any> = { page, limit }
      if (service) params.service = service
      if (userId) params.user_id = userId
      accessLogs.value = await $fetch<AccessLogPage>('/api/admin/analytics/access-logs', { params })
    } catch { accessLogs.value = null }
  }

  async function fetchGitActivity() {
    try {
      gitActivity.value = await $fetch<GitActivityItem[]>('/api/admin/analytics/git-activity')
    } catch { gitActivity.value = [] }
  }

  async function fetchGitStats() {
    try {
      gitStats.value = await $fetch<GitStats>('/api/admin/analytics/git-stats')
    } catch { gitStats.value = null }
  }

  async function fetchAll(period = 'today') {
    loading.value = true
    const days = period === '30d' ? 30 : period === '7d' ? 7 : 1
    await Promise.all([
      fetchOverview(period),
      fetchDailyVisits(days),
      fetchTopPages(period),
      fetchCountries(period),
      fetchServiceUsage(period),
      fetchActiveUsers(),
      fetchRecentLogins(),
      fetchGitActivity(),
      fetchGitStats(),
    ])
    loading.value = false
  }

  return {
    overview, dailyVisits, topPages, countries, serviceUsage,
    activeUsers, recentLogins, accessLogs, gitActivity, gitStats,
    loading,
    fetchOverview, fetchDailyVisits, fetchTopPages, fetchCountries,
    fetchServiceUsage, fetchActiveUsers, fetchRecentLogins,
    fetchAccessLogs, fetchAll, fetchGitActivity, fetchGitStats,
  }
}

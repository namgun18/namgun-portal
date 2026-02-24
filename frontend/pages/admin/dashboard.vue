<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { user } = useAuth()
const route = useRoute()

watch(user, (u) => {
  if (u && !u.is_admin) navigateTo('/')
}, { immediate: true })

const {
  overview, dailyVisits, topPages, countries, serviceUsage,
  activeUsers, recentLogins, accessLogs, gitActivity, gitStats,
  loading,
  fetchAll, fetchAccessLogs,
} = useAdminAnalytics()

const period = ref<'today' | '7d' | '30d'>('today')

const logService = ref<string | undefined>()
const logPage = ref(1)

async function changePeriod(p: 'today' | '7d' | '30d') {
  period.value = p
  await fetchAll(p)
}

function onLogPage(p: number) {
  logPage.value = p
  fetchAccessLogs(p, 50, logService.value)
}

function onLogFilter(service: string | undefined) {
  logService.value = service
  logPage.value = 1
  fetchAccessLogs(1, 50, service)
}

onMounted(async () => {
  await fetchAll(period.value)
  await fetchAccessLogs(1, 50)
})
</script>

<template>
  <div v-if="user?.is_admin" class="h-full overflow-auto px-4 sm:px-6 lg:px-8 py-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">관리 대시보드</h1>
        <p class="text-muted-foreground mt-1">방문자 분석 및 서비스 현황</p>
      </div>
    </div>

    <!-- Sub tabs + Period filter -->
    <div class="flex items-center justify-between mb-6 border-b">
      <div class="flex gap-1">
        <NuxtLink
          to="/admin/dashboard"
          class="px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px"
          :class="route.path === '/admin/dashboard'
            ? 'border-primary text-primary'
            : 'border-transparent text-muted-foreground hover:text-foreground'"
        >
          대시보드
        </NuxtLink>
        <NuxtLink
          to="/admin/users"
          class="px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px border-transparent text-muted-foreground hover:text-foreground"
        >
          사용자 관리
        </NuxtLink>
      </div>
      <div class="flex gap-1 mb-1">
        <button
          v-for="p in (['today', '7d', '30d'] as const)"
          :key="p"
          @click="changePeriod(p)"
          class="px-3 py-1 text-xs font-medium rounded-md transition-colors"
          :class="period === p
            ? 'bg-primary text-primary-foreground'
            : 'text-muted-foreground hover:bg-accent'"
        >
          {{ p === 'today' ? '오늘' : p === '7d' ? '7일' : '30일' }}
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <svg class="h-6 w-6 animate-spin text-muted-foreground" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>

    <div v-else class="space-y-4">
      <!-- Overview cards -->
      <AdminAnalyticsOverview :data="overview" />

      <!-- Charts row 1: Daily + Countries -->
      <div class="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div class="lg:col-span-3">
          <AdminAnalyticsDailyChart :data="dailyVisits" />
        </div>
        <div class="lg:col-span-2">
          <AdminAnalyticsCountries :data="countries" />
        </div>
      </div>

      <!-- Charts row 2: Top Pages + Service Usage -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <AdminAnalyticsTopPages :data="topPages" />
        <AdminAnalyticsServiceUsage :data="serviceUsage" />
      </div>

      <!-- Row 3: Active Users + Recent Logins -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <AdminAnalyticsActiveUsers :data="activeUsers" />
        <AdminAnalyticsRecentLogins :data="recentLogins" />
      </div>

      <!-- Row 4: Git Activity -->
      <AdminAnalyticsGitActivity :activity="gitActivity" :stats="gitStats" />

      <!-- Row 5: Access Logs -->
      <AdminAnalyticsAccessLogs
        :data="accessLogs"
        @page="onLogPage"
        @filter="onLogFilter"
      />
    </div>
  </div>
</template>

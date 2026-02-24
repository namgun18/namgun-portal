<script setup lang="ts">
import { countryFlag, type RecentLogin } from '~/composables/useAdminAnalytics'

defineProps<{ data: RecentLogin[] }>()

function timeAgo(iso: string) {
  if (!iso) return '-'
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '방금'
  if (mins < 60) return `${mins}분 전`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}시간 전`
  return `${Math.floor(hours / 24)}일 전`
}

function maskIp(ip: string) {
  const parts = ip.split('.')
  if (parts.length === 4) return `${parts[0]}.${parts[1]}.x.x`
  return ip.length > 10 ? ip.slice(0, 10) + '...' : ip
}
</script>

<template>
  <div class="rounded-lg border bg-card p-4">
    <h3 class="text-sm font-medium text-muted-foreground mb-3">최근 로그인</h3>
    <div v-if="data.length === 0" class="text-sm text-muted-foreground py-4 text-center">
      로그인 기록 없음
    </div>
    <div v-else class="space-y-2">
      <div
        v-for="(l, i) in data.slice(0, 10)"
        :key="i"
        class="flex items-center justify-between text-sm py-1.5 border-b last:border-0"
      >
        <div class="flex items-center gap-2 min-w-0">
          <span>{{ countryFlag(l.country_code) }}</span>
          <span class="font-medium truncate">{{ l.display_name || l.username }}</span>
          <span class="text-muted-foreground text-xs">{{ maskIp(l.ip_address) }}</span>
        </div>
        <span class="text-xs text-muted-foreground shrink-0 ml-2">{{ timeAgo(l.login_at) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { countryFlag, type ActiveUser } from '~/composables/useAdminAnalytics'

defineProps<{ data: ActiveUser[] }>()

function timeAgo(iso: string) {
  if (!iso) return '-'
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '방금'
  return `${mins}분 전`
}
</script>

<template>
  <div class="rounded-lg border bg-card p-4">
    <h3 class="text-sm font-medium text-muted-foreground mb-3">활성 사용자 (5분 이내)</h3>
    <div v-if="data.length === 0" class="text-sm text-muted-foreground py-4 text-center">
      현재 활성 사용자 없음
    </div>
    <div v-else class="space-y-2">
      <div
        v-for="u in data"
        :key="u.user_id"
        class="flex items-center justify-between text-sm py-1.5 border-b last:border-0"
      >
        <div class="flex items-center gap-2 min-w-0">
          <span>{{ countryFlag(u.country_code) }}</span>
          <span class="font-medium truncate">{{ u.display_name || u.username }}</span>
          <span class="text-muted-foreground truncate">{{ u.path }}</span>
        </div>
        <span class="text-xs text-muted-foreground shrink-0 ml-2">{{ timeAgo(u.last_seen) }}</span>
      </div>
    </div>
  </div>
</template>

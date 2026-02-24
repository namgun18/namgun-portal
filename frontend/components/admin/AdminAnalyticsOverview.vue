<script setup lang="ts">
import type { AnalyticsOverview } from '~/composables/useAdminAnalytics'

const props = defineProps<{ data: AnalyticsOverview | null }>()

const stats = computed(() => {
  if (!props.data) return []
  return [
    { label: '총 방문', value: props.data.total_visits.toLocaleString() },
    { label: '유니크 방문자', value: props.data.unique_ips.toLocaleString() },
    { label: '인증 방문', value: props.data.authenticated_visits.toLocaleString() },
    { label: '평균 응답시간', value: `${props.data.avg_response_time_ms}ms` },
  ]
})
</script>

<template>
  <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
    <div
      v-for="s in stats"
      :key="s.label"
      class="rounded-lg border bg-card p-4"
    >
      <div class="text-sm text-muted-foreground">{{ s.label }}</div>
      <div class="text-2xl font-bold mt-1">{{ s.value }}</div>
    </div>
  </div>
</template>

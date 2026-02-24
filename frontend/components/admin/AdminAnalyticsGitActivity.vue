<script setup lang="ts">
import type { GitActivityItem, GitStats } from '~/composables/useAdminAnalytics'

defineProps<{
  activity: GitActivityItem[]
  stats: GitStats | null
}>()

const eventIcons: Record<string, string> = {
  push: 'commit',
  issue: 'issue',
  pull_request: 'PR',
}

const eventColors: Record<string, string> = {
  push: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  issue: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  pull_request: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
}

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
</script>

<template>
  <div class="rounded-lg border bg-card p-4">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-medium text-muted-foreground">Git 활동</h3>
      <div v-if="stats" class="flex gap-3 text-xs text-muted-foreground">
        <span>저장소 {{ stats.total_repos }}</span>
        <span>이슈 {{ stats.total_issues }}</span>
        <span>PR {{ stats.total_pulls }}</span>
      </div>
    </div>
    <div v-if="activity.length === 0" class="text-sm text-muted-foreground py-4 text-center">
      Git 활동 없음
    </div>
    <div v-else class="space-y-2">
      <div
        v-for="(item, i) in activity.slice(0, 10)"
        :key="i"
        class="flex items-start gap-2 text-sm py-1.5 border-b last:border-0"
      >
        <span
          class="shrink-0 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium mt-0.5"
          :class="eventColors[item.event_type] || 'bg-gray-100 text-gray-600'"
        >
          {{ eventIcons[item.event_type] || item.event_type }}
        </span>
        <div class="min-w-0 flex-1">
          <div class="truncate">
            <span class="text-muted-foreground">{{ item.repo_name }}</span>
            <span class="mx-1 text-muted-foreground">/</span>
            <span>{{ item.title }}</span>
          </div>
          <div class="text-xs text-muted-foreground">
            {{ item.user }} &middot; {{ timeAgo(item.created_at) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { countryFlag, type AccessLogPage } from '~/composables/useAdminAnalytics'

const props = defineProps<{
  data: AccessLogPage | null
}>()

const emit = defineEmits<{
  (e: 'page', page: number): void
  (e: 'filter', service: string | undefined): void
}>()

const serviceFilter = ref<string>('')

const services = ['', 'mail', 'calendar', 'contacts', 'files', 'meetings', 'git', 'lab', 'admin', 'auth']
const serviceLabels: Record<string, string> = {
  '': '전체', mail: '메일', calendar: '캘린더', contacts: '연락처', files: '파일',
  meetings: '회의', git: 'Git', lab: 'Lab', admin: '관리', auth: '인증',
}

function onFilterChange() {
  emit('filter', serviceFilter.value || undefined)
}

function formatTime(iso: string) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('ko-KR', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

function statusColor(code: number) {
  if (code < 300) return 'text-green-600 dark:text-green-400'
  if (code < 400) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-red-600 dark:text-red-400'
}

const totalPages = computed(() => {
  if (!props.data) return 0
  return Math.ceil(props.data.total / props.data.limit)
})
</script>

<template>
  <div class="rounded-lg border bg-card p-4">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-medium text-muted-foreground">접속 로그</h3>
      <select
        v-model="serviceFilter"
        @change="onFilterChange"
        class="text-xs border rounded px-2 py-1 bg-background"
      >
        <option v-for="s in services" :key="s" :value="s">{{ serviceLabels[s] || s }}</option>
      </select>
    </div>

    <div v-if="!data || data.logs.length === 0" class="text-sm text-muted-foreground py-4 text-center">
      로그 없음
    </div>
    <div v-else class="overflow-x-auto">
      <table class="w-full text-xs">
        <thead>
          <tr class="border-b">
            <th class="text-left py-2 px-2 font-medium text-muted-foreground">시간</th>
            <th class="text-left py-2 px-2 font-medium text-muted-foreground">IP</th>
            <th class="text-left py-2 px-2 font-medium text-muted-foreground">국가</th>
            <th class="text-left py-2 px-2 font-medium text-muted-foreground">경로</th>
            <th class="text-left py-2 px-2 font-medium text-muted-foreground">상태</th>
            <th class="text-left py-2 px-2 font-medium text-muted-foreground">응답</th>
            <th class="text-left py-2 px-2 font-medium text-muted-foreground">브라우저</th>
            <th class="text-left py-2 px-2 font-medium text-muted-foreground">사용자</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in data.logs" :key="log.id" class="border-b last:border-0 hover:bg-accent/30">
            <td class="py-1.5 px-2 text-muted-foreground whitespace-nowrap">{{ formatTime(log.created_at) }}</td>
            <td class="py-1.5 px-2 font-mono">{{ log.ip_address }}</td>
            <td class="py-1.5 px-2">{{ countryFlag(log.country_code) }}</td>
            <td class="py-1.5 px-2 max-w-[200px] truncate" :title="log.path">{{ log.method }} {{ log.path }}</td>
            <td class="py-1.5 px-2 font-mono" :class="statusColor(log.status_code)">{{ log.status_code }}</td>
            <td class="py-1.5 px-2 text-muted-foreground">{{ log.response_time_ms }}ms</td>
            <td class="py-1.5 px-2 text-muted-foreground">{{ log.browser || '-' }}</td>
            <td class="py-1.5 px-2">{{ log.username || '-' }}</td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-between mt-3 pt-3 border-t">
        <span class="text-xs text-muted-foreground">
          {{ data.total.toLocaleString() }}건 중 {{ ((data.page - 1) * data.limit) + 1 }}-{{ Math.min(data.page * data.limit, data.total) }}
        </span>
        <div class="flex gap-1">
          <button
            :disabled="data.page <= 1"
            @click="emit('page', data.page - 1)"
            class="px-2 py-1 text-xs rounded border hover:bg-accent disabled:opacity-50"
          >
            이전
          </button>
          <button
            :disabled="data.page >= totalPages"
            @click="emit('page', data.page + 1)"
            class="px-2 py-1 text-xs rounded border hover:bg-accent disabled:opacity-50"
          >
            다음
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

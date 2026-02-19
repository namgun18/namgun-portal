<script setup lang="ts">
import type { Recording } from '~/composables/useMeetings'

defineProps<{
  recordings: Recording[]
  loading: boolean
  isAdmin: boolean
}>()

const emit = defineEmits<{
  delete: [recordId: string]
}>()

function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}

function formatTime(ts: string): string {
  if (!ts || ts === '0') return ''
  try {
    return new Date(parseInt(ts)).toLocaleString('ko-KR')
  } catch {
    return ''
  }
}
</script>

<template>
  <div>
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-8">
      <div class="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Empty -->
    <div v-else-if="recordings.length === 0" class="text-center py-8 text-sm text-muted-foreground">
      녹화된 회의가 없습니다.
    </div>

    <!-- List -->
    <div v-else class="divide-y">
      <div
        v-for="rec in recordings"
        :key="rec.recordID"
        class="flex items-center justify-between gap-3 px-4 py-3 hover:bg-muted/50 transition-colors"
      >
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 shrink-0 text-muted-foreground">
              <circle cx="12" cy="12" r="10" /><polygon points="10 8 16 12 10 16 10 8" />
            </svg>
            <span class="font-medium text-sm truncate">{{ rec.name || rec.meetingID }}</span>
            <span
              class="shrink-0 px-1.5 py-0.5 text-[10px] font-medium rounded"
              :class="rec.state === 'published'
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'"
            >
              {{ rec.state === 'published' ? '게시됨' : rec.state }}
            </span>
          </div>
          <div class="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
            <span v-if="formatTime(rec.startTime)">{{ formatTime(rec.startTime) }}</span>
            <span v-if="rec.size">{{ formatSize(rec.size) }}</span>
          </div>
        </div>

        <div class="flex items-center gap-1.5 shrink-0">
          <a
            v-if="rec.playbackUrl"
            :href="rec.playbackUrl"
            target="_blank"
            class="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-md border hover:bg-accent transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            재생
          </a>
          <button
            v-if="isAdmin"
            @click="emit('delete', rec.recordID)"
            class="inline-flex items-center justify-center h-7 w-7 rounded-md text-destructive hover:bg-destructive/10 transition-colors"
            title="삭제"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5">
              <polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

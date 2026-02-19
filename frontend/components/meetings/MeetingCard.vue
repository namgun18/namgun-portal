<script setup lang="ts">
import type { Meeting } from '~/composables/useMeetings'

const props = defineProps<{
  meeting: Meeting
  isAdmin: boolean
}>()

const emit = defineEmits<{
  join: [meetingId: string]
  end: [meetingId: string]
  select: [meetingId: string]
}>()

const createdAt = computed(() => {
  if (!props.meeting.createTime || props.meeting.createTime === '0') return ''
  try {
    return new Date(parseInt(props.meeting.createTime)).toLocaleString('ko-KR')
  } catch {
    return ''
  }
})
</script>

<template>
  <div
    class="group border rounded-lg p-4 hover:shadow-md transition-all cursor-pointer bg-card"
    @click="emit('select', meeting.meetingID)"
  >
    <div class="flex items-start justify-between gap-2">
      <div class="min-w-0 flex-1">
        <h3 class="font-medium truncate">{{ meeting.meetingName }}</h3>
        <p v-if="createdAt" class="text-xs text-muted-foreground mt-1">{{ createdAt }}</p>
      </div>
      <span
        class="shrink-0 inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full"
        :class="meeting.running
          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
          : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'"
      >
        <span class="h-1.5 w-1.5 rounded-full" :class="meeting.running ? 'bg-green-500' : 'bg-gray-400'" />
        {{ meeting.running ? '진행 중' : '대기' }}
      </span>
    </div>

    <div class="flex items-center gap-3 mt-3 text-sm text-muted-foreground">
      <span class="inline-flex items-center gap-1">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5">
          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
        {{ meeting.participantCount }}명
      </span>
      <span class="inline-flex items-center gap-1">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
        {{ meeting.moderatorCount }}명
      </span>
    </div>

    <div class="flex items-center gap-2 mt-3">
      <button
        @click.stop="emit('join', meeting.meetingID)"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5">
          <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" /><polyline points="10 17 15 12 10 7" /><line x1="15" y1="12" x2="3" y2="12" />
        </svg>
        참가
      </button>
      <button
        v-if="isAdmin && meeting.running"
        @click.stop="emit('end', meeting.meetingID)"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md border border-destructive text-destructive hover:bg-destructive hover:text-destructive-foreground transition-colors"
      >
        종료
      </button>
    </div>
  </div>
</template>

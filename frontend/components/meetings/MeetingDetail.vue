<script setup lang="ts">
import type { MeetingDetail } from '~/composables/useMeetings'

const props = defineProps<{
  meeting: MeetingDetail
  isAdmin: boolean
}>()

const emit = defineEmits<{
  join: [meetingId: string]
  end: [meetingId: string]
  close: []
}>()

const startedAt = computed(() => {
  if (!props.meeting.startTime || props.meeting.startTime === '0') return ''
  try {
    return new Date(parseInt(props.meeting.startTime)).toLocaleString('ko-KR')
  } catch {
    return ''
  }
})
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b">
      <h2 class="font-semibold truncate">{{ meeting.meetingName }}</h2>
      <button
        @click="emit('close')"
        class="inline-flex items-center justify-center h-8 w-8 rounded-md hover:bg-accent transition-colors shrink-0"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
          <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>

    <!-- Info -->
    <div class="flex-1 overflow-y-auto p-4 space-y-4">
      <div class="grid grid-cols-2 gap-3 text-sm">
        <div>
          <span class="text-muted-foreground">상태</span>
          <div class="mt-0.5 font-medium">
            <span
              class="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full"
              :class="meeting.running
                ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'"
            >
              {{ meeting.running ? '진행 중' : '대기' }}
            </span>
          </div>
        </div>
        <div>
          <span class="text-muted-foreground">참가자</span>
          <div class="mt-0.5 font-medium">{{ meeting.participantCount }}명</div>
        </div>
        <div v-if="startedAt">
          <span class="text-muted-foreground">시작 시간</span>
          <div class="mt-0.5 font-medium">{{ startedAt }}</div>
        </div>
        <div>
          <span class="text-muted-foreground">ID</span>
          <div class="mt-0.5 font-mono text-xs break-all">{{ meeting.meetingID }}</div>
        </div>
      </div>

      <!-- Attendees -->
      <div v-if="meeting.attendees.length > 0">
        <h3 class="text-sm font-medium mb-2">참가자 목록</h3>
        <div class="space-y-1.5">
          <div
            v-for="att in meeting.attendees"
            :key="att.fullName"
            class="flex items-center justify-between px-3 py-2 text-sm rounded-md bg-muted/50"
          >
            <div class="flex items-center gap-2 min-w-0">
              <span class="font-medium truncate">{{ att.fullName }}</span>
              <span
                class="shrink-0 px-1.5 py-0.5 text-[10px] font-medium rounded"
                :class="att.role === 'MODERATOR'
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                  : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'"
              >
                {{ att.role === 'MODERATOR' ? '관리자' : '참가자' }}
              </span>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <svg
                v-if="att.hasJoinedVoice"
                xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                class="h-3.5 w-3.5 text-green-500"
                title="음성 참가"
              >
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" /><path d="M19 10v2a7 7 0 0 1-14 0v-2" /><line x1="12" y1="19" x2="12" y2="23" /><line x1="8" y1="23" x2="16" y2="23" />
              </svg>
              <svg
                v-if="att.hasVideo"
                xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                class="h-3.5 w-3.5 text-blue-500"
                title="비디오"
              >
                <polygon points="23 7 16 12 23 17 23 7" /><rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
              </svg>
            </div>
          </div>
        </div>
      </div>
      <p v-else class="text-sm text-muted-foreground">참가자가 없습니다.</p>

      <!-- Actions -->
      <div class="flex items-center gap-2 pt-2">
        <button
          @click="emit('join', meeting.meetingID)"
          class="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" /><polyline points="10 17 15 12 10 7" /><line x1="15" y1="12" x2="3" y2="12" />
          </svg>
          회의 참가
        </button>
        <button
          v-if="isAdmin && meeting.running"
          @click="emit('end', meeting.meetingID)"
          class="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-md border border-destructive text-destructive hover:bg-destructive hover:text-destructive-foreground transition-colors"
        >
          회의 종료
        </button>
      </div>
    </div>
  </div>
</template>

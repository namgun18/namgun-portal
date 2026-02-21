<script setup lang="ts">
import MeetingCard from '~/components/meetings/MeetingCard.vue'
import MeetingDetail from '~/components/meetings/MeetingDetail.vue'
import CreateMeetingModal from '~/components/meetings/CreateMeetingModal.vue'
import RecordingList from '~/components/meetings/RecordingList.vue'

definePageMeta({ layout: 'default' })

const { user } = useAuth()
const {
  meetings,
  selectedMeeting,
  recordings,
  loadingMeetings,
  loadingDetail,
  loadingRecordings,
  showCreateModal,
  activeJoinUrl,
  activeMeetingName,
  fetchMeetings,
  fetchMeetingDetail,
  joinMeeting,
  leaveMeeting,
  openInNewTab,
  endMeeting,
  fetchRecordings,
  deleteRecording,
  clearSelectedMeeting,
} = useMeetings()

const activeTab = ref<'meetings' | 'recordings'>('meetings')
const isAdmin = computed(() => user.value?.is_admin ?? false)

onMounted(async () => {
  await fetchMeetings()
  await fetchRecordings()
})

async function handleSelect(meetingId: string) {
  await fetchMeetingDetail(meetingId)
}

async function handleJoin(meetingId: string) {
  try {
    await joinMeeting(meetingId)
  } catch (e: any) {
    console.error('Join failed:', e)
  }
}

async function handleEnd(meetingId: string) {
  if (!confirm('이 회의를 종료하시겠습니까?')) return
  try {
    await endMeeting(meetingId)
  } catch (e: any) {
    console.error('End failed:', e)
  }
}

async function handleDeleteRecording(recordId: string) {
  if (!confirm('이 녹화를 삭제하시겠습니까?')) return
  try {
    await deleteRecording(recordId)
  } catch (e: any) {
    console.error('Delete recording failed:', e)
  }
}

async function refresh() {
  await Promise.all([fetchMeetings(), fetchRecordings()])
}
</script>

<template>
  <!-- 회의 진행 중: iframe 전체화면 -->
  <div v-if="activeJoinUrl" class="flex flex-col h-[calc(100vh-3.5rem)]">
    <!-- 최소 컨트롤 바 -->
    <div class="flex items-center justify-between px-4 py-1.5 border-b bg-background">
      <div class="flex items-center gap-2 min-w-0">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 text-primary shrink-0">
          <path d="M23 7l-7 5 7 5V7z" /><rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
        </svg>
        <span class="text-sm font-medium truncate">{{ activeMeetingName }}</span>
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <button
          @click="openInNewTab"
          class="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md border hover:bg-accent transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" /><polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" />
          </svg>
          새 탭에서 열기
        </button>
        <button
          @click="leaveMeeting"
          class="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md border border-destructive/30 text-destructive hover:bg-destructive/10 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          회의 나가기
        </button>
      </div>
    </div>
    <!-- BBB iframe -->
    <iframe
      :src="activeJoinUrl"
      class="flex-1 w-full border-0"
      allow="camera; microphone; display-capture; autoplay; fullscreen; clipboard-write"
      allowfullscreen
    />
  </div>

  <!-- 기존 회의 목록 UI -->
  <div v-else class="flex h-[calc(100vh-3.5rem)] overflow-hidden">
    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Command bar -->
      <div class="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-4 py-2 border-b bg-background">
        <button
          @click="showCreateModal = true"
          class="inline-flex items-center gap-1.5 px-2 sm:px-3 py-1.5 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          <span class="hidden sm:inline">새 회의</span>
        </button>

        <button
          @click="refresh"
          class="inline-flex items-center gap-1.5 px-2 sm:px-3 py-1.5 text-sm font-medium rounded-md border hover:bg-accent transition-colors"
          title="새로고침"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
            <polyline points="23 4 23 10 17 10" /><polyline points="1 20 1 14 7 14" /><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
          </svg>
          <span class="hidden sm:inline">새로고침</span>
        </button>

        <div class="flex-1" />

        <!-- Tabs -->
        <div class="flex items-center border rounded-md">
          <button
            @click="activeTab = 'meetings'"
            class="px-3 py-1.5 text-xs font-medium rounded-l-md transition-colors"
            :class="activeTab === 'meetings' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50'"
          >
            회의
          </button>
          <button
            @click="activeTab = 'recordings'"
            class="px-3 py-1.5 text-xs font-medium rounded-r-md transition-colors"
            :class="activeTab === 'recordings' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50'"
          >
            녹화
          </button>
        </div>
      </div>

      <!-- Content area -->
      <div class="flex flex-1 min-h-0">
        <!-- Meetings tab -->
        <template v-if="activeTab === 'meetings'">
          <!-- Meeting grid -->
          <div
            class="flex-1 overflow-y-auto p-4"
            :class="selectedMeeting ? 'hidden md:block' : ''"
          >
            <!-- Loading -->
            <div v-if="loadingMeetings" class="flex items-center justify-center py-16">
              <div class="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            </div>

            <!-- Empty -->
            <div v-else-if="meetings.length === 0" class="flex flex-col items-center justify-center py-16 text-center">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="h-12 w-12 text-muted-foreground/50 mb-3">
                <path d="M23 7l-7 5 7 5V7z" /><rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
              </svg>
              <p class="text-muted-foreground text-sm">활성 회의가 없습니다</p>
              <p class="text-muted-foreground text-xs mt-1">새 회의를 만들어 시작하세요</p>
            </div>

            <!-- Grid -->
            <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <MeetingCard
                v-for="m in meetings"
                :key="m.meetingID"
                :meeting="m"
                :is-admin="isAdmin"
                @select="handleSelect"
                @join="handleJoin"
                @end="handleEnd"
              />
            </div>
          </div>

          <!-- Detail panel -->
          <div
            v-if="selectedMeeting"
            class="w-full md:w-80 md:shrink-0 border-l bg-background"
          >
            <div v-if="loadingDetail" class="flex items-center justify-center h-full">
              <div class="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
            <MeetingDetail
              v-else
              :meeting="selectedMeeting"
              :is-admin="isAdmin"
              @join="handleJoin"
              @end="handleEnd"
              @close="clearSelectedMeeting"
            />
          </div>
        </template>

        <!-- Recordings tab -->
        <div v-else class="flex-1 overflow-y-auto">
          <RecordingList
            :recordings="recordings"
            :loading="loadingRecordings"
            :is-admin="isAdmin"
            @delete="handleDeleteRecording"
          />
        </div>
      </div>
    </div>

    <!-- Create modal -->
    <CreateMeetingModal
      v-if="showCreateModal"
      @close="showCreateModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import type { CalendarShareInfo } from '~/composables/useCalendar'

const {
  showShareModal, sharingCalendar,
  fetchCalendarShares, setCalendarShares, removeCalendarShare, closeShareModal,
} = useCalendar()

const shares = ref<CalendarShareInfo[]>([])
const loading = ref(false)
const newEmail = ref('')
const newCanWrite = ref(false)
const error = ref('')

watch(showShareModal, async (open) => {
  if (open && sharingCalendar.value) {
    loading.value = true
    error.value = ''
    try {
      shares.value = await fetchCalendarShares(sharingCalendar.value.id)
    } finally {
      loading.value = false
    }
  } else {
    shares.value = []
    newEmail.value = ''
    newCanWrite.value = false
    error.value = ''
  }
})

async function handleAdd() {
  const email = newEmail.value.trim()
  if (!email || !sharingCalendar.value) return
  if (shares.value.some(s => s.email === email)) {
    error.value = '이미 공유된 사용자입니다.'
    return
  }
  error.value = ''

  const updated = [...shares.value, { email, can_write: newCanWrite.value }]
  try {
    await setCalendarShares(sharingCalendar.value.id, updated)
    shares.value = updated
    newEmail.value = ''
    newCanWrite.value = false
  } catch {
    error.value = '공유 설정에 실패했습니다.'
  }
}

async function handleRemove(email: string) {
  if (!sharingCalendar.value) return
  try {
    await removeCalendarShare(sharingCalendar.value.id, email)
    shares.value = shares.value.filter(s => s.email !== email)
  } catch {
    error.value = '공유 해제에 실패했습니다.'
  }
}

async function toggleWrite(share: CalendarShareInfo) {
  if (!sharingCalendar.value) return
  const updated = shares.value.map(s =>
    s.email === share.email ? { ...s, can_write: !s.can_write } : s
  )
  try {
    await setCalendarShares(sharingCalendar.value.id, updated)
    shares.value = updated
  } catch {
    error.value = '권한 변경에 실패했습니다.'
  }
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="showShareModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="closeShareModal"
    >
      <div class="bg-background border rounded-xl shadow-lg w-full max-w-md mx-4 overflow-hidden">
        <!-- Header -->
        <div class="flex items-center justify-between px-5 py-4 border-b">
          <div>
            <h2 class="text-lg font-semibold">캘린더 공유</h2>
            <p v-if="sharingCalendar" class="text-sm text-muted-foreground flex items-center gap-1.5 mt-0.5">
              <span
                class="w-2.5 h-2.5 rounded-full inline-block"
                :style="{ backgroundColor: sharingCalendar.color || '#3b82f6' }"
              />
              {{ sharingCalendar.name }}
            </p>
          </div>
          <button @click="closeShareModal" class="p-1.5 rounded-lg hover:bg-accent">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        <div class="px-5 py-4 space-y-4">
          <!-- Add new share -->
          <div class="space-y-2">
            <label class="text-sm font-medium">사용자 추가</label>
            <div class="flex gap-2">
              <input
                v-model="newEmail"
                type="email"
                placeholder="이메일 주소"
                class="flex-1 px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
                @keyup.enter="handleAdd"
              />
              <button
                @click="handleAdd"
                :disabled="!newEmail.trim()"
                class="px-3 py-2 text-sm font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                추가
              </button>
            </div>
            <label class="flex items-center gap-2 text-sm text-muted-foreground">
              <input v-model="newCanWrite" type="checkbox" class="h-3.5 w-3.5 rounded border-gray-300" />
              쓰기 권한 부여
            </label>
          </div>

          <p v-if="error" class="text-sm text-destructive">{{ error }}</p>

          <!-- Current shares -->
          <div>
            <h3 class="text-sm font-medium mb-2">공유 중인 사용자</h3>
            <div v-if="loading" class="text-sm text-muted-foreground py-2">불러오는 중...</div>
            <div v-else-if="shares.length === 0" class="text-sm text-muted-foreground py-2">
              아직 공유된 사용자가 없습니다.
            </div>
            <div v-else class="space-y-1 max-h-48 overflow-y-auto">
              <div
                v-for="share in shares"
                :key="share.email"
                class="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/30 group"
              >
                <div class="w-7 h-7 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-medium shrink-0">
                  {{ share.email[0].toUpperCase() }}
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm truncate">{{ share.email }}</p>
                  <button
                    @click="toggleWrite(share)"
                    class="text-xs transition-colors"
                    :class="share.can_write ? 'text-emerald-600' : 'text-muted-foreground hover:text-foreground'"
                  >
                    {{ share.can_write ? '읽기/쓰기' : '읽기 전용' }}
                  </button>
                </div>
                <button
                  @click="handleRemove(share.email)"
                  class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-accent text-muted-foreground hover:text-destructive transition-all"
                  title="공유 해제"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="px-5 py-3 border-t bg-muted/20 flex justify-end">
          <button
            @click="closeShareModal"
            class="px-4 py-2 text-sm font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            완료
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

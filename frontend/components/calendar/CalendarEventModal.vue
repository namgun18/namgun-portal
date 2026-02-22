<script setup lang="ts">
import type { CalendarEvent, CalendarInfo } from '~/composables/useCalendar'

const {
  calendars, selectedDate, showEventModal, editingEvent,
  createEvent, updateEvent, deleteEvent, closeModal,
} = useCalendar()

const form = reactive({
  calendar_id: '',
  title: '',
  description: '',
  location: '',
  start: '',
  end: '',
  all_day: false,
})
const error = ref('')
const submitting = ref(false)

const isEditing = computed(() => !!editingEvent.value)
const modalTitle = computed(() => isEditing.value ? '일정 수정' : '새 일정')

watch(showEventModal, (show) => {
  if (!show) return
  error.value = ''
  if (editingEvent.value) {
    const e = editingEvent.value
    form.calendar_id = e.calendar_id
    form.title = e.title
    form.description = e.description || ''
    form.location = e.location || ''
    form.start = formatDateTimeLocal(e.start)
    form.end = formatDateTimeLocal(e.end)
    form.all_day = e.all_day
  } else {
    const d = selectedDate.value
    const start = new Date(d)
    if (start.getHours() === 0 && start.getMinutes() === 0) {
      start.setHours(9, 0, 0, 0)
    }
    const end = new Date(start)
    end.setHours(end.getHours() + 1)

    form.calendar_id = calendars.value[0]?.id || ''
    form.title = ''
    form.description = ''
    form.location = ''
    form.start = formatDateTimeLocal(start.toISOString())
    form.end = formatDateTimeLocal(end.toISOString())
    form.all_day = false
  }
})

function formatDateTimeLocal(iso: string) {
  try {
    const d = new Date(iso)
    const pad = (n: number) => n.toString().padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return ''
  }
}

async function handleSubmit() {
  if (!form.title.trim()) {
    error.value = '제목을 입력해주세요.'
    return
  }
  if (!form.calendar_id) {
    error.value = '캘린더를 선택해주세요.'
    return
  }
  if (!form.start || !form.end) {
    error.value = '시작/종료 시간을 입력해주세요.'
    return
  }

  submitting.value = true
  error.value = ''
  try {
    const data = {
      calendar_id: form.calendar_id,
      title: form.title.trim(),
      description: form.description.trim() || undefined,
      location: form.location.trim() || undefined,
      start: new Date(form.start).toISOString(),
      end: new Date(form.end).toISOString(),
      all_day: form.all_day,
    }

    if (isEditing.value) {
      await updateEvent(editingEvent.value!.id, data)
    } else {
      await createEvent(data)
    }
    closeModal()
  } catch (e: any) {
    error.value = e?.data?.detail || '일정 저장에 실패했습니다.'
  } finally {
    submitting.value = false
  }
}

async function handleDelete() {
  if (!editingEvent.value) return
  if (!confirm('이 일정을 삭제하시겠습니까?')) return
  await deleteEvent(editingEvent.value.id)
  closeModal()
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="showEventModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/50" @click="closeModal" />

      <!-- Modal -->
      <div class="relative w-full max-w-md bg-background border rounded-xl shadow-lg">
        <div class="flex items-center justify-between px-5 py-4 border-b">
          <h2 class="text-lg font-semibold">{{ modalTitle }}</h2>
          <button @click="closeModal" class="p-1 rounded hover:bg-accent">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        <form @submit.prevent="handleSubmit" class="px-5 py-4 space-y-3">
          <div>
            <label class="block text-sm font-medium mb-1">제목</label>
            <input
              v-model="form.title"
              type="text"
              placeholder="일정 제목"
              class="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          <div>
            <label class="block text-sm font-medium mb-1">캘린더</label>
            <select
              v-model="form.calendar_id"
              class="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            >
              <option v-for="cal in calendars" :key="cal.id" :value="cal.id">
                {{ cal.name }}
              </option>
            </select>
          </div>

          <div class="flex items-center gap-2">
            <input id="allDay" v-model="form.all_day" type="checkbox" class="h-4 w-4 rounded border-gray-300 text-primary" />
            <label for="allDay" class="text-sm">종일</label>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium mb-1">시작</label>
              <input
                v-model="form.start"
                :type="form.all_day ? 'date' : 'datetime-local'"
                class="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">종료</label>
              <input
                v-model="form.end"
                :type="form.all_day ? 'date' : 'datetime-local'"
                class="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium mb-1">장소</label>
            <input
              v-model="form.location"
              type="text"
              placeholder="장소 (선택)"
              class="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          <div>
            <label class="block text-sm font-medium mb-1">설명</label>
            <textarea
              v-model="form.description"
              rows="2"
              placeholder="설명 (선택)"
              class="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
            />
          </div>

          <p v-if="error" class="text-sm text-destructive">{{ error }}</p>

          <div class="flex items-center justify-between pt-1">
            <button
              v-if="isEditing"
              type="button"
              @click="handleDelete"
              class="px-3 py-2 text-sm rounded-lg text-destructive hover:bg-destructive/10 transition-colors"
            >
              삭제
            </button>
            <div v-else />
            <div class="flex gap-2">
              <button
                type="button"
                @click="closeModal"
                class="px-4 py-2 text-sm rounded-lg hover:bg-accent transition-colors"
              >
                취소
              </button>
              <button
                type="submit"
                :disabled="submitting"
                class="px-4 py-2 text-sm rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {{ submitting ? '저장 중...' : '저장' }}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

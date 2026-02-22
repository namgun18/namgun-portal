<script setup lang="ts">
import type { CalendarInfo } from '~/composables/useCalendar'

const {
  calendars, selectedDate, loadingCalendars,
  fetchCalendars, createCalendar, deleteCalendar,
  toggleCalendarVisibility, soloCalendar, selectDate, openCreateModal, openShareModal,
  CALENDAR_COLORS,
} = useCalendar()

const showNewForm = ref(false)
const newName = ref('')
const newColor = ref(CALENDAR_COLORS[0])

onMounted(() => {
  if (calendars.value.length === 0) fetchCalendars()
})

async function handleCreate() {
  if (!newName.value.trim()) return
  try {
    await createCalendar(newName.value.trim(), newColor.value)
    newName.value = ''
    showNewForm.value = false
  } catch {}
}

async function handleDelete(cal: CalendarInfo) {
  if (!confirm(`'${cal.name}' 캘린더를 삭제하시겠습니까?`)) return
  await deleteCalendar(cal.id)
}
</script>

<template>
  <div class="space-y-4">
    <button
      @click="openCreateModal()"
      class="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 text-sm font-medium transition-colors"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
      새 일정
    </button>

    <CalendarMiniMonth :selected-date="selectedDate" @select="selectDate" />

    <div>
      <div class="flex items-center justify-between mb-2">
        <h3 class="text-sm font-medium">내 캘린더</h3>
        <button @click="showNewForm = !showNewForm" class="p-1 rounded hover:bg-accent" title="캘린더 추가">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        </button>
      </div>

      <div v-if="loadingCalendars" class="text-sm text-muted-foreground">불러오는 중...</div>

      <div v-else class="space-y-1">
        <div
          v-for="cal in calendars"
          :key="cal.id"
          class="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-accent/50 group"
        >
          <button
            @click="toggleCalendarVisibility(cal.id)"
            class="w-3.5 h-3.5 rounded-sm border-2 shrink-0 transition-colors"
            :style="{
              borderColor: cal.color || '#3b82f6',
              backgroundColor: cal.is_visible ? (cal.color || '#3b82f6') : 'transparent',
            }"
          />
          <span
            class="text-sm flex-1 truncate cursor-pointer hover:underline"
            @click="soloCalendar(cal.id)"
            :title="`'${cal.name}'만 표시 (다시 클릭하면 전체 표시)`"
          >{{ cal.name }}</span>
          <button
            @click="openShareModal(cal)"
            class="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-accent text-muted-foreground"
            title="공유"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>
          </button>
          <button
            @click="handleDelete(cal)"
            class="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-accent text-muted-foreground"
            title="삭제"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
      </div>

      <!-- New calendar form -->
      <div v-if="showNewForm" class="mt-2 p-2 border rounded-lg space-y-2 bg-muted/30">
        <input
          v-model="newName"
          type="text"
          placeholder="캘린더 이름"
          class="w-full px-2 py-1.5 text-sm border rounded bg-background focus:outline-none focus:ring-1 focus:ring-primary/50"
          @keyup.enter="handleCreate"
        />
        <div class="flex gap-1">
          <button
            v-for="c in CALENDAR_COLORS"
            :key="c"
            @click="newColor = c"
            class="w-5 h-5 rounded-full border-2 transition-transform"
            :style="{ backgroundColor: c, borderColor: newColor === c ? 'currentColor' : 'transparent' }"
            :class="{ 'scale-110': newColor === c }"
          />
        </div>
        <div class="flex gap-1">
          <button @click="handleCreate" class="px-2 py-1 text-xs rounded bg-primary text-primary-foreground hover:bg-primary/90">추가</button>
          <button @click="showNewForm = false" class="px-2 py-1 text-xs rounded hover:bg-accent">취소</button>
        </div>
      </div>
    </div>
  </div>
</template>

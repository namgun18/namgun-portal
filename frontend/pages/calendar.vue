<script setup lang="ts">
definePageMeta({ layout: 'default' })

const {
  viewMode, selectedDate, loadingEvents,
  fetchCalendars, fetchEvents,
  setViewMode, goToToday, navigatePrev, navigateNext,
} = useCalendar()

onMounted(async () => {
  await fetchCalendars()
  await fetchEvents()
})

watch(selectedDate, () => {
  fetchEvents()
})

const headerLabel = computed(() => {
  const d = selectedDate.value
  if (viewMode.value === 'month') {
    return `${d.getFullYear()}년 ${d.getMonth() + 1}월`
  } else if (viewMode.value === 'week') {
    const start = new Date(d)
    start.setDate(start.getDate() - start.getDay())
    const end = new Date(start)
    end.setDate(end.getDate() + 6)
    if (start.getMonth() === end.getMonth()) {
      return `${start.getFullYear()}년 ${start.getMonth() + 1}월 ${start.getDate()}일 ~ ${end.getDate()}일`
    }
    return `${start.getMonth() + 1}월 ${start.getDate()}일 ~ ${end.getMonth() + 1}월 ${end.getDate()}일`
  } else {
    const weekdays = ['일', '월', '화', '수', '목', '금', '토']
    return `${d.getFullYear()}년 ${d.getMonth() + 1}월 ${d.getDate()}일 (${weekdays[d.getDay()]})`
  }
})
</script>

<template>
  <div class="h-full flex overflow-hidden">
    <!-- Sidebar -->
    <aside class="hidden lg:block w-60 shrink-0 border-r p-4 overflow-y-auto">
      <ClientOnly>
        <CalendarSidebar />
      </ClientOnly>
    </aside>

    <!-- Main content (ClientOnly: new Date() 타임존 SSR/클라이언트 불일치 방지) -->
    <ClientOnly>
      <div class="flex-1 flex flex-col overflow-hidden">
        <!-- Toolbar -->
        <div class="flex items-center justify-between px-4 py-3 border-b shrink-0">
          <div class="flex items-center gap-2">
            <button
              @click="goToToday"
              class="px-3 py-1.5 text-sm border rounded-md hover:bg-accent transition-colors"
            >
              오늘
            </button>
            <button @click="navigatePrev" class="p-1.5 rounded-md hover:bg-accent transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5"><polyline points="15 18 9 12 15 6"/></svg>
            </button>
            <button @click="navigateNext" class="p-1.5 rounded-md hover:bg-accent transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5"><polyline points="9 18 15 12 9 6"/></svg>
            </button>
            <h2 class="text-lg font-semibold ml-2">{{ headerLabel }}</h2>
            <div v-if="loadingEvents" class="ml-2">
              <svg class="animate-spin h-4 w-4 text-muted-foreground" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            </div>
          </div>

          <div class="flex items-center gap-1 rounded-lg border p-0.5">
            <button
              v-for="mode in (['month', 'week', 'day'] as const)"
              :key="mode"
              @click="setViewMode(mode)"
              class="px-3 py-1 text-sm rounded-md transition-colors"
              :class="viewMode === mode ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:text-foreground'"
            >
              {{ mode === 'month' ? '월' : mode === 'week' ? '주' : '일' }}
            </button>
          </div>
        </div>

        <!-- Calendar view -->
        <div class="flex-1 overflow-hidden">
          <CalendarMonthView v-if="viewMode === 'month'" />
          <CalendarWeekView v-else-if="viewMode === 'week'" />
          <CalendarDayView v-else />
        </div>
      </div>

      <template #fallback>
        <div class="flex-1 flex items-center justify-center text-muted-foreground">
          불러오는 중...
        </div>
      </template>
    </ClientOnly>

    <!-- Event modal -->
    <CalendarEventModal />
    <!-- Share modal -->
    <CalendarShareModal />
  </div>
</template>

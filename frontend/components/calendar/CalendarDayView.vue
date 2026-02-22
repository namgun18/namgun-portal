<script setup lang="ts">
import type { CalendarEvent } from '~/composables/useCalendar'

const { selectedDate, visibleEvents, openCreateModal, openEditModal } = useCalendar()

const HOURS = Array.from({ length: 24 }, (_, i) => i)

const today = new Date()

const isToday = computed(() => {
  const d = selectedDate.value
  return d.getDate() === today.getDate() &&
    d.getMonth() === today.getMonth() &&
    d.getFullYear() === today.getFullYear()
})

const dateLabel = computed(() => {
  const d = selectedDate.value
  const weekdays = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일']
  return `${d.getMonth() + 1}월 ${d.getDate()}일 ${weekdays[d.getDay()]}`
})

const allDayEvts = computed(() =>
  visibleEvents.value.filter(e => {
    if (!e.all_day) return false
    const d = selectedDate.value
    const dayStart = new Date(d.getFullYear(), d.getMonth(), d.getDate())
    const dayEnd = new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1)
    const eStart = new Date(e.start)
    const eEnd = new Date(e.end)
    return eStart < dayEnd && eEnd > dayStart
  })
)

function eventsForHour(hour: number): CalendarEvent[] {
  const d = selectedDate.value
  const slotStart = new Date(d.getFullYear(), d.getMonth(), d.getDate(), hour)
  const slotEnd = new Date(d.getFullYear(), d.getMonth(), d.getDate(), hour + 1)
  return visibleEvents.value.filter(e => {
    if (e.all_day) return false
    const eStart = new Date(e.start)
    const eEnd = new Date(e.end)
    return eStart < slotEnd && eEnd > slotStart
  })
}

function formatHour(h: number) {
  return `${h.toString().padStart(2, '0')}:00`
}

function handleSlotClick(hour: number) {
  const d = selectedDate.value
  openCreateModal(new Date(d.getFullYear(), d.getMonth(), d.getDate(), hour))
}
</script>

<template>
  <div class="flex flex-col h-full overflow-hidden">
    <!-- Header -->
    <div class="border-b p-3 shrink-0">
      <h3 class="text-sm font-medium" :class="{ 'text-primary': isToday }">
        {{ dateLabel }}
        <span v-if="isToday" class="ml-1 text-xs text-primary">(오늘)</span>
      </h3>
      <!-- All day events -->
      <div v-if="allDayEvts.length" class="mt-2 space-y-1">
        <CalendarEventChip
          v-for="event in allDayEvts"
          :key="event.id"
          :event="event"
          @click="openEditModal(event)"
        />
      </div>
    </div>

    <!-- Time grid -->
    <div class="flex-1 overflow-y-auto">
      <div v-for="hour in HOURS" :key="hour" class="grid grid-cols-[60px_1fr]">
        <div class="border-r border-b h-14 flex items-start justify-end pr-2 pt-0.5">
          <span class="text-xs text-muted-foreground">{{ formatHour(hour) }}</span>
        </div>
        <div
          class="border-b h-14 p-0.5 cursor-pointer hover:bg-accent/20 transition-colors"
          @click="handleSlotClick(hour)"
        >
          <CalendarEventChip
            v-for="event in eventsForHour(hour)"
            :key="event.id"
            :event="event"
            @click="openEditModal(event)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

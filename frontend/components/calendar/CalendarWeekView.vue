<script setup lang="ts">
import type { CalendarEvent } from '~/composables/useCalendar'

const { selectedDate, visibleEvents, openCreateModal, openEditModal } = useCalendar()

const HOURS = Array.from({ length: 24 }, (_, i) => i)
const DAY_LABELS = ['일', '월', '화', '수', '목', '금', '토']

const weekDays = computed(() => {
  const d = selectedDate.value
  const day = d.getDay()
  const start = new Date(d.getFullYear(), d.getMonth(), d.getDate() - day)
  return Array.from({ length: 7 }, (_, i) => {
    const date = new Date(start)
    date.setDate(date.getDate() + i)
    return date
  })
})

const today = new Date()

function isToday(date: Date) {
  return date.getDate() === today.getDate() &&
    date.getMonth() === today.getMonth() &&
    date.getFullYear() === today.getFullYear()
}

function eventsForDayHour(date: Date, hour: number): CalendarEvent[] {
  const slotStart = new Date(date.getFullYear(), date.getMonth(), date.getDate(), hour)
  const slotEnd = new Date(date.getFullYear(), date.getMonth(), date.getDate(), hour + 1)
  return visibleEvents.value.filter(e => {
    if (e.all_day) return false
    const eStart = new Date(e.start)
    const eEnd = new Date(e.end)
    return eStart < slotEnd && eEnd > slotStart
  })
}

function allDayEvents(date: Date): CalendarEvent[] {
  const dayStart = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const dayEnd = new Date(date.getFullYear(), date.getMonth(), date.getDate() + 1)
  return visibleEvents.value.filter(e => {
    if (!e.all_day) return false
    const eStart = new Date(e.start)
    const eEnd = new Date(e.end)
    return eStart < dayEnd && eEnd > dayStart
  })
}

function formatHour(h: number) {
  return `${h.toString().padStart(2, '0')}:00`
}

function handleSlotClick(date: Date, hour: number) {
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate(), hour)
  openCreateModal(d)
}
</script>

<template>
  <div class="flex flex-col h-full overflow-hidden">
    <!-- Header row -->
    <div class="grid grid-cols-[60px_repeat(7,1fr)] border-b shrink-0">
      <div class="border-r" />
      <div
        v-for="(day, i) in weekDays"
        :key="i"
        class="py-2 text-center border-r last:border-r-0"
      >
        <div class="text-xs text-muted-foreground" :class="{ 'text-red-500 dark:text-red-400': i === 0 }">
          {{ DAY_LABELS[i] }}
        </div>
        <div
          class="text-sm font-medium inline-flex items-center justify-center w-7 h-7 rounded-full"
          :class="{ 'bg-primary text-primary-foreground': isToday(day) }"
        >
          {{ day.getDate() }}
        </div>
        <!-- All day events -->
        <div v-if="allDayEvents(day).length" class="px-1 mt-1 space-y-0.5">
          <CalendarEventChip
            v-for="event in allDayEvents(day)"
            :key="event.id"
            :event="event"
            @click="openEditModal(event)"
          />
        </div>
      </div>
    </div>

    <!-- Time grid -->
    <div class="flex-1 overflow-y-auto">
      <div class="grid grid-cols-[60px_repeat(7,1fr)]">
        <template v-for="hour in HOURS" :key="hour">
          <!-- Time label -->
          <div class="border-r border-b h-12 flex items-start justify-end pr-2 pt-0.5">
            <span class="text-xs text-muted-foreground">{{ formatHour(hour) }}</span>
          </div>
          <!-- Day cells -->
          <div
            v-for="(day, di) in weekDays"
            :key="`${hour}-${di}`"
            class="border-r border-b last:border-r-0 h-12 relative cursor-pointer hover:bg-accent/20 transition-colors"
            @click="handleSlotClick(day, hour)"
          >
            <CalendarEventChip
              v-for="event in eventsForDayHour(day, hour)"
              :key="event.id"
              :event="event"
              @click="openEditModal(event)"
            />
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CalendarEvent } from '~/composables/useCalendar'

const { selectedDate, visibleEvents, openCreateModal, openEditModal } = useCalendar()

const DAY_LABELS = ['일', '월', '화', '수', '목', '금', '토']

interface DayCell {
  date: Date
  isCurrentMonth: boolean
  isToday: boolean
  events: CalendarEvent[]
}

const weeks = computed((): DayCell[][] => {
  const d = selectedDate.value
  const year = d.getFullYear()
  const month = d.getMonth()
  const today = new Date()

  const firstOfMonth = new Date(year, month, 1)
  const startDay = firstOfMonth.getDay()
  const lastOfMonth = new Date(year, month + 1, 0).getDate()

  // Start from Sunday of the first week
  const startDate = new Date(year, month, 1 - startDay)

  const result: DayCell[][] = []
  let current = new Date(startDate)

  for (let w = 0; w < 6; w++) {
    const week: DayCell[] = []
    for (let d = 0; d < 7; d++) {
      const date = new Date(current)
      const isCurrentMonth = date.getMonth() === month
      const isToday = date.getDate() === today.getDate() &&
        date.getMonth() === today.getMonth() &&
        date.getFullYear() === today.getFullYear()

      // Filter events for this day
      const dayStart = new Date(date.getFullYear(), date.getMonth(), date.getDate())
      const dayEnd = new Date(date.getFullYear(), date.getMonth(), date.getDate() + 1)
      const dayEvents = visibleEvents.value.filter(e => {
        const eStart = new Date(e.start)
        const eEnd = new Date(e.end)
        return eStart < dayEnd && eEnd > dayStart
      })

      week.push({ date, isCurrentMonth, isToday, events: dayEvents })
      current.setDate(current.getDate() + 1)
    }
    result.push(week)
    // Stop if we've gone past the month and have enough weeks
    if (current.getMonth() > month || (current.getMonth() < month && w > 3)) break
  }

  return result
})
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Day headers -->
    <div class="grid grid-cols-7 border-b">
      <div
        v-for="label in DAY_LABELS"
        :key="label"
        class="py-2 text-center text-xs font-medium text-muted-foreground"
        :class="{ 'text-red-500 dark:text-red-400': label === '일' }"
      >
        {{ label }}
      </div>
    </div>

    <!-- Week rows -->
    <div class="flex-1 grid" :style="{ gridTemplateRows: `repeat(${weeks.length}, 1fr)` }">
      <div v-for="(week, wi) in weeks" :key="wi" class="grid grid-cols-7 border-b last:border-b-0">
        <div
          v-for="(day, di) in week"
          :key="di"
          class="border-r last:border-r-0 p-1 min-h-[80px] overflow-hidden cursor-pointer hover:bg-accent/30 transition-colors"
          :class="{
            'bg-muted/30': !day.isCurrentMonth,
          }"
          @click="openCreateModal(day.date)"
        >
          <div
            class="text-xs mb-0.5 inline-flex items-center justify-center w-6 h-6 rounded-full"
            :class="{
              'text-muted-foreground': !day.isCurrentMonth,
              'bg-primary text-primary-foreground': day.isToday,
              'text-red-500 dark:text-red-400': di === 0 && day.isCurrentMonth && !day.isToday,
            }"
          >
            {{ day.date.getDate() }}
          </div>
          <div class="space-y-0.5">
            <CalendarEventChip
              v-for="event in day.events.slice(0, 3)"
              :key="event.id"
              :event="event"
              @click="openEditModal(event)"
            />
            <div v-if="day.events.length > 3" class="text-xs text-muted-foreground px-1">
              +{{ day.events.length - 3 }}개 더
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

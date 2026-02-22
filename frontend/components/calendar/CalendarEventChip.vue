<script setup lang="ts">
import type { CalendarEvent } from '~/composables/useCalendar'

const props = defineProps<{
  event: CalendarEvent
}>()

const emit = defineEmits<{
  click: [event: CalendarEvent]
}>()

const timeLabel = computed(() => {
  if (props.event.all_day) return '종일'
  try {
    const d = new Date(props.event.start)
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
  } catch {
    return ''
  }
})
</script>

<template>
  <button
    @click.stop="emit('click', event)"
    class="w-full text-left px-1.5 py-0.5 rounded text-xs truncate text-white transition-opacity hover:opacity-80"
    :style="{ backgroundColor: event.color || '#3b82f6' }"
    :title="event.title"
  >
    <span v-if="!event.all_day" class="font-medium mr-0.5">{{ timeLabel }}</span>
    {{ event.title }}
  </button>
</template>

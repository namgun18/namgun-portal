<script setup lang="ts">
const props = defineProps<{
  selectedDate: Date
}>()

const emit = defineEmits<{
  select: [date: Date]
}>()

const viewDate = ref(new Date(props.selectedDate))

watch(() => props.selectedDate, (d) => {
  viewDate.value = new Date(d)
})

const DAY_LABELS = ['일', '월', '화', '수', '목', '금', '토']

const monthLabel = computed(() => {
  const y = viewDate.value.getFullYear()
  const m = viewDate.value.getMonth() + 1
  return `${y}년 ${m}월`
})

const days = computed(() => {
  const d = viewDate.value
  const year = d.getFullYear()
  const month = d.getMonth()
  const firstDay = new Date(year, month, 1).getDay()
  const lastDate = new Date(year, month + 1, 0).getDate()

  const cells: (Date | null)[] = []
  for (let i = 0; i < firstDay; i++) cells.push(null)
  for (let i = 1; i <= lastDate; i++) cells.push(new Date(year, month, i))
  return cells
})

function prevMonth() {
  const d = new Date(viewDate.value)
  d.setMonth(d.getMonth() - 1)
  viewDate.value = d
}

function nextMonth() {
  const d = new Date(viewDate.value)
  d.setMonth(d.getMonth() + 1)
  viewDate.value = d
}

function isToday(date: Date) {
  const t = new Date()
  return date.getDate() === t.getDate() && date.getMonth() === t.getMonth() && date.getFullYear() === t.getFullYear()
}

function isSelected(date: Date) {
  const s = props.selectedDate
  return date.getDate() === s.getDate() && date.getMonth() === s.getMonth() && date.getFullYear() === s.getFullYear()
}
</script>

<template>
  <div class="select-none">
    <div class="flex items-center justify-between mb-2">
      <button @click="prevMonth" class="p-1 rounded hover:bg-accent">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4"><polyline points="15 18 9 12 15 6"/></svg>
      </button>
      <span class="text-sm font-medium">{{ monthLabel }}</span>
      <button @click="nextMonth" class="p-1 rounded hover:bg-accent">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4"><polyline points="9 18 15 12 9 6"/></svg>
      </button>
    </div>
    <div class="grid grid-cols-7 text-center text-xs text-muted-foreground mb-1">
      <div v-for="label in DAY_LABELS" :key="label">{{ label }}</div>
    </div>
    <div class="grid grid-cols-7 text-center">
      <div v-for="(day, i) in days" :key="i" class="py-0.5">
        <button
          v-if="day"
          @click="emit('select', day)"
          class="w-7 h-7 text-xs rounded-full transition-colors"
          :class="{
            'bg-primary text-primary-foreground': isSelected(day),
            'bg-accent': isToday(day) && !isSelected(day),
            'hover:bg-accent/50': !isSelected(day) && !isToday(day),
          }"
        >
          {{ day.getDate() }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { user } = useAuth()

const now = ref(new Date())
let timer: ReturnType<typeof setInterval>

onMounted(() => {
  timer = setInterval(() => { now.value = new Date() }, 60_000)
})
onUnmounted(() => clearInterval(timer))

const greeting = computed(() => {
  const h = now.value.getHours()
  if (h < 6) return '늦은 밤이에요'
  if (h < 12) return '좋은 아침이에요'
  if (h < 18) return '좋은 오후예요'
  return '좋은 저녁이에요'
})

const dateStr = computed(() =>
  now.value.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  })
)
</script>

<template>
  <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-1">
    <div>
      <h1 class="text-2xl font-bold tracking-tight">
        {{ greeting }}, {{ user?.display_name || user?.username }}님
      </h1>
      <p class="text-muted-foreground text-sm mt-0.5">
        오늘도 좋은 하루 되세요
      </p>
    </div>
    <p class="text-sm text-muted-foreground shrink-0">
      {{ dateStr }}
    </p>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  name: string
  url: string | null
  status: 'ok' | 'down' | 'checking'
  responseMs: number | null
  internalOnly: boolean
}>()

const statusLabel = computed(() => {
  switch (props.status) {
    case 'ok': return '정상'
    case 'down': return '장애'
    case 'checking': return '확인중'
  }
})

const statusVariant = computed(() => {
  switch (props.status) {
    case 'ok': return 'success' as const
    case 'down': return 'destructive' as const
    case 'checking': return 'warning' as const
  }
})
</script>

<template>
  <UiCard class="flex flex-col">
    <UiCardHeader class="pb-3">
      <div class="flex items-center justify-between">
        <UiCardTitle class="text-base">{{ name }}</UiCardTitle>
        <UiBadge :variant="statusVariant">{{ statusLabel }}</UiBadge>
      </div>
    </UiCardHeader>
    <UiCardContent class="flex-1 flex flex-col justify-between gap-3">
      <div class="text-sm text-muted-foreground">
        <span v-if="status === 'ok' && responseMs !== null">
          응답시간: {{ responseMs }}ms
        </span>
        <span v-else-if="status === 'checking'">상태 확인 중...</span>
        <span v-else-if="status === 'down'">서비스에 연결할 수 없습니다</span>
      </div>
      <div>
        <a
          v-if="url && !internalOnly"
          :href="url"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
        >
          바로가기
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3 w-3">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" /><polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" />
          </svg>
        </a>
        <span v-else-if="internalOnly" class="text-xs text-muted-foreground">
          내부 서비스
        </span>
      </div>
    </UiCardContent>
  </UiCard>
</template>

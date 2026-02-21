<script setup lang="ts">
interface GameServer {
  name: string
  status: string
  game: string
}

const servers = ref<GameServer[]>([])
const loading = ref(true)

async function fetchGameServers() {
  try {
    servers.value = await $fetch<GameServer[]>('/api/dashboard/game-servers')
  } catch {
    // silent
  } finally {
    loading.value = false
  }
}

onMounted(fetchGameServers)

function statusColor(status: string) {
  return status === 'running' ? 'bg-green-500' : 'bg-zinc-400'
}

function statusLabel(status: string) {
  return status === 'running' ? '실행중' : '중지됨'
}
</script>

<template>
  <UiCard>
    <UiCardHeader class="pb-3">
      <div class="flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 text-orange-500"><line x1="6" x2="10" y1="11" y2="11"/><line x1="8" x2="8" y1="9" y2="13"/><line x1="15" x2="15.01" y1="12" y2="12"/><line x1="18" x2="18.01" y1="10" y2="10"/><path d="M17.32 5H6.68a4 4 0 0 0-3.978 3.59c-.006.052-.01.101-.017.152C2.604 9.416 2 14.456 2 16a3 3 0 0 0 3 3c1 0 1.5-.5 2-1l1.414-1.414A2 2 0 0 1 9.828 16h4.344a2 2 0 0 1 1.414.586L17 18c.5.5 1 1 2 1a3 3 0 0 0 3-3c0-1.545-.604-6.584-.685-7.258-.007-.05-.011-.1-.017-.151A4 4 0 0 0 17.32 5z"/></svg>
        <UiCardTitle class="text-base">게임서버</UiCardTitle>
      </div>
    </UiCardHeader>
    <UiCardContent>
      <!-- Loading -->
      <div v-if="loading" class="space-y-3">
        <UiSkeleton class="h-4 w-full" />
        <UiSkeleton class="h-4 w-3/4" />
      </div>

      <!-- Empty -->
      <p v-else-if="servers.length === 0" class="text-sm text-muted-foreground">
        등록된 게임서버가 없습니다
      </p>

      <!-- Server list -->
      <div v-else class="space-y-2">
        <div
          v-for="s in servers"
          :key="s.name"
          class="flex items-center justify-between rounded-md border px-3 py-2"
        >
          <div class="min-w-0">
            <p class="text-sm font-medium truncate">{{ s.name }}</p>
            <p v-if="s.game" class="text-xs text-muted-foreground">{{ s.game }}</p>
          </div>
          <div class="flex items-center gap-1.5 shrink-0">
            <span class="inline-block h-2 w-2 rounded-full" :class="statusColor(s.status)" />
            <span class="text-xs text-muted-foreground">{{ statusLabel(s.status) }}</span>
          </div>
        </div>
      </div>
    </UiCardContent>
  </UiCard>
</template>

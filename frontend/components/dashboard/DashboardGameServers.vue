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
      <UiCardTitle class="text-base">게임서버</UiCardTitle>
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

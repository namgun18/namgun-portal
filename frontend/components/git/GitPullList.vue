<script setup lang="ts">
const { pulls, pullState, loading, fetchPulls, selectPull } = useGit()

function timeAgo(dateStr: string) {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}분 전`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}시간 전`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}일 전`
  return new Date(dateStr).toLocaleDateString('ko-KR')
}

async function toggleState(state: 'open' | 'closed') {
  pullState.value = state
  await fetchPulls()
}
</script>

<template>
  <div class="flex-1 overflow-y-auto">
    <!-- Sub-header -->
    <div class="flex items-center gap-2 px-4 py-3 border-b">
      <div class="flex items-center border rounded-md">
        <button
          @click="toggleState('open')"
          class="px-3 py-1 text-xs font-medium rounded-l-md transition-colors"
          :class="pullState === 'open' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50'"
        >
          Open
        </button>
        <button
          @click="toggleState('closed')"
          class="px-3 py-1 text-xs font-medium rounded-r-md transition-colors"
          :class="pullState === 'closed' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50'"
        >
          Closed
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Empty -->
    <div v-else-if="pulls.length === 0" class="text-center py-12 text-sm text-muted-foreground">
      {{ pullState === 'open' ? '열린 PR이 없습니다' : '닫힌 PR이 없습니다' }}
    </div>

    <!-- List -->
    <div v-else>
      <button
        v-for="pr in pulls"
        :key="pr.number"
        @click="selectPull(pr.number)"
        class="w-full text-left px-4 py-3 border-b hover:bg-accent/30 transition-colors"
      >
        <div class="flex items-start gap-2">
          <svg v-if="pr.merged" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 text-purple-500 shrink-0 mt-0.5">
            <circle cx="18" cy="18" r="3" /><circle cx="6" cy="6" r="3" /><path d="M6 21V9a9 9 0 0 0 9 9" />
          </svg>
          <svg v-else-if="pr.state === 'open'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 text-green-500 shrink-0 mt-0.5">
            <circle cx="18" cy="18" r="3" /><circle cx="6" cy="6" r="3" /><path d="M13 6h3a2 2 0 0 1 2 2v7" /><line x1="6" y1="9" x2="6" y2="21" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 text-red-500 shrink-0 mt-0.5">
            <circle cx="18" cy="18" r="3" /><circle cx="6" cy="6" r="3" /><path d="M13 6h3a2 2 0 0 1 2 2v7" /><line x1="6" y1="9" x2="6" y2="21" />
          </svg>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-sm font-medium">{{ pr.title }}</span>
              <span
                v-for="label in pr.labels"
                :key="label.id"
                class="px-1.5 py-0.5 text-[10px] font-medium rounded-full"
                :style="{ backgroundColor: `#${label.color}20`, color: `#${label.color}`, border: `1px solid #${label.color}40` }"
              >
                {{ label.name }}
              </span>
            </div>
            <div class="text-xs text-muted-foreground mt-1">
              #{{ pr.number }} · {{ pr.user?.login }} · {{ timeAgo(pr.created_at) }}
              <span v-if="pr.head_branch && pr.base_branch" class="ml-1">
                <code class="bg-muted px-1 rounded text-[10px]">{{ pr.head_branch }}</code>
                →
                <code class="bg-muted px-1 rounded text-[10px]">{{ pr.base_branch }}</code>
              </span>
            </div>
          </div>
        </div>
      </button>
    </div>
  </div>
</template>

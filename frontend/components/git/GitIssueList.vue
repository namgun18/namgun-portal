<script setup lang="ts">
const { issues, issueState, loading, fetchIssues, selectIssue } = useGit()
const emit = defineEmits<{ createIssue: [] }>()

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
  issueState.value = state
  await fetchIssues()
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
          :class="issueState === 'open' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50'"
        >
          Open
        </button>
        <button
          @click="toggleState('closed')"
          class="px-3 py-1 text-xs font-medium rounded-r-md transition-colors"
          :class="issueState === 'closed' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50'"
        >
          Closed
        </button>
      </div>
      <div class="flex-1" />
      <button
        @click="emit('createIssue')"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
          <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
        </svg>
        새 이슈
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Empty -->
    <div v-else-if="issues.length === 0" class="text-center py-12 text-sm text-muted-foreground">
      {{ issueState === 'open' ? '열린 이슈가 없습니다' : '닫힌 이슈가 없습니다' }}
    </div>

    <!-- List -->
    <div v-else>
      <button
        v-for="issue in issues"
        :key="issue.number"
        @click="selectIssue(issue.number)"
        class="w-full text-left px-4 py-3 border-b hover:bg-accent/30 transition-colors"
      >
        <div class="flex items-start gap-2">
          <svg v-if="issue.state === 'open'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 text-green-500 shrink-0 mt-0.5">
            <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 text-purple-500 shrink-0 mt-0.5">
            <circle cx="12" cy="12" r="10" /><polyline points="16 12 12 8 8 12" /><line x1="12" y1="16" x2="12" y2="8" />
          </svg>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-sm font-medium">{{ issue.title }}</span>
              <span
                v-for="label in issue.labels"
                :key="label.id"
                class="px-1.5 py-0.5 text-[10px] font-medium rounded-full"
                :style="{ backgroundColor: `#${label.color}20`, color: `#${label.color}`, border: `1px solid #${label.color}40` }"
              >
                {{ label.name }}
              </span>
            </div>
            <div class="text-xs text-muted-foreground mt-1">
              #{{ issue.number }} · {{ issue.user?.login }} · {{ timeAgo(issue.created_at) }}
              <span v-if="issue.comments > 0"> · {{ issue.comments }}개 댓글</span>
            </div>
          </div>
        </div>
      </button>
    </div>
  </div>
</template>

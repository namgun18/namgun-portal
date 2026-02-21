<script setup lang="ts">
const { commits, loading } = useGit()

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

function shortSha(sha: string) {
  return sha.substring(0, 7)
}

function getInitial(name: string) {
  return (name || '?')[0].toUpperCase()
}

// Group commits by date
const groupedCommits = computed(() => {
  const groups: { date: string; commits: typeof commits.value }[] = []
  let currentDate = ''
  for (const c of commits.value) {
    const date = c.author?.date
      ? new Date(c.author.date).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })
      : '알 수 없음'
    if (date !== currentDate) {
      currentDate = date
      groups.push({ date, commits: [] })
    }
    groups[groups.length - 1].commits.push(c)
  }
  return groups
})
</script>

<template>
  <div class="flex-1 overflow-y-auto p-4">
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
    </div>

    <div v-else-if="commits.length === 0" class="text-center py-12 text-sm text-muted-foreground">
      커밋이 없습니다
    </div>

    <div v-else class="space-y-6">
      <div v-for="group in groupedCommits" :key="group.date">
        <!-- Date header -->
        <h3 class="text-sm font-semibold mb-3 flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-4 w-4 text-muted-foreground">
            <path fill="currentColor" d="M11.93 8.5a4.002 4.002 0 0 1-7.86 0H.75a.75.75 0 0 1 0-1.5h3.32a4.002 4.002 0 0 1 7.86 0h3.32a.75.75 0 0 1 0 1.5Zm-1.43-.25a2.5 2.5 0 1 0-5 0 2.5 2.5 0 0 0 5 0Z" />
          </svg>
          Commits on {{ group.date }}
        </h3>

        <!-- Commits in group -->
        <div class="border rounded-md overflow-hidden">
          <div
            v-for="(c, i) in group.commits"
            :key="c.sha"
            class="flex items-center gap-3 px-4 py-3 hover:bg-accent/20 transition-colors"
            :class="i < group.commits.length - 1 ? 'border-b' : ''"
          >
            <!-- Avatar -->
            <div class="w-7 h-7 rounded-full bg-muted flex items-center justify-center shrink-0 text-xs font-bold">
              {{ getInitial(c.author?.name || '') }}
            </div>

            <!-- Message + Author -->
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium truncate">{{ c.message.split('\n')[0] }}</p>
              <div class="flex items-center gap-1.5 mt-0.5 text-xs text-muted-foreground">
                <span class="font-medium text-foreground">{{ c.author?.name || 'unknown' }}</span>
                <span>committed {{ timeAgo(c.author?.date || '') }}</span>
              </div>
            </div>

            <!-- SHA badge -->
            <div class="flex items-center gap-1 shrink-0">
              <button
                class="inline-flex items-center gap-1 px-2 py-1 text-xs font-mono rounded-md border hover:bg-accent transition-colors"
                :title="c.sha"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-3 w-3">
                  <path fill="currentColor" d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 0 1 0 1.5h-1.5a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-1.5a.75.75 0 0 1 1.5 0v1.5A1.75 1.75 0 0 1 9.25 16h-7.5A1.75 1.75 0 0 1 0 14.25ZM5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0 1 14.25 11h-7.5A1.75 1.75 0 0 1 5 9.25Zm1.75-.25a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-7.5a.25.25 0 0 0-.25-.25Z" />
                </svg>
                {{ shortSha(c.sha) }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

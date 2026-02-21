<script setup lang="ts">
import { timeAgo } from '~/lib/date'

interface RecentCommit {
  repo_full_name: string
  repo_name: string
  sha: string
  message: string
  author_name: string
  author_date: string
}

const commits = ref<RecentCommit[]>([])
const loading = ref(true)

async function fetchRecentCommits() {
  try {
    commits.value = await $fetch<RecentCommit[]>('/api/git/recent-commits', {
      params: { limit: 5 },
    })
  } catch {
    // silent
  } finally {
    loading.value = false
  }
}

onMounted(fetchRecentCommits)

function shortSha(sha: string) {
  return sha.slice(0, 7)
}

function firstLine(msg: string) {
  return msg.split('\n')[0]
}
</script>

<template>
  <UiCard class="col-span-1 lg:col-span-2">
    <UiCardHeader class="pb-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 text-purple-500"><line x1="6" x2="6" y1="3" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></svg>
          <UiCardTitle class="text-base">최근 Git 활동</UiCardTitle>
        </div>
        <NuxtLink to="/git" class="text-xs text-primary hover:underline">전체 보기</NuxtLink>
      </div>
    </UiCardHeader>
    <UiCardContent>
      <!-- Loading -->
      <div v-if="loading" class="space-y-3">
        <div v-for="i in 3" :key="i" class="flex gap-3">
          <UiSkeleton class="h-4 w-16 shrink-0" />
          <UiSkeleton class="h-4 flex-1" />
        </div>
      </div>

      <!-- Empty -->
      <p v-else-if="commits.length === 0" class="text-sm text-muted-foreground">
        최근 커밋이 없습니다
      </p>

      <!-- Commit list -->
      <div v-else class="space-y-1">
        <div
          v-for="c in commits"
          :key="c.sha"
          class="flex items-start gap-3 rounded-md px-2 py-2 -mx-2"
        >
          <code class="mt-0.5 text-xs text-primary shrink-0">{{ shortSha(c.sha) }}</code>
          <div class="min-w-0 flex-1">
            <p class="text-sm truncate">{{ firstLine(c.message) }}</p>
            <div class="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
              <span>{{ c.repo_name }}</span>
              <span>&middot;</span>
              <span>{{ c.author_name }}</span>
              <span>&middot;</span>
              <span>{{ timeAgo(c.author_date) }}</span>
            </div>
          </div>
        </div>
      </div>
    </UiCardContent>
  </UiCard>
</template>

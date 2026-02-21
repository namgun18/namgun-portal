<script setup lang="ts">
import GitRepoCard from './GitRepoCard.vue'

const { repos, reposTotal, loading, searchQuery, fetchRepos, selectRepo } = useGit()

const page = ref(1)
const totalPages = computed(() => Math.ceil(reposTotal.value / 20))

async function search() {
  page.value = 1
  await fetchRepos(1)
}

async function changePage(p: number) {
  page.value = p
  await fetchRepos(p)
}
</script>

<template>
  <div class="flex-1 overflow-y-auto p-4">
    <!-- Search -->
    <div class="mb-4">
      <div class="flex items-center gap-3">
        <div class="relative flex-1">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground">
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            v-model="searchQuery"
            @keydown.enter="search"
            type="text"
            placeholder="Find a repository..."
            class="w-full h-9 pl-9 pr-3 text-sm rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <span class="text-sm text-muted-foreground shrink-0">
          {{ reposTotal }} repositories
        </span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-16">
      <div class="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Empty -->
    <div v-else-if="repos.length === 0" class="flex flex-col items-center justify-center py-16 text-center">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="h-12 w-12 text-muted-foreground/50 mb-3">
        <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
        <path d="M9 18c-4.51 2-5-2-7-2" />
      </svg>
      <p class="text-muted-foreground text-sm">저장소가 없습니다</p>
    </div>

    <!-- Grid -->
    <div v-else>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <GitRepoCard
          v-for="r in repos"
          :key="r.id"
          :repo="r"
          @select="selectRepo"
        />
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 mt-6">
        <button
          :disabled="page <= 1"
          @click="changePage(page - 1)"
          class="px-3 py-1.5 text-sm rounded-md border hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          이전
        </button>
        <span class="text-sm text-muted-foreground">{{ page }} / {{ totalPages }}</span>
        <button
          :disabled="page >= totalPages"
          @click="changePage(page + 1)"
          class="px-3 py-1.5 text-sm rounded-md border hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          다음
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import GitBranchSelector from './GitBranchSelector.vue'

const {
  currentView,
  selectedRepo,
  repoTab,
  commitCount,
  goBack,
  resetToRepoList,
  switchTab,
} = useGit()

const showBack = computed(() => currentView.value !== 'repo-list')
const showTabs = computed(() =>
  selectedRepo.value && !['repo-list'].includes(currentView.value),
)
</script>

<template>
  <div class="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-4 py-2 border-b bg-background">
    <!-- Back button -->
    <button
      v-if="showBack"
      @click="goBack"
      class="inline-flex items-center gap-1 px-2 py-1.5 text-sm font-medium rounded-md border hover:bg-accent transition-colors"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
        <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
      </svg>
      <span class="hidden sm:inline">뒤로</span>
    </button>

    <!-- Home button -->
    <button
      v-if="showBack"
      @click="resetToRepoList"
      class="inline-flex items-center gap-1 px-2 py-1.5 text-sm font-medium rounded-md border hover:bg-accent transition-colors"
      title="저장소 목록"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-4 w-4">
        <path fill="currentColor" d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.25.25 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z" />
      </svg>
    </button>

    <!-- Repo name -->
    <span v-if="selectedRepo" class="text-sm font-semibold truncate max-w-[200px]">
      {{ selectedRepo.full_name }}
    </span>

    <!-- Branch selector -->
    <GitBranchSelector v-if="selectedRepo && currentView !== 'repo-list'" />

    <!-- Gitea link -->
    <a
      :href="selectedRepo ? selectedRepo.html_url : 'https://git.namgun.or.kr'"
      target="_blank"
      rel="noopener"
      class="inline-flex items-center gap-1 px-2 py-1.5 text-xs font-medium text-muted-foreground rounded-md border hover:bg-accent hover:text-foreground transition-colors"
      title="Gitea에서 열기"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-3.5 w-3.5">
        <path fill="currentColor" d="M3.75 2h3.5a.75.75 0 0 1 0 1.5h-3.5a.25.25 0 0 0-.25.25v8.5c0 .138.112.25.25.25h8.5a.25.25 0 0 0 .25-.25v-3.5a.75.75 0 0 1 1.5 0v3.5A1.75 1.75 0 0 1 12.25 14h-8.5A1.75 1.75 0 0 1 2 12.25v-8.5C2 2.784 2.784 2 3.75 2Zm6.854-1h4.146a.25.25 0 0 1 .25.25v4.146a.25.25 0 0 1-.427.177L13.03 4.03 9.28 7.78a.751.751 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042l3.75-3.75-1.543-1.543A.25.25 0 0 1 10.604 1Z" />
      </svg>
      <span class="hidden sm:inline">Gitea</span>
    </a>

    <div class="flex-1" />

    <!-- Tabs with icons and counts -->
    <div v-if="showTabs" class="flex items-center border rounded-md overflow-hidden">
      <!-- Code tab -->
      <button
        @click="switchTab('code')"
        class="inline-flex items-center gap-1 px-2 sm:px-3 py-1.5 text-xs font-medium transition-colors"
        :class="repoTab === 'code' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50'"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-3.5 w-3.5">
          <path fill="currentColor" d="m11.28 3.22 4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.749.749 0 0 1-1.275-.326.749.749 0 0 1 .215-.734L13.94 8l-3.72-3.72a.749.749 0 0 1 .326-1.275.749.749 0 0 1 .734.215Zm-6.56 0a.751.751 0 0 1 1.042.018.751.751 0 0 1 .018 1.042L2.06 8l3.72 3.72a.749.749 0 0 1-.326 1.275.749.749 0 0 1-.734-.215L.47 8.53a.75.75 0 0 1 0-1.06Z" />
        </svg>
        <span class="hidden sm:inline">코드</span>
      </button>

      <!-- Issues tab -->
      <button
        @click="switchTab('issues')"
        class="inline-flex items-center gap-1 px-2 sm:px-3 py-1.5 text-xs font-medium transition-colors border-l"
        :class="repoTab === 'issues' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50'"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-3.5 w-3.5">
          <path fill="currentColor" d="M8 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z" /><path fill="currentColor" d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Z" />
        </svg>
        <span class="hidden sm:inline">이슈</span>
        <span
          v-if="selectedRepo && selectedRepo.open_issues_count > 0"
          class="px-1.5 py-0.5 text-[10px] font-medium rounded-full bg-muted"
        >
          {{ selectedRepo.open_issues_count }}
        </span>
      </button>

      <!-- PR tab -->
      <button
        @click="switchTab('pulls')"
        class="inline-flex items-center gap-1 px-2 sm:px-3 py-1.5 text-xs font-medium transition-colors border-l"
        :class="repoTab === 'pulls' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50'"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-3.5 w-3.5">
          <path fill="currentColor" d="M1.5 3.25a2.25 2.25 0 1 1 3 2.122v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.25 2.25 0 0 1 1.5 3.25Zm5.677-.177L9.573.677A.25.25 0 0 1 10 .854V2.5h1A2.5 2.5 0 0 1 13.5 5v5.628a2.251 2.251 0 1 1-1.5 0V5a1 1 0 0 0-1-1h-1v1.646a.25.25 0 0 1-.427.177L7.177 3.427a.25.25 0 0 1 0-.354ZM3.75 2.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm0 9.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm8.25.75a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0Z" />
        </svg>
        <span class="hidden sm:inline">PR</span>
      </button>

      <!-- Commits tab -->
      <button
        @click="switchTab('commits')"
        class="inline-flex items-center gap-1 px-2 sm:px-3 py-1.5 text-xs font-medium transition-colors border-l"
        :class="repoTab === 'commits' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50'"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-3.5 w-3.5">
          <path fill="currentColor" d="M11.93 8.5a4.002 4.002 0 0 1-7.86 0H.75a.75.75 0 0 1 0-1.5h3.32a4.002 4.002 0 0 1 7.86 0h3.32a.75.75 0 0 1 0 1.5Zm-1.43-.25a2.5 2.5 0 1 0-5 0 2.5 2.5 0 0 0 5 0Z" />
        </svg>
        <span class="hidden sm:inline">커밋</span>
        <span
          v-if="commitCount > 0"
          class="px-1.5 py-0.5 text-[10px] font-medium rounded-full bg-muted"
        >
          {{ commitCount }}+
        </span>
      </button>
    </div>
  </div>
</template>

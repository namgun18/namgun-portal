<script setup lang="ts">
import { LANG_COLORS } from '~/composables/useGit'
import GitBreadcrumb from './GitBreadcrumb.vue'
import GitFileTree from './GitFileTree.vue'
import GitMarkdownRenderer from './GitMarkdownRenderer.vue'

const {
  selectedRepo, loading, latestCommit, commitCount, cloneUrl,
  currentBranch, branches,
} = useGit()

const langColor = computed(() =>
  selectedRepo.value?.language ? (LANG_COLORS[selectedRepo.value.language] || '#8b949e') : '#8b949e'
)

const showClonePopup = ref(false)
const copied = ref(false)
const cloneDropdown = ref<HTMLElement | null>(null)
const cloneDropdownStyle = ref<Record<string, string>>({})

function updateDropdownPosition() {
  nextTick(() => {
    const btn = document.querySelector('[data-clone-btn]') as HTMLElement | null
    if (!btn) return
    const rect = btn.getBoundingClientRect()
    const dropdownWidth = 360
    let left = rect.right - dropdownWidth
    if (left < 8) left = 8
    cloneDropdownStyle.value = {
      top: `${rect.bottom + 4}px`,
      left: `${left}px`,
    }
  })
}

watch(showClonePopup, (v) => {
  if (v) updateDropdownPosition()
})

function copyCloneUrl() {
  navigator.clipboard.writeText(cloneUrl.value)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

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

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>

<template>
  <div v-if="selectedRepo" class="flex-1 overflow-y-auto">
    <div class="flex flex-col lg:flex-row gap-6 px-4 pt-4 pb-6">
      <!-- Main column -->
      <div class="flex-1 min-w-0">
        <!-- Clone button -->
        <div class="flex items-center justify-end mb-4">
          <div class="relative">
            <button
              data-clone-btn
              @click="showClonePopup = !showClonePopup"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md bg-green-600 text-white hover:bg-green-700 transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-4 w-4">
                <path fill="currentColor" d="M4.72 3.22a.75.75 0 0 1 1.06 0l3.25 3.25a.75.75 0 0 1 0 1.06l-3.25 3.25a.75.75 0 0 1-1.06-1.06L7.44 7 4.72 4.28a.75.75 0 0 1 0-1.06Zm3.5 0a.75.75 0 0 1 1.06 0l3.25 3.25a.75.75 0 0 1 0 1.06l-3.25 3.25a.75.75 0 0 1-1.06-1.06L10.94 7 8.22 4.28a.75.75 0 0 1 0-1.06Z" />
              </svg>
              Code
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-4 w-4 -mr-0.5">
                <path fill="currentColor" d="m4.427 7.427 3.396 3.396a.25.25 0 0 0 .354 0l3.396-3.396A.25.25 0 0 0 11.396 7H4.604a.25.25 0 0 0-.177.427Z" />
              </svg>
            </button>

            <!-- Clone dropdown -->
            <Teleport to="body">
              <div v-if="showClonePopup" class="fixed inset-0 z-[99]" @click="showClonePopup = false" />
              <div
                v-if="showClonePopup"
                ref="cloneDropdown"
                class="fixed z-[100] w-[360px] rounded-lg border bg-popover shadow-xl"
                :style="cloneDropdownStyle"
              >
                <!-- Header -->
                <div class="flex items-center justify-between px-3 py-2 border-b">
                  <span class="text-xs font-semibold">Clone</span>
                  <button @click="showClonePopup = false" class="p-0.5 rounded hover:bg-accent transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-3.5 w-3.5 text-muted-foreground">
                      <path fill="currentColor" d="M3.72 3.72a.75.75 0 0 1 1.06 0L8 6.94l3.22-3.22a.749.749 0 0 1 1.275.326.749.749 0 0 1-.215.734L9.06 8l3.22 3.22a.749.749 0 0 1-.326 1.275.749.749 0 0 1-.734-.215L8 9.06l-3.22 3.22a.751.751 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042L6.94 8 3.72 4.78a.75.75 0 0 1 0-1.06Z" />
                    </svg>
                  </button>
                </div>
                <!-- HTTPS section -->
                <div class="p-3">
                  <div class="flex items-center gap-2 mb-2">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-4 w-4 text-muted-foreground">
                      <path fill="currentColor" d="M2 2.75A2.75 2.75 0 0 1 4.75 0h8.5A2.75 2.75 0 0 1 16 2.75v10.5A2.75 2.75 0 0 1 13.25 16h-8.5A2.75 2.75 0 0 1 2 13.25Zm1.75-.25c-.69 0-1.25.56-1.25 1.25v10.5c0 .69.56 1.25 1.25 1.25h8.5c.69 0 1.25-.56 1.25-1.25V2.75c0-.69-.56-1.25-1.25-1.25ZM8 10a2 2 0 1 1 0-4 2 2 0 0 1 0 4Zm0-2.5a.5.5 0 1 0 0 1 .5.5 0 0 0 0-1Z" />
                    </svg>
                    <span class="text-xs font-semibold">HTTPS</span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <input
                      :value="cloneUrl"
                      readonly
                      class="flex-1 h-8 px-2.5 text-xs font-mono rounded-md border bg-muted/50 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                      @focus="($event.target as HTMLInputElement).select()"
                    />
                    <button
                      @click="copyCloneUrl"
                      class="inline-flex items-center justify-center h-8 w-8 rounded-md border hover:bg-accent transition-colors shrink-0"
                      :title="copied ? '복사됨!' : 'URL 복사'"
                    >
                      <svg v-if="!copied" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-3.5 w-3.5">
                        <path fill="currentColor" d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 0 1 0 1.5h-1.5a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-1.5a.75.75 0 0 1 1.5 0v1.5A1.75 1.75 0 0 1 9.25 16h-7.5A1.75 1.75 0 0 1 0 14.25ZM5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0 1 14.25 11h-7.5A1.75 1.75 0 0 1 5 9.25Zm1.75-.25a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-7.5a.25.25 0 0 0-.25-.25Z" />
                      </svg>
                      <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-3.5 w-3.5 text-green-500">
                        <path fill="currentColor" d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z" />
                      </svg>
                    </button>
                  </div>
                  <p class="mt-2 text-[11px] text-muted-foreground leading-relaxed">
                    Use Git or checkout with SVN using the web URL.
                  </p>
                </div>
              </div>
            </Teleport>
          </div>
        </div>

        <!-- Latest commit bar -->
        <div v-if="latestCommit" class="flex items-center gap-3 px-4 py-2.5 rounded-t-md border border-b-0 bg-muted/30">
          <div class="w-6 h-6 rounded-full bg-muted flex items-center justify-center shrink-0">
            <span class="text-[10px] font-bold uppercase">
              {{ (latestCommit.author?.name || '?')[0] }}
            </span>
          </div>
          <div class="flex-1 min-w-0 flex items-center gap-2">
            <span class="text-xs font-semibold shrink-0">{{ latestCommit.author?.name }}</span>
            <span class="text-xs text-muted-foreground truncate">{{ latestCommit.message.split('\n')[0] }}</span>
          </div>
          <code class="text-[11px] font-mono text-muted-foreground shrink-0">{{ latestCommit.sha.substring(0, 7) }}</code>
          <span class="text-xs text-muted-foreground shrink-0">{{ timeAgo(latestCommit.author?.date || '') }}</span>
          <div class="flex items-center gap-1 text-xs text-muted-foreground shrink-0 border-l pl-3 ml-1">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-3.5 w-3.5">
              <path fill="currentColor" d="M11.93 8.5a4.002 4.002 0 0 1-7.86 0H.75a.75.75 0 0 1 0-1.5h3.32a4.002 4.002 0 0 1 7.86 0h3.32a.75.75 0 0 1 0 1.5Zm-1.43-.25a2.5 2.5 0 1 0-5 0 2.5 2.5 0 0 0 5 0Z" />
            </svg>
            <span class="font-medium">{{ commitCount }}+ commits</span>
          </div>
        </div>

        <!-- Breadcrumb -->
        <GitBreadcrumb />

        <!-- Loading -->
        <div v-if="loading" class="flex items-center justify-center py-12">
          <div class="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>

        <!-- File tree -->
        <div v-else>
          <GitFileTree :has-commit-header="!!latestCommit" />
        </div>

        <!-- README -->
        <div v-if="selectedRepo.readme && !loading" class="mt-4">
          <div class="border rounded-md overflow-hidden">
            <div class="px-4 py-2.5 border-b bg-muted/30 text-sm font-medium flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-4 w-4">
                <path fill="currentColor" d="M0 1.75A.75.75 0 0 1 .75 1h4.253c1.227 0 2.317.59 3 1.501A3.743 3.743 0 0 1 11.006 1h4.245a.75.75 0 0 1 .75.75v10.5a.75.75 0 0 1-.75.75h-4.507a2.25 2.25 0 0 0-1.591.659l-.622.621a.75.75 0 0 1-1.06 0l-.622-.621A2.25 2.25 0 0 0 5.258 13H.75a.75.75 0 0 1-.75-.75Zm7.251 10.324.004-5.073-.002-2.253A2.25 2.25 0 0 0 5.003 2.5H1.5v9h3.757a3.75 3.75 0 0 1 1.994.574ZM8.755 4.75l-.004 7.322a3.752 3.752 0 0 1 1.992-.572H14.5v-9h-3.495a2.25 2.25 0 0 0-2.25 2.25Z" />
              </svg>
              README.md
            </div>
            <div class="p-5">
              <GitMarkdownRenderer :content="selectedRepo.readme" />
            </div>
          </div>
        </div>
      </div>

      <!-- About sidebar (desktop) -->
      <div class="hidden lg:block w-72 shrink-0">
        <div class="sticky top-4">
          <h3 class="text-sm font-semibold mb-2">About</h3>
          <p v-if="selectedRepo.description" class="text-sm text-muted-foreground leading-relaxed mb-4">
            {{ selectedRepo.description }}
          </p>
          <p v-else class="text-sm text-muted-foreground italic mb-4">설명 없음</p>

          <div class="space-y-2.5 text-sm">
            <!-- Stars -->
            <div class="flex items-center gap-2 text-muted-foreground">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-4 w-4">
                <path fill="currentColor" d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z" />
              </svg>
              <span><strong>{{ selectedRepo.stars_count }}</strong> stars</span>
            </div>
            <!-- Forks -->
            <div class="flex items-center gap-2 text-muted-foreground">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-4 w-4">
                <path fill="currentColor" d="M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 2.25h-1.5v2.128a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878a2.25 2.25 0 1 1 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z" />
              </svg>
              <span><strong>{{ selectedRepo.forks_count }}</strong> forks</span>
            </div>
            <!-- Issues -->
            <div v-if="selectedRepo.open_issues_count > 0" class="flex items-center gap-2 text-muted-foreground">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-4 w-4">
                <path fill="currentColor" d="M8 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z" /><path fill="currentColor" d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Z" />
              </svg>
              <span><strong>{{ selectedRepo.open_issues_count }}</strong> open issues</span>
            </div>
          </div>

          <div class="border-t mt-4 pt-4 space-y-2.5 text-sm">
            <!-- Language -->
            <div v-if="selectedRepo.language" class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full shrink-0" :style="{ backgroundColor: langColor }" />
              <span>{{ selectedRepo.language }}</span>
            </div>
            <!-- Size -->
            <div class="flex items-center gap-2 text-muted-foreground">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-4 w-4">
                <path fill="currentColor" d="M3.75 1.5a.25.25 0 0 0-.25.25v11.5c0 .138.112.25.25.25h8.5a.25.25 0 0 0 .25-.25V6H9.75A1.75 1.75 0 0 1 8 4.25V1.5ZM14 13.25v-7.5a.75.75 0 0 0-.22-.53l-4-4A.75.75 0 0 0 9.25 1H3.75A1.75 1.75 0 0 0 2 2.75v10.5c0 .966.784 1.75 1.75 1.75h8.5A1.75 1.75 0 0 0 14 13.25Z" />
              </svg>
              <span>{{ formatSize(selectedRepo.size * 1024) }}</span>
            </div>
            <!-- Branch -->
            <div class="flex items-center gap-2 text-muted-foreground">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-4 w-4">
                <path fill="currentColor" d="M9.5 3.25a2.25 2.25 0 1 1 3 2.122V6A2.5 2.5 0 0 1 10 8.5H6a1 1 0 0 0-1 1v1.128a2.251 2.251 0 1 1-1.5 0V5.372a2.25 2.25 0 1 1 1.5 0v1.836A2.493 2.493 0 0 1 6 7h4a1 1 0 0 0 1-1v-.628A2.25 2.25 0 0 1 9.5 3.25Zm-6 0a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0Zm8.25-.75a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5ZM4.25 12a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Z" />
              </svg>
              <span>{{ branches.length }} branch{{ branches.length !== 1 ? 'es' : '' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

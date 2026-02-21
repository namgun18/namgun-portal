<script setup lang="ts">
import type { RepoSummary } from '~/composables/useGit'
import { LANG_COLORS } from '~/composables/useGit'

const props = defineProps<{ repo: RepoSummary }>()
const emit = defineEmits<{ select: [owner: string, repo: string] }>()

const langColor = computed(() => LANG_COLORS[props.repo.language] || '#8b949e')

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
</script>

<template>
  <button
    @click="emit('select', repo.owner.login, repo.name)"
    class="text-left p-4 rounded-lg border hover:border-primary/50 hover:bg-accent/20 transition-all group"
  >
    <!-- Repo icon + name -->
    <div class="flex items-start gap-2.5 mb-2">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-4 w-4 text-muted-foreground shrink-0 mt-0.5">
        <path fill="currentColor" d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.25.25 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z" />
      </svg>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-1.5 flex-wrap">
          <span class="text-sm font-semibold text-primary group-hover:underline truncate">{{ repo.full_name }}</span>
          <span
            class="shrink-0 px-1.5 py-0.5 text-[10px] font-medium rounded-full border"
            :class="repo.private
              ? 'border-amber-500/40 text-amber-600 dark:text-amber-400'
              : 'border-muted-foreground/30 text-muted-foreground'"
          >
            {{ repo.private ? 'Private' : 'Public' }}
          </span>
        </div>
        <p v-if="repo.description" class="text-xs text-muted-foreground mt-1.5 line-clamp-2 leading-relaxed">
          {{ repo.description }}
        </p>
      </div>
    </div>

    <div class="flex items-center gap-3 text-xs text-muted-foreground mt-3">
      <span v-if="repo.language" class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded-full shrink-0" :style="{ backgroundColor: langColor }" />
        {{ repo.language }}
      </span>
      <span v-if="repo.stars_count > 0" class="flex items-center gap-1">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-3.5 w-3.5">
          <path fill="currentColor" d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z" />
        </svg>
        {{ repo.stars_count }}
      </span>
      <span v-if="repo.forks_count > 0" class="flex items-center gap-1">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-3.5 w-3.5">
          <path fill="currentColor" d="M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 2.25h-1.5v2.128a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878a2.25 2.25 0 1 1 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z" />
        </svg>
        {{ repo.forks_count }}
      </span>
      <span class="ml-auto">{{ timeAgo(repo.updated_at) }}</span>
    </div>
  </button>
</template>

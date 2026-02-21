<script setup lang="ts">
import GitMarkdownRenderer from './GitMarkdownRenderer.vue'

const { selectedIssue, issueComments, loading, addIssueComment } = useGit()

const newComment = ref('')
const submitting = ref(false)

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

async function submitComment() {
  if (!newComment.value.trim() || !selectedIssue.value) return
  submitting.value = true
  try {
    await addIssueComment(selectedIssue.value.number, newComment.value)
    newComment.value = ''
  } catch (e: any) {
    console.error('Comment failed:', e)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div v-if="selectedIssue" class="flex-1 overflow-y-auto">
    <!-- Issue header -->
    <div class="px-4 pt-4 pb-3 border-b">
      <h2 class="text-lg font-semibold">
        {{ selectedIssue.title }}
        <span class="text-muted-foreground font-normal">#{{ selectedIssue.number }}</span>
      </h2>
      <div class="flex items-center gap-2 mt-2">
        <span
          class="px-2 py-0.5 text-xs font-medium rounded-full"
          :class="selectedIssue.state === 'open' ? 'bg-green-500/10 text-green-600' : 'bg-purple-500/10 text-purple-600'"
        >
          {{ selectedIssue.state === 'open' ? 'Open' : 'Closed' }}
        </span>
        <span class="text-xs text-muted-foreground">
          {{ selectedIssue.user?.login }} · {{ timeAgo(selectedIssue.created_at) }}
        </span>
      </div>
    </div>

    <!-- Body -->
    <div v-if="selectedIssue.body" class="px-4 py-4 border-b">
      <GitMarkdownRenderer :content="selectedIssue.body" />
    </div>

    <!-- Comments -->
    <div v-if="issueComments.length > 0">
      <div
        v-for="comment in issueComments"
        :key="comment.id"
        class="px-4 py-4 border-b"
      >
        <div class="flex items-center gap-2 mb-2 text-xs text-muted-foreground">
          <span class="font-medium text-foreground">{{ comment.user?.login }}</span>
          <span>{{ timeAgo(comment.created_at) }}</span>
        </div>
        <GitMarkdownRenderer :content="comment.body" />
      </div>
    </div>

    <!-- Add comment -->
    <div class="px-4 py-4">
      <textarea
        v-model="newComment"
        placeholder="댓글을 작성하세요... (마크다운 지원)"
        class="w-full h-24 px-3 py-2 text-sm rounded-md border bg-background resize-none focus:outline-none focus:ring-2 focus:ring-ring"
      />
      <div class="flex justify-end mt-2">
        <button
          @click="submitComment"
          :disabled="!newComment.trim() || submitting"
          class="px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ submitting ? '전송 중...' : '댓글 작성' }}
        </button>
      </div>
    </div>
  </div>
</template>

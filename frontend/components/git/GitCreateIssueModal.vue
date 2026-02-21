<script setup lang="ts">
const emit = defineEmits<{ close: [] }>()
const { createIssue } = useGit()

const title = ref('')
const body = ref('')
const submitting = ref(false)

async function submit() {
  if (!title.value.trim()) return
  submitting.value = true
  try {
    await createIssue(title.value, body.value)
    emit('close')
  } catch (e: any) {
    console.error('Create issue failed:', e)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <!-- Backdrop -->
    <div class="absolute inset-0 bg-black/50" @click="emit('close')" />

    <!-- Modal -->
    <div class="relative w-full max-w-lg bg-background rounded-lg border shadow-xl">
      <div class="flex items-center justify-between px-4 py-3 border-b">
        <h3 class="text-sm font-semibold">새 이슈 생성</h3>
        <button
          @click="emit('close')"
          class="inline-flex items-center justify-center h-8 w-8 rounded-md hover:bg-accent transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <div class="p-4 space-y-3">
        <input
          v-model="title"
          type="text"
          placeholder="이슈 제목"
          class="w-full h-9 px-3 text-sm rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <textarea
          v-model="body"
          placeholder="설명 (선택, 마크다운 지원)"
          class="w-full h-32 px-3 py-2 text-sm rounded-md border bg-background resize-none focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      <div class="flex justify-end gap-2 px-4 py-3 border-t">
        <button
          @click="emit('close')"
          class="px-4 py-2 text-sm font-medium rounded-md border hover:bg-accent transition-colors"
        >
          취소
        </button>
        <button
          @click="submit"
          :disabled="!title.trim() || submitting"
          class="px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ submitting ? '생성 중...' : '이슈 생성' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FileItem } from '~/composables/useFiles'

const props = defineProps<{
  item: FileItem
}>()

const emit = defineEmits<{
  close: []
}>()

const { createShareLink } = useFiles()

const expiresIn = ref<string>('')
const oneTime = ref(false)
const creating = ref(false)
const shareUrl = ref<string | null>(null)
const copied = ref(false)

async function handleCreate() {
  creating.value = true
  try {
    const result = await createShareLink(props.item.path, expiresIn.value || undefined, oneTime.value)
    shareUrl.value = result.url
  } catch (e: any) {
    alert(e?.data?.detail || '공유 링크 생성 실패')
  } finally {
    creating.value = false
  }
}

async function copyUrl() {
  if (!shareUrl.value) return
  await navigator.clipboard.writeText(shareUrl.value)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50" @click.self="emit('close')">
    <div class="bg-background rounded-t-xl sm:rounded-lg shadow-xl w-full sm:max-w-md sm:mx-4">
      <!-- Header -->
      <div class="flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4 border-b">
        <h2 class="text-base sm:text-lg font-semibold">공유 링크 생성</h2>
        <button @click="emit('close')" class="h-8 w-8 flex items-center justify-center rounded-md hover:bg-accent">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <div class="p-4 sm:p-6 space-y-4">
        <div>
          <p class="text-sm text-muted-foreground">파일</p>
          <p class="text-sm font-medium">{{ item.name }}</p>
        </div>

        <!-- Generated URL -->
        <div v-if="shareUrl">
          <label class="text-sm text-muted-foreground block mb-1">공유 링크</label>
          <div class="flex gap-2">
            <input
              :value="shareUrl"
              readonly
              class="flex-1 px-3 py-2 text-sm bg-muted rounded-md border focus:outline-none"
              @click="($event.target as HTMLInputElement).select()"
            />
            <button
              @click="copyUrl"
              class="px-3 py-2 text-sm rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shrink-0"
            >
              {{ copied ? '복사됨!' : '복사' }}
            </button>
          </div>
        </div>

        <!-- Options (before creation) -->
        <template v-else>
          <div>
            <label class="text-sm text-muted-foreground block mb-1">만료 시간</label>
            <select v-model="expiresIn" class="w-full px-3 py-2 text-sm bg-background border rounded-md focus:outline-none focus:ring-1 focus:ring-primary">
              <option value="">무제한</option>
              <option value="1h">1시간</option>
              <option value="1d">1일</option>
              <option value="7d">7일</option>
            </select>
          </div>

          <label class="flex items-center gap-2 text-sm cursor-pointer">
            <input v-model="oneTime" type="checkbox" class="rounded border-muted-foreground/30" />
            1회성 다운로드 (한 번 다운로드 후 만료)
          </label>
        </template>
      </div>

      <!-- Footer -->
      <div class="flex justify-end gap-2 px-4 sm:px-6 py-3 border-t">
        <button
          @click="emit('close')"
          class="px-4 py-2 text-sm rounded-md hover:bg-accent transition-colors"
        >
          {{ shareUrl ? '닫기' : '취소' }}
        </button>
        <button
          v-if="!shareUrl"
          @click="handleCreate"
          :disabled="creating"
          class="px-4 py-2 text-sm rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          {{ creating ? '생성 중...' : '링크 생성' }}
        </button>
      </div>
      <div class="h-safe-area-inset-bottom sm:hidden" />
    </div>
  </div>
</template>

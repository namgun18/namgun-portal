<script setup lang="ts">
import type { FileItem } from '~/composables/useFiles'

const props = defineProps<{
  item: FileItem
}>()

const emit = defineEmits<{
  close: []
}>()

const { getPreviewUrl, downloadFile } = useFiles()

const textContent = ref<string | null>(null)
const loadingText = ref(false)

const previewType = computed(() => {
  const mime = props.item.mime_type || ''
  if (mime.startsWith('image/')) return 'image'
  if (mime === 'application/pdf') return 'pdf'
  // Check extension for text files
  const ext = props.item.name.split('.').pop()?.toLowerCase() || ''
  const textExts = ['txt', 'md', 'csv', 'json', 'xml', 'yaml', 'yml', 'py', 'js', 'ts', 'html', 'css', 'sh', 'vue', 'jsx', 'tsx', 'sql', 'go', 'rs', 'java', 'log', 'ini', 'toml', 'cfg', 'conf', 'env']
  if (textExts.includes(ext)) return 'text'
  return null
})

async function loadTextPreview() {
  if (previewType.value !== 'text') return
  loadingText.value = true
  try {
    const data = await $fetch<{ type: string; content: string; name: string }>(getPreviewUrl(props.item.path))
    textContent.value = data.content
  } catch {
    textContent.value = '미리보기를 불러올 수 없습니다.'
  } finally {
    loadingText.value = false
  }
}

onMounted(() => {
  if (previewType.value === 'text') loadTextPreview()
})
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60" @click.self="emit('close')">
    <div class="bg-background rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] mx-4 flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-3 border-b shrink-0">
        <h2 class="text-sm font-medium truncate">{{ item.name }}</h2>
        <div class="flex items-center gap-2">
          <button
            @click="downloadFile(item.path)"
            class="h-8 w-8 flex items-center justify-center rounded-md hover:bg-accent"
            title="다운로드"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" />
            </svg>
          </button>
          <button @click="emit('close')" class="h-8 w-8 flex items-center justify-center rounded-md hover:bg-accent">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-auto p-4 min-h-0">
        <!-- Image -->
        <div v-if="previewType === 'image'" class="flex items-center justify-center h-full">
          <img
            :src="getPreviewUrl(item.path)"
            :alt="item.name"
            class="max-w-full max-h-full object-contain rounded"
          />
        </div>

        <!-- PDF -->
        <div v-else-if="previewType === 'pdf'" class="h-full">
          <iframe
            :src="getPreviewUrl(item.path)"
            class="w-full h-full min-h-[60vh] rounded border"
          />
        </div>

        <!-- Text -->
        <div v-else-if="previewType === 'text'">
          <div v-if="loadingText" class="flex items-center justify-center h-40">
            <div class="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
          <pre v-else class="text-sm bg-muted/30 rounded-lg p-4 overflow-auto max-h-[70vh] whitespace-pre-wrap break-words font-mono">{{ textContent }}</pre>
        </div>

        <!-- Unsupported -->
        <div v-else class="flex flex-col items-center justify-center h-40 text-muted-foreground">
          <p class="text-sm">이 파일 형식은 미리보기를 지원하지 않습니다.</p>
          <button
            @click="downloadFile(item.path)"
            class="mt-3 px-4 py-2 text-sm rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            다운로드
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

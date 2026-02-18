<script setup lang="ts">
const emit = defineEmits<{
  close: []
}>()

const { uploadFiles, currentPath } = useFiles()

const isDragging = ref(false)
const uploading = ref(false)
const results = ref<{ name: string; ok: boolean; error?: string }[]>([])
const fileInput = ref<HTMLInputElement>()

function handleDragOver(e: DragEvent) {
  e.preventDefault()
  isDragging.value = true
}

function handleDragLeave() {
  isDragging.value = false
}

async function handleDrop(e: DragEvent) {
  e.preventDefault()
  isDragging.value = false
  const files = Array.from(e.dataTransfer?.files || [])
  if (files.length) await doUpload(files)
}

function triggerFileInput() {
  fileInput.value?.click()
}

async function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  const files = Array.from(input.files || [])
  if (files.length) await doUpload(files)
  input.value = ''
}

async function doUpload(files: File[]) {
  uploading.value = true
  results.value = []
  try {
    results.value = await uploadFiles(files)
  } finally {
    uploading.value = false
  }
}

const hasErrors = computed(() => results.value.some(r => !r.ok))
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50" @click.self="emit('close')">
    <div class="bg-background rounded-t-xl sm:rounded-lg shadow-xl w-full sm:max-w-lg sm:mx-4">
      <!-- Header -->
      <div class="flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4 border-b">
        <h2 class="text-base sm:text-lg font-semibold">파일 업로드</h2>
        <button @click="emit('close')" class="h-8 w-8 flex items-center justify-center rounded-md hover:bg-accent">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <div class="p-4 sm:p-6">
        <p class="text-sm text-muted-foreground mb-3 sm:mb-4">
          업로드 위치: <span class="font-medium text-foreground">{{ currentPath || '/' }}</span>
        </p>

        <!-- Drop zone -->
        <div
          @dragover="handleDragOver"
          @dragleave="handleDragLeave"
          @drop="handleDrop"
          @click="triggerFileInput"
          class="border-2 border-dashed rounded-lg p-6 sm:p-8 text-center cursor-pointer transition-colors"
          :class="isDragging ? 'border-primary bg-primary/5' : 'border-muted-foreground/30 hover:border-primary/50'"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="h-10 w-10 mx-auto mb-3 text-muted-foreground">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          <p v-if="isDragging" class="text-sm text-primary font-medium">여기에 놓으세요</p>
          <template v-else>
            <p class="text-sm text-muted-foreground">파일을 드래그하거나 클릭하여 선택</p>
            <p class="text-xs text-muted-foreground/70 mt-1">최대 1GB</p>
          </template>
        </div>

        <input ref="fileInput" type="file" multiple class="hidden" @change="handleFileSelect" />

        <!-- Upload progress -->
        <div v-if="uploading" class="mt-4 text-center">
          <div class="inline-block h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p class="text-sm text-muted-foreground mt-2">업로드 중...</p>
        </div>

        <!-- Results -->
        <div v-if="results.length > 0" class="mt-4 space-y-2">
          <div
            v-for="r in results"
            :key="r.name"
            class="flex items-center gap-2 text-sm px-3 py-2 rounded-md"
            :class="r.ok ? 'bg-green-500/10 text-green-700 dark:text-green-400' : 'bg-destructive/10 text-destructive'"
          >
            <svg v-if="r.ok" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4 shrink-0">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4 shrink-0">
              <circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" />
            </svg>
            <span class="truncate">{{ r.name }}</span>
            <span v-if="r.error" class="text-xs ml-auto shrink-0">{{ r.error }}</span>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex justify-end px-4 sm:px-6 py-3 border-t">
        <button
          @click="emit('close')"
          class="px-4 py-2 text-sm rounded-md hover:bg-accent transition-colors"
        >
          닫기
        </button>
      </div>
      <div class="h-safe-area-inset-bottom sm:hidden" />
    </div>
  </div>
</template>

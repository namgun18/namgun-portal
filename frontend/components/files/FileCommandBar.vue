<script setup lang="ts">
const emit = defineEmits<{
  upload: []
  newFolder: []
}>()

const { viewMode, selectedItems, deleteItems, downloadFile } = useFiles()
const showNewMenu = ref(false)

function toggleView() {
  viewMode.value = viewMode.value === 'list' ? 'grid' : 'list'
}

async function handleDeleteSelected() {
  if (selectedItems.value.size === 0) return
  if (!confirm(`${selectedItems.value.size}개 항목을 삭제하시겠습니까?`)) return
  await deleteItems([...selectedItems.value])
}

async function handleDownloadSelected() {
  for (const path of selectedItems.value) {
    downloadFile(path)
  }
}
</script>

<template>
  <div class="flex items-center gap-2 px-4 py-2 border-b bg-background">
    <!-- New button -->
    <div class="relative">
      <button
        @click="showNewMenu = !showNewMenu"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
          <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
        </svg>
        새로만들기
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3 w-3">
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>
      <div
        v-if="showNewMenu"
        v-click-outside="() => showNewMenu = false"
        class="absolute top-full left-0 mt-1 w-40 bg-popover border rounded-md shadow-md z-50 py-1"
      >
        <button
          @click="emit('newFolder'); showNewMenu = false"
          class="w-full px-3 py-2 text-sm text-left hover:bg-accent transition-colors flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
            <path d="M12 10v6M9 13h6" />
            <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
          </svg>
          새 폴더
        </button>
      </div>
    </div>

    <!-- Upload -->
    <button
      @click="emit('upload')"
      class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md border hover:bg-accent transition-colors"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
      </svg>
      업로드
    </button>

    <!-- Bulk actions -->
    <template v-if="selectedItems.size > 0">
      <div class="h-5 w-px bg-border mx-1" />
      <button
        @click="handleDownloadSelected"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md hover:bg-accent transition-colors"
        title="다운로드"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" />
        </svg>
      </button>
      <button
        @click="handleDeleteSelected"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md hover:bg-destructive/10 text-destructive transition-colors"
        title="삭제"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
          <polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
        </svg>
      </button>
      <span class="text-xs text-muted-foreground">{{ selectedItems.size }}개 선택됨</span>
    </template>

    <div class="flex-1" />

    <!-- View toggle -->
    <button
      @click="toggleView"
      class="inline-flex items-center justify-center h-8 w-8 rounded-md hover:bg-accent transition-colors"
      :title="viewMode === 'list' ? '타일 보기' : '목록 보기'"
    >
      <!-- List icon -->
      <svg v-if="viewMode === 'grid'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
        <line x1="8" y1="6" x2="21" y2="6" /><line x1="8" y1="12" x2="21" y2="12" /><line x1="8" y1="18" x2="21" y2="18" /><line x1="3" y1="6" x2="3.01" y2="6" /><line x1="3" y1="12" x2="3.01" y2="12" /><line x1="3" y1="18" x2="3.01" y2="18" />
      </svg>
      <!-- Grid icon -->
      <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
        <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" />
      </svg>
    </button>
  </div>
</template>

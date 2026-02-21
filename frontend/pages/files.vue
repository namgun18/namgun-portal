<script setup lang="ts">
import type { FileItem } from '~/composables/useFiles'

definePageMeta({ layout: 'default' })

const {
  viewMode,
  fetchFiles,
  fetchStorageInfo,
  downloadFile,
  deleteItems,
  renameItem,
} = useFiles()

// Modals state
const showUpload = ref(false)
const showNewFolder = ref(false)
const newFolderName = ref('')
const previewFile = ref<FileItem | null>(null)
const shareFile = ref<FileItem | null>(null)
const contextMenu = ref<{ item: FileItem; x: number; y: number } | null>(null)
const detailItem = ref<FileItem | null>(null)
const showMobileSidebar = ref(false)

// Drag overlay
const isDragOver = ref(false)

onMounted(() => {
  fetchFiles()
  fetchStorageInfo()
})

// New folder
const { createFolder } = useFiles()
async function handleNewFolder() {
  showNewFolder.value = true
  newFolderName.value = ''
}

async function confirmNewFolder() {
  if (!newFolderName.value.trim()) return
  try {
    await createFolder(newFolderName.value.trim())
    showNewFolder.value = false
  } catch (e: any) {
    alert(e?.data?.detail || '폴더 생성 실패')
  }
}

// File select (open detail panel)
function handleSelect(item: FileItem) {
  detailItem.value = item
}

// Context menu
function handleContextMenu(e: MouseEvent, item: FileItem) {
  contextMenu.value = { item, x: e.clientX, y: e.clientY }
}

// Actions
async function handleDelete(item: FileItem) {
  if (!confirm(`"${item.name}"을(를) 삭제하시겠습니까?`)) return
  try {
    await deleteItems([item.path])
    if (detailItem.value?.path === item.path) detailItem.value = null
  } catch (e: any) {
    alert(e?.data?.detail || '삭제 실패')
  }
}

async function handleRename(item: FileItem) {
  const newName = prompt('새 이름을 입력하세요:', item.name)
  if (!newName || newName === item.name) return
  try {
    await renameItem(item.path, newName)
    detailItem.value = null
  } catch (e: any) {
    alert(e?.data?.detail || '이름 변경 실패')
  }
}

// Drag-drop upload on entire area
const { uploadFiles } = useFiles()
function handleDragOver(e: DragEvent) {
  e.preventDefault()
  isDragOver.value = true
}
function handleDragLeave() {
  isDragOver.value = false
}
async function handleDrop(e: DragEvent) {
  e.preventDefault()
  isDragOver.value = false
  const files = Array.from(e.dataTransfer?.files || [])
  if (files.length) {
    await uploadFiles(files)
  }
}
</script>

<template>
  <div
    class="flex h-full overflow-hidden relative"
    @dragover="handleDragOver"
    @dragleave="handleDragLeave"
    @drop="handleDrop"
  >
    <!-- Drag overlay -->
    <div
      v-if="isDragOver"
      class="absolute inset-0 z-40 bg-primary/10 border-2 border-dashed border-primary rounded-lg flex items-center justify-center pointer-events-none"
    >
      <div class="text-center">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="h-12 w-12 mx-auto mb-2 text-primary">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        <p class="text-lg font-medium text-primary">여기에 파일을 놓으세요</p>
      </div>
    </div>

    <!-- Mobile sidebar overlay -->
    <div
      v-if="showMobileSidebar"
      class="md:hidden fixed inset-0 z-30 bg-black/40"
      @click="showMobileSidebar = false"
    />

    <!-- Sidebar: hidden on mobile, slide-in overlay -->
    <div
      class="shrink-0 h-full z-30 transition-transform duration-200
        fixed md:relative
        w-64 md:w-56
        bg-background md:bg-transparent
        shadow-xl md:shadow-none"
      :class="showMobileSidebar ? 'translate-x-0' : '-translate-x-full md:translate-x-0'"
    >
      <FilesFileSidebar @navigate="showMobileSidebar = false" />
    </div>

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0 min-h-0">
      <!-- Command bar -->
      <FilesFileCommandBar
        @upload="showUpload = true"
        @new-folder="handleNewFolder"
        @toggle-sidebar="showMobileSidebar = !showMobileSidebar"
      />

      <!-- Breadcrumb -->
      <FilesFileBreadcrumb />

      <!-- File content area -->
      <div class="flex flex-1 min-h-0">
        <!-- List or Grid view -->
        <FilesFileList
          v-if="viewMode === 'list'"
          @select="handleSelect"
          @contextmenu="handleContextMenu"
        />
        <FilesFileGridView
          v-else
          @select="handleSelect"
          @contextmenu="handleContextMenu"
        />

        <!-- Detail panel: side on desktop, modal on mobile -->
        <FilesFileDetailPanel
          :item="detailItem"
          @close="detailItem = null"
          @download="downloadFile"
          @share="(item: FileItem) => { shareFile = item }"
          @rename="handleRename"
          @delete="handleDelete"
        />
      </div>
    </div>

    <!-- Context menu -->
    <FilesFileContextMenu
      v-if="contextMenu"
      :item="contextMenu.item"
      :x="contextMenu.x"
      :y="contextMenu.y"
      @close="contextMenu = null"
      @download="downloadFile"
      @share="(item: FileItem) => { shareFile = item }"
      @rename="handleRename"
      @delete="handleDelete"
      @preview="(item: FileItem) => { previewFile = item }"
    />

    <!-- Upload modal -->
    <FilesFileUploadModal v-if="showUpload" @close="showUpload = false" />

    <!-- Preview modal -->
    <FilesFilePreviewModal
      v-if="previewFile"
      :item="previewFile"
      @close="previewFile = null"
    />

    <!-- Share modal -->
    <FilesFileShareModal
      v-if="shareFile"
      :item="shareFile"
      @close="shareFile = null"
    />

    <!-- New folder dialog -->
    <div v-if="showNewFolder" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="showNewFolder = false">
      <div class="bg-background rounded-lg shadow-xl w-full max-w-sm mx-4 p-6">
        <h3 class="text-lg font-semibold mb-4">새 폴더</h3>
        <input
          v-model="newFolderName"
          placeholder="폴더 이름"
          class="w-full px-3 py-2 text-sm bg-background border rounded-md focus:outline-none focus:ring-1 focus:ring-primary"
          @keydown.enter="confirmNewFolder"
        />
        <div class="flex justify-end gap-2 mt-4">
          <button @click="showNewFolder = false" class="px-4 py-2 text-sm rounded-md hover:bg-accent transition-colors">
            취소
          </button>
          <button
            @click="confirmNewFolder"
            :disabled="!newFolderName.trim()"
            class="px-4 py-2 text-sm rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            생성
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

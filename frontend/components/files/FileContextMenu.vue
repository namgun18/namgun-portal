<script setup lang="ts">
import type { FileItem } from '~/composables/useFiles'

const props = defineProps<{
  item: FileItem
  x: number
  y: number
}>()

const emit = defineEmits<{
  close: []
  download: [path: string]
  share: [item: FileItem]
  rename: [item: FileItem]
  move: [item: FileItem]
  delete: [item: FileItem]
  preview: [item: FileItem]
}>()

const { downloadFile } = useFiles()

const style = computed(() => ({
  left: `${props.x}px`,
  top: `${props.y}px`,
}))

function handleDownload() {
  downloadFile(props.item.path)
  emit('close')
}
</script>

<template>
  <div class="fixed inset-0 z-50" @click="emit('close')" @contextmenu.prevent="emit('close')">
    <div
      :style="style"
      class="fixed bg-popover border rounded-md shadow-lg py-1 w-48 z-50"
    >
      <button
        v-if="!item.is_dir"
        @click="emit('preview', item); emit('close')"
        class="w-full px-3 py-1.5 text-sm text-left hover:bg-accent transition-colors flex items-center gap-2"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" />
        </svg>
        미리보기
      </button>
      <button
        v-if="!item.is_dir"
        @click="handleDownload"
        class="w-full px-3 py-1.5 text-sm text-left hover:bg-accent transition-colors flex items-center gap-2"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" />
        </svg>
        다운로드
      </button>
      <button
        v-if="!item.is_dir"
        @click="emit('share', item); emit('close')"
        class="w-full px-3 py-1.5 text-sm text-left hover:bg-accent transition-colors flex items-center gap-2"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
          <circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" /><line x1="8.59" y1="13.51" x2="15.42" y2="17.49" /><line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
        </svg>
        공유 링크
      </button>
      <div class="border-t my-1" />
      <button
        @click="emit('rename', item); emit('close')"
        class="w-full px-3 py-1.5 text-sm text-left hover:bg-accent transition-colors flex items-center gap-2"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
        </svg>
        이름 변경
      </button>
      <button
        @click="emit('delete', item); emit('close')"
        class="w-full px-3 py-1.5 text-sm text-left hover:bg-destructive/10 text-destructive transition-colors flex items-center gap-2"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
          <polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
        </svg>
        삭제
      </button>
    </div>
  </div>
</template>

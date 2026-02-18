<script setup lang="ts">
import type { FileItem } from '~/composables/useFiles'

const props = defineProps<{
  item: FileItem | null
}>()

const emit = defineEmits<{
  close: []
  download: [path: string]
  share: [item: FileItem]
  rename: [item: FileItem]
  move: [item: FileItem]
  delete: [item: FileItem]
}>()

const { getPreviewUrl } = useFiles()

function formatSize(bytes: number): string {
  if (!bytes) return '—'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0) + ' ' + units[i]
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function isImage(item: FileItem) {
  return item.mime_type?.startsWith('image/')
}
</script>

<template>
  <!-- Desktop: side panel -->
  <div
    v-if="item"
    class="hidden md:flex w-72 shrink-0 border-l bg-background flex-col h-full overflow-hidden"
  >
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b">
      <h3 class="text-sm font-medium truncate">상세 정보</h3>
      <button @click="emit('close')" class="h-6 w-6 flex items-center justify-center rounded hover:bg-accent transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
          <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>

    <!-- Preview -->
    <div class="p-4 flex flex-col items-center gap-3 border-b">
      <div v-if="isImage(item)" class="w-full aspect-square rounded-lg overflow-hidden bg-muted/30">
        <img :src="getPreviewUrl(item.path)" :alt="item.name" class="w-full h-full object-contain" />
      </div>
      <div v-else-if="item.is_dir" class="py-4">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="h-16 w-16 text-blue-500">
          <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
        </svg>
      </div>
      <div v-else class="py-4">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="h-16 w-16 text-muted-foreground">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
        </svg>
      </div>
      <div class="text-center">
        <p class="text-sm font-medium break-all">{{ item.name }}</p>
        <p class="text-xs text-muted-foreground mt-0.5">{{ item.mime_type || (item.is_dir ? '폴더' : '파일') }}</p>
      </div>
    </div>

    <!-- Metadata -->
    <div class="p-4 space-y-3 text-sm flex-1 overflow-auto">
      <div v-if="!item.is_dir" class="flex justify-between">
        <span class="text-muted-foreground">크기</span>
        <span>{{ formatSize(item.size) }}</span>
      </div>
      <div class="flex justify-between">
        <span class="text-muted-foreground">수정일</span>
        <span class="text-xs">{{ formatDate(item.modified_at) }}</span>
      </div>
    </div>

    <!-- Actions -->
    <div class="p-3 border-t space-y-1">
      <button v-if="!item.is_dir" @click="emit('download', item.path)" class="w-full text-left px-3 py-1.5 text-sm rounded-md hover:bg-accent transition-colors flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>
        다운로드
      </button>
      <button v-if="!item.is_dir" @click="emit('share', item)" class="w-full text-left px-3 py-1.5 text-sm rounded-md hover:bg-accent transition-colors flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4"><circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" /><line x1="8.59" y1="13.51" x2="15.42" y2="17.49" /><line x1="15.41" y1="6.51" x2="8.59" y2="10.49" /></svg>
        공유 링크
      </button>
      <button @click="emit('rename', item)" class="w-full text-left px-3 py-1.5 text-sm rounded-md hover:bg-accent transition-colors flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" /></svg>
        이름 변경
      </button>
      <button @click="emit('delete', item)" class="w-full text-left px-3 py-1.5 text-sm rounded-md hover:bg-destructive/10 text-destructive transition-colors flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4"><polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" /></svg>
        삭제
      </button>
    </div>
  </div>

  <!-- Mobile: bottom sheet modal -->
  <div v-if="item" class="md:hidden fixed inset-0 z-50" @click.self="emit('close')">
    <div class="absolute inset-0 bg-black/40" @click="emit('close')" />
    <div class="absolute bottom-0 left-0 right-0 bg-background rounded-t-xl shadow-xl max-h-[70vh] flex flex-col animate-slide-up">
      <!-- Handle -->
      <div class="flex justify-center pt-2 pb-1">
        <div class="w-10 h-1 rounded-full bg-muted-foreground/30" />
      </div>

      <!-- Header -->
      <div class="flex items-center gap-3 px-4 py-3 border-b">
        <div v-if="isImage(item)" class="h-10 w-10 rounded overflow-hidden bg-muted/30 shrink-0">
          <img :src="getPreviewUrl(item.path)" :alt="item.name" class="w-full h-full object-cover" />
        </div>
        <div v-else-if="item.is_dir" class="shrink-0">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-8 w-8 text-blue-500">
            <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
          </svg>
        </div>
        <div v-else class="shrink-0">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-8 w-8 text-muted-foreground">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
          </svg>
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium truncate">{{ item.name }}</p>
          <p class="text-xs text-muted-foreground">
            {{ item.is_dir ? '폴더' : formatSize(item.size) }}
            <span v-if="item.modified_at"> &middot; {{ formatDate(item.modified_at) }}</span>
          </p>
        </div>
        <button @click="emit('close')" class="h-8 w-8 flex items-center justify-center rounded-md hover:bg-accent shrink-0">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <!-- Actions -->
      <div class="p-2 space-y-0.5 overflow-auto">
        <button v-if="!item.is_dir" @click="emit('download', item.path); emit('close')" class="w-full text-left px-4 py-3 text-sm rounded-md hover:bg-accent transition-colors flex items-center gap-3">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-5 w-5 text-muted-foreground"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>
          다운로드
        </button>
        <button v-if="!item.is_dir" @click="emit('share', item); emit('close')" class="w-full text-left px-4 py-3 text-sm rounded-md hover:bg-accent transition-colors flex items-center gap-3">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-5 w-5 text-muted-foreground"><circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" /><line x1="8.59" y1="13.51" x2="15.42" y2="17.49" /><line x1="15.41" y1="6.51" x2="8.59" y2="10.49" /></svg>
          공유 링크
        </button>
        <button @click="emit('rename', item); emit('close')" class="w-full text-left px-4 py-3 text-sm rounded-md hover:bg-accent transition-colors flex items-center gap-3">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-5 w-5 text-muted-foreground"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" /></svg>
          이름 변경
        </button>
        <button @click="emit('delete', item); emit('close')" class="w-full text-left px-4 py-3 text-sm rounded-md hover:bg-destructive/10 text-destructive transition-colors flex items-center gap-3">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-5 w-5"><polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" /></svg>
          삭제
        </button>
      </div>
    </div>
  </div>
</template>

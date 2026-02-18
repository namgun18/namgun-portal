<script setup lang="ts">
const emit = defineEmits<{
  select: [item: any]
  contextmenu: [event: MouseEvent, item: any]
}>()

const { sortedItems, sortField, sortDir, toggleSort, selectedItems, selectAll, toggleSelect, navigateTo, loading } = useFiles()

function getFileIcon(item: any): string {
  if (item.is_dir) return 'folder'
  const mime = item.mime_type || ''
  if (mime.startsWith('image/')) return 'image'
  if (mime === 'application/pdf') return 'pdf'
  if (mime.startsWith('video/')) return 'video'
  if (mime.startsWith('audio/')) return 'audio'
  if (mime.includes('spreadsheet') || mime.includes('excel') || item.name.match(/\.(xlsx?|csv)$/i)) return 'spreadsheet'
  if (mime.includes('presentation') || item.name.match(/\.(pptx?)$/i)) return 'presentation'
  if (mime.includes('document') || mime.includes('word') || item.name.match(/\.(docx?)$/i)) return 'document'
  if (item.name.match(/\.(zip|rar|7z|tar|gz)$/i)) return 'archive'
  if (item.name.match(/\.(py|js|ts|vue|html|css|json|xml|yaml|yml|sh|go|rs|java|sql)$/i)) return 'code'
  return 'file'
}

function formatSize(bytes: number): string {
  if (!bytes) return '—'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0) + ' ' + units[i]
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  const m = d.getMonth() + 1
  const day = d.getDate()
  const h = d.getHours().toString().padStart(2, '0')
  const min = d.getMinutes().toString().padStart(2, '0')
  return `${m}/${day} ${h}:${min}`
}

function handleClick(item: any) {
  if (item.is_dir) {
    navigateTo(item.path)
  } else {
    emit('select', item)
  }
}

function handleContextMenu(e: MouseEvent, item: any) {
  e.preventDefault()
  emit('contextmenu', e, item)
}

const isAllSelected = computed(() =>
  sortedItems.value.length > 0 && selectedItems.value.size === sortedItems.value.length
)
</script>

<template>
  <div class="flex-1 overflow-auto">
    <!-- Loading skeleton -->
    <div v-if="loading" class="p-4 space-y-2">
      <div v-for="i in 5" :key="i" class="h-10 bg-muted/50 rounded animate-pulse" />
    </div>

    <!-- Empty state -->
    <div v-else-if="sortedItems.length === 0" class="flex flex-col items-center justify-center h-64 text-muted-foreground">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="h-12 w-12 mb-3 opacity-50">
        <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
      </svg>
      <p class="text-sm">이 폴더는 비어 있습니다</p>
    </div>

    <!-- Table -->
    <table v-else class="w-full text-sm">
      <thead class="sticky top-0 bg-background border-b">
        <tr class="text-left text-muted-foreground">
          <th class="w-10 px-3 py-2">
            <input
              type="checkbox"
              :checked="isAllSelected"
              @change="selectAll()"
              class="rounded border-muted-foreground/30"
            />
          </th>
          <th class="px-2 py-2 cursor-pointer select-none" @click="toggleSort('name')">
            <span class="flex items-center gap-1">
              이름
              <svg v-if="sortField === 'name'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-3 w-3" :class="sortDir === 'desc' ? 'rotate-180' : ''">
                <polyline points="18 15 12 9 6 15" />
              </svg>
            </span>
          </th>
          <th class="px-2 py-2 w-32 cursor-pointer select-none hidden sm:table-cell" @click="toggleSort('modified_at')">
            <span class="flex items-center gap-1">
              수정일
              <svg v-if="sortField === 'modified_at'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-3 w-3" :class="sortDir === 'desc' ? 'rotate-180' : ''">
                <polyline points="18 15 12 9 6 15" />
              </svg>
            </span>
          </th>
          <th class="px-2 py-2 w-24 cursor-pointer select-none hidden sm:table-cell" @click="toggleSort('size')">
            <span class="flex items-center gap-1">
              크기
              <svg v-if="sortField === 'size'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-3 w-3" :class="sortDir === 'desc' ? 'rotate-180' : ''">
                <polyline points="18 15 12 9 6 15" />
              </svg>
            </span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="item in sortedItems"
          :key="item.path"
          @click="handleClick(item)"
          @contextmenu="handleContextMenu($event, item)"
          class="border-b hover:bg-accent/50 cursor-pointer transition-colors"
          :class="selectedItems.has(item.path) ? 'bg-accent/30' : ''"
        >
          <td class="px-3 py-2" @click.stop>
            <input
              type="checkbox"
              :checked="selectedItems.has(item.path)"
              @change="toggleSelect(item.path)"
              class="rounded border-muted-foreground/30"
            />
          </td>
          <td class="px-2 py-2">
            <div class="flex items-center gap-2">
              <!-- File type icons -->
              <svg v-if="getFileIcon(item) === 'folder'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5 text-blue-500 shrink-0">
                <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
              </svg>
              <svg v-else-if="getFileIcon(item) === 'image'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5 text-green-500 shrink-0">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21 15 16 10 5 21" />
              </svg>
              <svg v-else-if="getFileIcon(item) === 'pdf'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5 text-red-500 shrink-0">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="9" y1="15" x2="15" y2="15" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5 text-muted-foreground shrink-0">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
              </svg>
              <span class="truncate">{{ item.name }}</span>
            </div>
          </td>
          <td class="px-2 py-2 text-muted-foreground hidden sm:table-cell">{{ formatDate(item.modified_at) }}</td>
          <td class="px-2 py-2 text-muted-foreground hidden sm:table-cell">{{ item.is_dir ? '—' : formatSize(item.size) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

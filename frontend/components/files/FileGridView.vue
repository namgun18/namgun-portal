<script setup lang="ts">
const emit = defineEmits<{
  select: [item: any]
  contextmenu: [event: MouseEvent, item: any]
}>()

const { sortedItems, selectedItems, toggleSelect, navigateTo, getPreviewUrl, loading } = useFiles()

function isImage(item: any) {
  return item.mime_type?.startsWith('image/') && !item.is_dir
}

function handleClick(item: any) {
  if (item.is_dir) {
    navigateTo(item.path)
  } else {
    emit('select', item)
  }
}

function formatSize(bytes: number): string {
  if (!bytes) return ''
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0) + ' ' + units[i]
}
</script>

<template>
  <div class="flex-1 overflow-auto p-2 sm:p-4">
    <!-- Loading -->
    <div v-if="loading" class="grid grid-cols-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2 sm:gap-3">
      <div v-for="i in 8" :key="i" class="aspect-square bg-muted/50 rounded-lg animate-pulse" />
    </div>

    <!-- Empty -->
    <div v-else-if="sortedItems.length === 0" class="flex flex-col items-center justify-center h-64 text-muted-foreground">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="h-12 w-12 mb-3 opacity-50">
        <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
      </svg>
      <p class="text-sm">이 폴더는 비어 있습니다</p>
    </div>

    <!-- Grid -->
    <div v-else class="grid grid-cols-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2 sm:gap-3">
      <div
        v-for="item in sortedItems"
        :key="item.path"
        @click="handleClick(item)"
        @contextmenu.prevent="emit('contextmenu', $event, item)"
        class="group relative rounded-lg border p-1.5 sm:p-2 cursor-pointer transition-all hover:shadow-md"
        :class="selectedItems.has(item.path) ? 'ring-2 ring-primary bg-accent/30' : 'hover:bg-accent/30'"
      >
        <!-- Checkbox -->
        <input
          type="checkbox"
          :checked="selectedItems.has(item.path)"
          @click.stop
          @change="toggleSelect(item.path)"
          class="absolute top-2 left-2 z-10 rounded border-muted-foreground/30 opacity-0 group-hover:opacity-100 transition-opacity"
          :class="selectedItems.has(item.path) ? 'opacity-100' : ''"
        />
        <!-- More actions button -->
        <button
          @click.stop="emit('contextmenu', $event, item)"
          class="absolute top-1.5 right-1.5 z-10 h-6 w-6 flex items-center justify-center rounded-md bg-background/80 hover:bg-accent opacity-0 group-hover:opacity-100 transition-opacity"
          title="더보기"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-3.5 w-3.5 text-muted-foreground">
            <circle cx="12" cy="5" r="1.5" /><circle cx="12" cy="12" r="1.5" /><circle cx="12" cy="19" r="1.5" />
          </svg>
        </button>

        <!-- Preview area -->
        <div class="aspect-square flex items-center justify-center rounded bg-muted/30 mb-2 overflow-hidden">
          <img
            v-if="isImage(item)"
            :src="getPreviewUrl(item.path)"
            :alt="item.name"
            class="w-full h-full object-cover"
            loading="lazy"
          />
          <svg v-else-if="item.is_dir" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="h-12 w-12 text-blue-500">
            <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="h-12 w-12 text-muted-foreground">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
          </svg>
        </div>

        <!-- Name + size -->
        <div class="text-xs truncate font-medium">{{ item.name }}</div>
        <div v-if="!item.is_dir" class="text-xs text-muted-foreground">{{ formatSize(item.size) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { currentPath, navigateTo, storageInfo, fetchStorageInfo } = useFiles()
const { user } = useAuth()

onMounted(() => {
  fetchStorageInfo()
})

const navItems = computed(() => {
  const items = [
    { label: '내 파일', path: 'my', icon: 'folder-user' },
    { label: '공유 파일', path: 'shared', icon: 'folder-shared' },
  ]
  if (user.value?.is_admin) {
    items.push({ label: '전체 사용자', path: 'users', icon: 'users' })
  }
  return items
})

function isActive(path: string) {
  return currentPath.value === path || currentPath.value.startsWith(path + '/')
}

function formatSize(bytes: number) {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + units[i]
}

const totalUsed = computed(() => {
  if (!storageInfo.value) return 0
  return storageInfo.value.personal_used + storageInfo.value.shared_used
})
</script>

<template>
  <aside class="w-56 shrink-0 border-r bg-muted/30 flex flex-col h-full">
    <nav class="flex-1 p-3 space-y-1">
      <button
        v-for="item in navItems"
        :key="item.path"
        @click="navigateTo(item.path)"
        class="w-full flex items-center gap-3 px-3 py-2 text-sm rounded-md transition-colors"
        :class="isActive(item.path) ? 'bg-accent text-accent-foreground font-medium' : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground'"
      >
        <!-- Folder user icon -->
        <svg v-if="item.icon === 'folder-user'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
          <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
          <circle cx="12" cy="13" r="2" />
          <path d="M12 15c-1.66 0-3 .9-3 2h6c0-1.1-1.34-2-3-2Z" />
        </svg>
        <!-- Folder shared icon -->
        <svg v-else-if="item.icon === 'folder-shared'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
          <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
          <path d="M14 13a2 2 0 1 0-4 0" />
          <circle cx="12" cy="11" r="1" />
        </svg>
        <!-- Users icon -->
        <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
        {{ item.label }}
      </button>
    </nav>

    <!-- Storage usage -->
    <div v-if="storageInfo" class="p-3 border-t">
      <div class="text-xs text-muted-foreground mb-2">사용량</div>
      <div class="space-y-1.5">
        <div class="flex justify-between text-xs">
          <span>내 파일</span>
          <span>{{ formatSize(storageInfo.personal_used) }}</span>
        </div>
        <div class="flex justify-between text-xs">
          <span>공유</span>
          <span>{{ formatSize(storageInfo.shared_used) }}</span>
        </div>
        <div class="text-xs font-medium mt-1">
          총 {{ formatSize(totalUsed) }}
        </div>
      </div>
    </div>
  </aside>
</template>

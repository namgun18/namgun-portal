export interface FileItem {
  name: string
  path: string
  is_dir: boolean
  size: number
  modified_at: string | null
  mime_type: string | null
}

export interface FileListResponse {
  path: string
  items: FileItem[]
}

export interface StorageInfo {
  personal_used: number
  shared_used: number
  total_available: number
}

export interface ShareLinkItem {
  id: string
  token: string
  display_name: string
  file_path: string
  expires_at: string | null
  max_downloads: number | null
  download_count: number
  created_at: string
}

export interface ShareLinkResponse {
  token: string
  url: string
  display_name: string
  expires_at: string | null
  max_downloads: number | null
  created_at: string
}

export type ViewMode = 'list' | 'grid'
export type SortField = 'name' | 'modified_at' | 'size'
export type SortDir = 'asc' | 'desc'

const currentPath = ref('my')
const items = ref<FileItem[]>([])
const loading = ref(false)
const viewMode = ref<ViewMode>('list')
const sortField = ref<SortField>('name')
const sortDir = ref<SortDir>('asc')
const selectedItems = ref<Set<string>>(new Set())
const storageInfo = ref<StorageInfo | null>(null)
const shareLinks = ref<ShareLinkItem[]>([])

export function useFiles() {
  async function fetchFiles(path?: string) {
    const p = path ?? currentPath.value
    loading.value = true
    try {
      const data = await $fetch<FileListResponse>('/api/files/list', {
        params: { path: p },
      })
      currentPath.value = data.path
      items.value = data.items
      selectedItems.value.clear()
    } catch (e: any) {
      console.error('fetchFiles error:', e)
      items.value = []
    } finally {
      loading.value = false
    }
  }

  async function fetchStorageInfo() {
    try {
      storageInfo.value = await $fetch<StorageInfo>('/api/files/info')
    } catch { /* ignore */ }
  }

  async function uploadFiles(files: File[], targetPath?: string) {
    const path = targetPath ?? currentPath.value
    const results: { name: string; ok: boolean; error?: string }[] = []

    for (const file of files) {
      const form = new FormData()
      form.append('file', file)
      try {
        await $fetch('/api/files/upload', {
          method: 'POST',
          params: { path },
          body: form,
        })
        results.push({ name: file.name, ok: true })
      } catch (e: any) {
        results.push({ name: file.name, ok: false, error: e?.data?.detail || 'Upload failed' })
      }
    }

    await fetchFiles()
    await fetchStorageInfo()
    return results
  }

  async function createFolder(name: string) {
    const fullPath = currentPath.value ? `${currentPath.value}/${name}` : name
    await $fetch('/api/files/mkdir', {
      method: 'POST',
      body: { path: fullPath },
    })
    await fetchFiles()
  }

  async function deleteItems(paths: string[]) {
    for (const p of paths) {
      await $fetch('/api/files/delete', {
        method: 'DELETE',
        params: { path: p },
      })
    }
    await fetchFiles()
    await fetchStorageInfo()
  }

  async function renameItem(path: string, newName: string) {
    await $fetch('/api/files/rename', {
      method: 'PATCH',
      body: { path, new_name: newName },
    })
    await fetchFiles()
  }

  async function moveItem(src: string, dst: string, copy = false) {
    await $fetch('/api/files/move', {
      method: 'PATCH',
      body: { src, dst, copy },
    })
    await fetchFiles()
  }

  async function downloadFile(path: string) {
    const url = `/api/files/download?path=${encodeURIComponent(path)}`
    window.open(url, '_blank')
  }

  function getPreviewUrl(path: string) {
    return `/api/files/preview?path=${encodeURIComponent(path)}`
  }

  // Share links
  async function createShareLink(path: string, expiresIn?: string, oneTime = false) {
    const data = await $fetch<ShareLinkResponse>('/api/files/share', {
      method: 'POST',
      body: { path, expires_in: expiresIn || null, one_time: oneTime },
    })
    return data
  }

  async function fetchShareLinks() {
    try {
      shareLinks.value = await $fetch<ShareLinkItem[]>('/api/files/share/list')
    } catch { /* ignore */ }
  }

  async function deleteShareLink(id: string) {
    await $fetch(`/api/files/share/${id}`, { method: 'DELETE' })
    await fetchShareLinks()
  }

  // Sort helpers
  const sortedItems = computed(() => {
    const arr = [...items.value]
    arr.sort((a, b) => {
      // Directories first
      if (a.is_dir !== b.is_dir) return a.is_dir ? -1 : 1

      let cmp = 0
      if (sortField.value === 'name') {
        cmp = a.name.localeCompare(b.name, 'ko')
      } else if (sortField.value === 'size') {
        cmp = a.size - b.size
      } else if (sortField.value === 'modified_at') {
        const ta = a.modified_at ? new Date(a.modified_at).getTime() : 0
        const tb = b.modified_at ? new Date(b.modified_at).getTime() : 0
        cmp = ta - tb
      }

      return sortDir.value === 'asc' ? cmp : -cmp
    })
    return arr
  })

  function toggleSort(field: SortField) {
    if (sortField.value === field) {
      sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortField.value = field
      sortDir.value = 'asc'
    }
  }

  // Navigation
  const breadcrumbs = computed(() => {
    const parts = currentPath.value.split('/').filter(Boolean)
    const crumbs: { label: string; path: string }[] = []
    const labelMap: Record<string, string> = { my: '내 파일', shared: '공유 파일', users: '전체 사용자' }

    let accumulated = ''
    for (const part of parts) {
      accumulated = accumulated ? `${accumulated}/${part}` : part
      crumbs.push({
        label: labelMap[accumulated] || part,
        path: accumulated,
      })
    }
    return crumbs
  })

  function navigateTo(path: string) {
    fetchFiles(path)
  }

  // Selection
  function toggleSelect(path: string) {
    if (selectedItems.value.has(path)) {
      selectedItems.value.delete(path)
    } else {
      selectedItems.value.add(path)
    }
    // Force reactivity
    selectedItems.value = new Set(selectedItems.value)
  }

  function selectAll() {
    if (selectedItems.value.size === items.value.length) {
      selectedItems.value.clear()
    } else {
      selectedItems.value = new Set(items.value.map(i => i.path))
    }
    selectedItems.value = new Set(selectedItems.value)
  }

  return {
    currentPath: readonly(currentPath),
    items: readonly(items),
    loading: readonly(loading),
    viewMode,
    sortField: readonly(sortField),
    sortDir: readonly(sortDir),
    selectedItems,
    storageInfo: readonly(storageInfo),
    shareLinks: readonly(shareLinks),
    sortedItems,
    breadcrumbs,
    fetchFiles,
    fetchStorageInfo,
    uploadFiles,
    createFolder,
    deleteItems,
    renameItem,
    moveItem,
    downloadFile,
    getPreviewUrl,
    createShareLink,
    fetchShareLinks,
    deleteShareLink,
    toggleSort,
    navigateTo,
    toggleSelect,
    selectAll,
  }
}

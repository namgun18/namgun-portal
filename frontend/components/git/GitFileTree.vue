<script setup lang="ts">
const props = withDefaults(defineProps<{ hasCommitHeader?: boolean }>(), {
  hasCommitHeader: false,
})

const { contents, navigateToDir, openFile } = useGit()

function handleClick(entry: { type: string; path: string }) {
  if (entry.type === 'dir') {
    navigateToDir(entry.path)
  } else {
    openFile(entry.path)
  }
}

function formatSize(bytes: number): string {
  if (bytes === 0) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>

<template>
  <div
    class="border overflow-hidden"
    :class="hasCommitHeader ? 'rounded-b-md border-t-0' : 'rounded-md'"
  >
    <table class="w-full">
      <tbody>
        <tr
          v-for="entry in contents"
          :key="entry.path"
          @click="handleClick(entry)"
          class="border-b last:border-b-0 hover:bg-accent/20 cursor-pointer transition-colors"
        >
          <!-- Icon -->
          <td class="w-8 pl-4 pr-1 py-2">
            <svg v-if="entry.type === 'dir'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-4 w-4 text-sky-500">
              <path fill="currentColor" d="M1.75 1A1.75 1.75 0 0 0 0 2.75v10.5C0 14.216.784 15 1.75 15h12.5A1.75 1.75 0 0 0 16 13.25v-8.5A1.75 1.75 0 0 0 14.25 3H7.5a.25.25 0 0 1-.2-.1l-.9-1.2C6.07 1.26 5.55 1 5 1Z" />
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-4 w-4 text-muted-foreground">
              <path fill="currentColor" d="M2 1.75C2 .784 2.784 0 3.75 0h6.586c.464 0 .909.184 1.237.513l2.914 2.914c.329.328.513.773.513 1.237v9.586A1.75 1.75 0 0 1 13.25 16h-9.5A1.75 1.75 0 0 1 2 14.25Zm1.75-.25a.25.25 0 0 0-.25.25v12.5c0 .138.112.25.25.25h9.5a.25.25 0 0 0 .25-.25V6h-2.75A1.75 1.75 0 0 1 9 4.25V1.5Zm6.75.062V4.25c0 .138.112.25.25.25h2.688l-.011-.013-2.914-2.914-.013-.011Z" />
            </svg>
          </td>

          <!-- Name -->
          <td class="py-2 pr-2">
            <span class="text-sm hover:text-primary hover:underline" :class="entry.type === 'dir' ? 'font-medium' : ''">
              {{ entry.name }}
            </span>
          </td>

          <!-- Size (files only) -->
          <td class="text-right pr-4 py-2">
            <span v-if="entry.type !== 'dir' && entry.size" class="text-xs text-muted-foreground">
              {{ formatSize(entry.size) }}
            </span>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="contents.length === 0" class="px-4 py-8 text-center text-sm text-muted-foreground">
      빈 디렉토리
    </div>
  </div>
</template>

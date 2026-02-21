<script setup lang="ts">
const { currentPath, navigateToDir } = useGit()

const segments = computed(() => {
  if (!currentPath.value) return []
  const parts = currentPath.value.split('/')
  return parts.map((name, i) => ({
    name,
    path: parts.slice(0, i + 1).join('/'),
  }))
})
</script>

<template>
  <div v-if="currentPath" class="flex items-center gap-1 text-sm px-4 py-2 border-b overflow-x-auto">
    <button
      @click="navigateToDir('')"
      class="text-primary hover:underline shrink-0"
    >
      root
    </button>
    <template v-for="seg in segments" :key="seg.path">
      <span class="text-muted-foreground shrink-0">/</span>
      <button
        @click="navigateToDir(seg.path)"
        class="text-primary hover:underline shrink-0"
      >
        {{ seg.name }}
      </button>
    </template>
  </div>
</template>

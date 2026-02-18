<script setup lang="ts">
const { breadcrumbs, navigateTo } = useFiles()
</script>

<template>
  <div class="flex items-center gap-1 px-2 sm:px-4 py-1.5 sm:py-2 text-sm border-b bg-muted/20 overflow-x-auto scrollbar-none">
    <button
      @click="navigateTo('')"
      class="text-muted-foreground hover:text-foreground transition-colors shrink-0"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
        <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" />
      </svg>
    </button>

    <template v-for="(crumb, i) in breadcrumbs" :key="crumb.path">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3 w-3 text-muted-foreground shrink-0">
        <polyline points="9 18 15 12 9 6" />
      </svg>
      <button
        v-if="i < breadcrumbs.length - 1"
        @click="navigateTo(crumb.path)"
        class="text-muted-foreground hover:text-foreground transition-colors truncate max-w-[150px]"
      >
        {{ crumb.label }}
      </button>
      <span v-else class="font-medium truncate max-w-[200px]">{{ crumb.label }}</span>
    </template>
  </div>
</template>

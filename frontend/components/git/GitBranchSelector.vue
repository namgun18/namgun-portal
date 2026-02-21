<script setup lang="ts">
const { branches, currentBranch, switchBranch } = useGit()
const open = ref(false)

function select(name: string) {
  open.value = false
  switchBranch(name)
}
</script>

<template>
  <div class="relative">
    <button
      @click="open = !open"
      class="inline-flex items-center gap-1.5 px-2 py-1.5 text-xs font-medium rounded-md border hover:bg-accent transition-colors max-w-[160px]"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5 shrink-0">
        <line x1="6" y1="3" x2="6" y2="15" /><circle cx="18" cy="6" r="3" /><circle cx="6" cy="18" r="3" /><path d="M18 9a9 9 0 0 1-9 9" />
      </svg>
      <span class="truncate">{{ currentBranch || 'branch' }}</span>
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3 w-3 shrink-0">
        <polyline points="6 9 12 15 18 9" />
      </svg>
    </button>

    <!-- Dropdown -->
    <div
      v-if="open"
      class="absolute left-0 top-full mt-1 z-50 w-56 max-h-64 overflow-y-auto rounded-md border bg-popover shadow-md"
    >
      <button
        v-for="b in branches"
        :key="b.name"
        @click="select(b.name)"
        class="w-full px-3 py-2 text-sm text-left hover:bg-accent transition-colors flex items-center gap-2"
        :class="b.name === currentBranch ? 'bg-accent/50 font-medium' : ''"
      >
        <svg v-if="b.name === currentBranch" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5 shrink-0">
          <polyline points="20 6 9 17 4 12" />
        </svg>
        <span v-else class="w-3.5" />
        <span class="truncate">{{ b.name }}</span>
      </button>
    </div>

    <!-- Backdrop -->
    <div v-if="open" class="fixed inset-0 z-40" @click="open = false" />
  </div>
</template>

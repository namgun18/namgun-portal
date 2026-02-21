<script setup lang="ts">
const { openCompose } = useMail()

const shortcuts = [
  { label: '메일 쓰기', icon: 'mail', action: () => openCompose('new') },
  { label: '회의 시작', icon: 'video', to: '/meetings' },
  { label: '파일 업로드', icon: 'upload', to: '/files' },
  { label: 'Git 저장소', icon: 'git', to: '/git' },
]
</script>

<template>
  <UiCard>
    <UiCardHeader class="pb-3">
      <UiCardTitle class="text-base">빠른 바로가기</UiCardTitle>
    </UiCardHeader>
    <UiCardContent>
      <div class="grid grid-cols-2 gap-2">
        <template v-for="s in shortcuts" :key="s.label">
          <button
            v-if="s.action"
            class="flex flex-col items-center gap-1.5 rounded-lg border p-3 text-sm hover:bg-accent/50 transition-colors"
            @click="s.action"
          >
            <!-- Mail icon -->
            <div v-if="s.icon === 'mail'" class="rounded-full p-2 bg-blue-100 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
            </div>
            <span>{{ s.label }}</span>
          </button>
          <NuxtLink
            v-else
            :to="s.to!"
            class="flex flex-col items-center gap-1.5 rounded-lg border p-3 text-sm hover:bg-accent/50 transition-colors"
          >
            <!-- Video icon -->
            <div v-if="s.icon === 'video'" class="rounded-full p-2 bg-green-100 text-green-600 dark:bg-green-500/20 dark:text-green-400">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5"><path d="m16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.87a.5.5 0 0 0-.752-.432L16 10.5"/><rect width="14" height="12" x="2" y="6" rx="2"/></svg>
            </div>
            <!-- Upload icon -->
            <div v-if="s.icon === 'upload'" class="rounded-full p-2 bg-amber-100 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>
            </div>
            <!-- Git icon -->
            <div v-if="s.icon === 'git'" class="rounded-full p-2 bg-purple-100 text-purple-600 dark:bg-purple-500/20 dark:text-purple-400">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5"><circle cx="12" cy="12" r="3"/><line x1="3" x2="9" y1="12" y2="12"/><line x1="15" x2="21" y1="12" y2="12"/></svg>
            </div>
            <span>{{ s.label }}</span>
          </NuxtLink>
        </template>
      </div>
    </UiCardContent>
  </UiCard>
</template>

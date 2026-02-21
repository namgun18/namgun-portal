<script setup lang="ts">
import { formatSize } from '~/lib/date'

const { storageInfo, fetchStorageInfo } = useFiles()

onMounted(fetchStorageInfo)

const usedPercent = computed(() => {
  if (!storageInfo.value || !storageInfo.value.total_capacity) return 0
  return Math.round(storageInfo.value.disk_used / storageInfo.value.total_capacity * 100)
})
</script>

<template>
  <UiCard>
    <UiCardHeader class="pb-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 text-teal-500"><line x1="22" x2="2" y1="12" y2="12"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/><line x1="6" x2="6.01" y1="16" y2="16"/><line x1="10" x2="10.01" y1="16" y2="16"/></svg>
          <UiCardTitle class="text-base">스토리지</UiCardTitle>
        </div>
        <NuxtLink to="/files" class="text-xs text-primary hover:underline">파일 관리</NuxtLink>
      </div>
    </UiCardHeader>
    <UiCardContent>
      <div v-if="!storageInfo" class="space-y-3">
        <UiSkeleton class="h-4 w-full" />
        <UiSkeleton class="h-2 w-full rounded-full" />
      </div>

      <div v-else class="space-y-3">
        <!-- Total usage bar -->
        <div>
          <div class="flex justify-between text-sm mb-1.5">
            <span class="font-medium">{{ usedPercent }}% 사용중</span>
            <span class="text-muted-foreground">
              {{ formatSize(storageInfo.disk_used) }} / {{ formatSize(storageInfo.total_capacity) }}
            </span>
          </div>
          <div class="h-2.5 w-full rounded-full bg-muted overflow-hidden">
            <div
              class="h-full rounded-full transition-all"
              :class="usedPercent > 90 ? 'bg-red-500' : usedPercent > 70 ? 'bg-yellow-500' : 'bg-primary'"
              :style="{ width: `${usedPercent}%` }"
            />
          </div>
        </div>

        <!-- Breakdown -->
        <div class="space-y-1 pt-1">
          <div class="flex justify-between text-xs text-muted-foreground">
            <span>내 파일</span>
            <span>{{ formatSize(storageInfo.personal_used) }}</span>
          </div>
          <div class="flex justify-between text-xs text-muted-foreground">
            <span>공유 파일</span>
            <span>{{ formatSize(storageInfo.shared_used) }}</span>
          </div>
        </div>
      </div>
    </UiCardContent>
  </UiCard>
</template>

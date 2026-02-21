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
        <UiCardTitle class="text-base">스토리지</UiCardTitle>
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

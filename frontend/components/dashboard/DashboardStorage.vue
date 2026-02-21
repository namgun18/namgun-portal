<script setup lang="ts">
import { formatSize } from '~/lib/date'

const { storageInfo, fetchStorageInfo } = useFiles()

onMounted(fetchStorageInfo)

const totalUsed = computed(() =>
  (storageInfo.value?.personal_used ?? 0) + (storageInfo.value?.shared_used ?? 0)
)
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
        <div class="flex justify-between text-sm">
          <span>전체 사용량</span>
          <span class="font-medium">{{ formatSize(totalUsed) }}</span>
        </div>
        <div class="space-y-2">
          <div class="flex justify-between text-xs text-muted-foreground">
            <span>내 파일</span>
            <span>{{ formatSize(storageInfo.personal_used) }}</span>
          </div>
          <div class="h-2 w-full rounded-full bg-muted overflow-hidden">
            <div
              class="h-full rounded-full bg-primary transition-all"
              :style="{ width: totalUsed > 0 ? `${Math.round(storageInfo.personal_used / totalUsed * 100)}%` : '0%' }"
            />
          </div>
          <div class="flex justify-between text-xs text-muted-foreground">
            <span>공유 파일</span>
            <span>{{ formatSize(storageInfo.shared_used) }}</span>
          </div>
          <div class="h-2 w-full rounded-full bg-muted overflow-hidden">
            <div
              class="h-full rounded-full bg-blue-500 transition-all"
              :style="{ width: totalUsed > 0 ? `${Math.round(storageInfo.shared_used / totalUsed * 100)}%` : '0%' }"
            />
          </div>
        </div>
      </div>
    </UiCardContent>
  </UiCard>
</template>

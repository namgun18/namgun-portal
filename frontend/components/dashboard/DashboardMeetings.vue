<script setup lang="ts">
const { meetings, loadingMeetings, fetchMeetings } = useMeetings()

onMounted(fetchMeetings)

const activeMeetings = computed(() => meetings.value.filter(m => m.running))
</script>

<template>
  <UiCard>
    <UiCardHeader class="pb-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 text-green-500"><path d="m16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.87a.5.5 0 0 0-.752-.432L16 10.5"/><rect width="14" height="12" x="2" y="6" rx="2"/></svg>
          <UiCardTitle class="text-base">진행 중인 회의</UiCardTitle>
        </div>
        <NuxtLink to="/meetings" class="text-xs text-primary hover:underline">전체 보기</NuxtLink>
      </div>
    </UiCardHeader>
    <UiCardContent>
      <!-- Loading -->
      <div v-if="loadingMeetings" class="space-y-3">
        <UiSkeleton class="h-4 w-full" />
        <UiSkeleton class="h-4 w-3/4" />
      </div>

      <!-- Empty -->
      <p v-else-if="activeMeetings.length === 0" class="text-sm text-muted-foreground">
        진행 중인 회의가 없습니다
      </p>

      <!-- Meeting list -->
      <div v-else class="space-y-2">
        <div
          v-for="m in activeMeetings"
          :key="m.meetingID"
          class="flex items-center justify-between rounded-md border px-3 py-2"
        >
          <div class="min-w-0">
            <p class="text-sm font-medium truncate">{{ m.meetingName }}</p>
            <p class="text-xs text-muted-foreground">
              참여자 {{ m.participantCount }}명
            </p>
          </div>
          <UiBadge variant="success" class="shrink-0">진행중</UiBadge>
        </div>
      </div>
    </UiCardContent>
  </UiCard>
</template>

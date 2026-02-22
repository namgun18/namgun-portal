<script setup lang="ts">
definePageMeta({ layout: 'auth' })

const route = useRoute()
const meetingId = route.params.id as string

const guestName = ref('')
const loading = ref(false)
const error = ref('')
const meetingName = ref('')
const loadingInfo = ref(true)

// Try to fetch meeting info
onMounted(async () => {
  try {
    const data = await $fetch<{ meetingName: string }>(`/api/meetings/${meetingId}`)
    meetingName.value = data.meetingName
  } catch {
    meetingName.value = ''
  } finally {
    loadingInfo.value = false
  }
})

async function handleJoin() {
  if (!guestName.value.trim()) {
    error.value = '이름을 입력해주세요.'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const resp = await $fetch<{ joinUrl: string }>(`/api/meetings/${meetingId}/guest-join`, {
      method: 'POST',
      body: { name: guestName.value.trim() },
    })
    window.location.href = resp.joinUrl
  } catch (e: any) {
    const detail = e?.data?.detail || ''
    if (detail) {
      error.value = detail
    } else {
      error.value = '회의에 참가할 수 없습니다. 링크를 확인해주세요.'
    }
    loading.value = false
  }
}
</script>

<template>
  <div class="w-full max-w-sm space-y-6">
    <div class="text-center space-y-2">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-12 w-12 mx-auto text-primary">
        <path d="M23 7l-7 5 7 5V7z" /><rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
      </svg>
      <h1 class="text-2xl font-bold">회의 참가</h1>
      <p v-if="loadingInfo" class="text-sm text-muted-foreground">불러오는 중...</p>
      <p v-else-if="meetingName" class="text-sm text-muted-foreground">
        <span class="font-medium text-foreground">{{ meetingName }}</span>에 참가합니다
      </p>
      <p v-else class="text-sm text-muted-foreground">
        이름을 입력하고 참가하세요
      </p>
    </div>

    <form @submit.prevent="handleJoin" class="space-y-4">
      <div>
        <label for="guestName" class="block text-sm font-medium mb-1.5">표시 이름</label>
        <input
          id="guestName"
          v-model="guestName"
          type="text"
          placeholder="회의에서 표시될 이름"
          class="w-full px-3 py-2.5 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
          autofocus
        />
      </div>

      <p v-if="error" class="text-sm text-destructive">{{ error }}</p>

      <button
        type="submit"
        :disabled="loading || !guestName.trim()"
        class="w-full py-2.5 px-4 text-sm font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
      >
        <svg v-if="loading" class="h-4 w-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        {{ loading ? '참가 중...' : '회의 참가' }}
      </button>
    </form>

    <div class="text-center">
      <NuxtLink to="/login" class="text-sm text-primary hover:underline">
        포털 로그인으로 돌아가기
      </NuxtLink>
    </div>
  </div>
</template>

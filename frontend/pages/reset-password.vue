<script setup lang="ts">
definePageMeta({ layout: 'auth' })

const route = useRoute()
const token = computed(() => (route.query.token as string) || '')

const newPassword = ref('')
const confirmPassword = ref('')
const error = ref('')
const submitting = ref(false)
const success = ref(false)

async function handleSubmit() {
  error.value = ''

  if (!token.value) {
    error.value = '유효하지 않은 재설정 링크입니다.'
    return
  }

  if (newPassword.value.length < 8) {
    error.value = '비밀번호는 최소 8자 이상이어야 합니다.'
    return
  }

  if (newPassword.value !== confirmPassword.value) {
    error.value = '비밀번호가 일치하지 않습니다.'
    return
  }

  submitting.value = true

  try {
    await $fetch('/api/auth/reset-password', {
      method: 'POST',
      body: { token: token.value, new_password: newPassword.value },
    })
    success.value = true
  } catch (e: any) {
    error.value = e?.data?.detail || '처리 중 오류가 발생했습니다.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="w-full max-w-sm space-y-6">
    <div class="text-center space-y-2">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-12 w-12 mx-auto text-primary">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
        <path d="M7 11V7a5 5 0 0 1 10 0v4" />
      </svg>
      <h1 class="text-2xl font-bold">비밀번호 재설정</h1>
      <p class="text-sm text-muted-foreground">
        새 비밀번호를 입력해주세요
      </p>
    </div>

    <!-- Success message -->
    <div v-if="success" class="rounded-lg border border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950 p-4 space-y-3">
      <div class="flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-5 w-5 text-green-600 dark:text-green-400">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" />
        </svg>
        <p class="font-medium text-green-800 dark:text-green-200">재설정 완료</p>
      </div>
      <p class="text-sm text-green-700 dark:text-green-300">비밀번호가 재설정되었습니다. 새 비밀번호로 로그인해주세요.</p>
      <NuxtLink
        to="/login"
        class="inline-block text-sm font-medium text-primary hover:underline"
      >
        로그인 페이지로 이동
      </NuxtLink>
    </div>

    <!-- Form -->
    <form v-else @submit.prevent="handleSubmit" class="space-y-4">
      <div>
        <label for="new-password" class="block text-sm font-medium mb-1.5">새 비밀번호</label>
        <input
          id="new-password"
          v-model="newPassword"
          type="password"
          autocomplete="new-password"
          placeholder="8자 이상"
          class="w-full px-3 py-2.5 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
          autofocus
        />
      </div>

      <div>
        <label for="confirm-password" class="block text-sm font-medium mb-1.5">비밀번호 확인</label>
        <input
          id="confirm-password"
          v-model="confirmPassword"
          type="password"
          autocomplete="new-password"
          placeholder="비밀번호를 다시 입력"
          class="w-full px-3 py-2.5 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
        />
      </div>

      <p v-if="error" class="text-sm text-destructive">{{ error }}</p>

      <UiButton
        type="submit"
        class="w-full"
        size="lg"
        :disabled="submitting"
      >
        <svg v-if="submitting" class="h-4 w-4 mr-2 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        {{ submitting ? '처리 중...' : '비밀번호 재설정' }}
      </UiButton>

      <p class="text-center text-sm text-muted-foreground">
        <NuxtLink to="/login" class="text-primary hover:underline font-medium">로그인으로 돌아가기</NuxtLink>
      </p>
    </form>
  </div>
</template>

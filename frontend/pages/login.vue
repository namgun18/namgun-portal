<script setup lang="ts">
definePageMeta({ layout: 'auth' })

const { nativeLogin, user } = useAuth()
const route = useRoute()

const username = ref('')
const password = ref('')
const rememberMe = ref(false)
const error = ref('')
const submitting = ref(false)

// Redirect destination after login (from query param or default to dashboard)
const redirectTo = computed(() => {
  const r = route.query.redirect as string | undefined
  if (!r) return '/'
  // Allow relative paths (e.g. /oauth/authorize?...)
  if (r.startsWith('/')) return r
  // Allow HTTPS URLs from our domain
  if (r.startsWith('https://') && r.includes('.namgun.or.kr')) return r
  return '/'
})

// If already logged in, redirect
watch(user, (u) => {
  if (u) {
    const dest = redirectTo.value
    if (dest.startsWith('https://') || dest.startsWith('/oauth/')) {
      if (import.meta.client) {
        window.location.href = dest
      } else {
        navigateTo(dest, { external: true })
      }
    } else {
      navigateTo(dest)
    }
  }
}, { immediate: true })

async function handleSubmit() {
  if (!username.value.trim() || !password.value) {
    error.value = '사용자명과 비밀번호를 입력하세요.'
    return
  }
  submitting.value = true
  error.value = ''
  try {
    await nativeLogin(username.value.trim(), password.value, rememberMe.value)
    const dest = redirectTo.value
    if (dest.startsWith('https://') || dest.startsWith('/oauth/')) {
      window.location.href = dest
    } else {
      navigateTo(dest)
    }
  } catch (e: any) {
    const detail = e?.data?.detail || ''
    const statusCode = e?.statusCode || e?.status || 0
    if (detail) {
      error.value = detail
    } else if (statusCode === 401) {
      error.value = '사용자명 또는 비밀번호가 올바르지 않습니다.'
    } else if (statusCode === 502) {
      error.value = '인증 서버에 연결할 수 없습니다.'
    } else {
      error.value = '로그인 중 오류가 발생했습니다. 다시 시도해주세요.'
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="w-full max-w-sm space-y-6">
    <div class="text-center space-y-2">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-12 w-12 mx-auto text-primary">
        <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>
      <h1 class="text-2xl font-bold">namgun.or.kr Portal</h1>
      <p class="text-sm text-muted-foreground">
        서비스에 접근하려면 로그인하세요
      </p>
    </div>

    <form @submit.prevent="handleSubmit" class="space-y-4">
      <div>
        <label for="username" class="block text-sm font-medium mb-1.5">사용자명 또는 이메일</label>
        <input
          id="username"
          v-model="username"
          type="text"
          autocomplete="username"
          placeholder="사용자명 또는 이메일"
          class="w-full px-3 py-2.5 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
          autofocus
        />
      </div>

      <div>
        <div class="flex items-center justify-between mb-1.5">
          <label for="password" class="block text-sm font-medium">비밀번호</label>
          <NuxtLink to="/forgot-password" class="text-xs text-primary hover:underline">비밀번호 찾기</NuxtLink>
        </div>
        <input
          id="password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          placeholder="비밀번호"
          class="w-full px-3 py-2.5 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
        />
      </div>

      <div class="flex items-center gap-2">
        <input
          id="rememberMe"
          v-model="rememberMe"
          type="checkbox"
          class="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary/50"
        />
        <label for="rememberMe" class="text-sm text-muted-foreground select-none cursor-pointer">로그인 상태 유지</label>
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
        {{ submitting ? '로그인 중...' : '로그인' }}
      </UiButton>

      <p class="text-center text-sm text-muted-foreground">
        계정이 없으신가요?
        <NuxtLink to="/register" class="text-primary hover:underline font-medium">회원가입</NuxtLink>
      </p>
    </form>

    <!-- Demo button -->
    <div class="relative">
      <div class="absolute inset-0 flex items-center">
        <span class="w-full border-t" />
      </div>
      <div class="relative flex justify-center text-xs uppercase">
        <span class="bg-background px-2 text-muted-foreground">또는</span>
      </div>
    </div>

    <a
      href="https://demo.namgun.or.kr"
      class="flex items-center justify-center gap-2 w-full py-3 px-4 text-sm font-medium rounded-lg border-2 border-dashed border-primary/40 text-primary hover:bg-primary/5 hover:border-primary/60 transition-colors"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5">
        <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
      데모 체험하기
      <span class="text-xs text-muted-foreground font-normal">(로그인 불필요)</span>
    </a>

  </div>
</template>

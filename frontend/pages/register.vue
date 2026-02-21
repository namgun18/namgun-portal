<script setup lang="ts">
definePageMeta({ layout: 'auth' })

const { register } = useAuth()

const form = reactive({
  username: '',
  password: '',
  passwordConfirm: '',
  display_name: '',
  recovery_email: '',
})
const error = ref('')
const submitting = ref(false)
const success = ref(false)

const emailPreview = computed(() =>
  form.username ? `${form.username.toLowerCase()}@namgun.or.kr` : ''
)

async function handleSubmit() {
  error.value = ''

  if (!form.username || !form.password || !form.display_name || !form.recovery_email) {
    error.value = '모든 필드를 입력해주세요.'
    return
  }

  if (form.password !== form.passwordConfirm) {
    error.value = '비밀번호가 일치하지 않습니다.'
    return
  }

  if (form.password.length < 8) {
    error.value = '비밀번호는 최소 8자 이상이어야 합니다.'
    return
  }

  if (form.recovery_email.endsWith('@namgun.or.kr')) {
    error.value = '복구 이메일은 외부 이메일 주소를 사용해주세요.'
    return
  }

  submitting.value = true
  try {
    await register({
      username: form.username.trim().toLowerCase(),
      password: form.password,
      display_name: form.display_name.trim(),
      recovery_email: form.recovery_email.trim(),
    })
    success.value = true
  } catch (e: any) {
    const detail = e?.data?.detail
    if (Array.isArray(detail)) {
      error.value = detail.map((d: any) => d.msg?.replace('Value error, ', '') || d.msg).join(', ')
    } else if (typeof detail === 'string') {
      error.value = detail
    } else {
      error.value = '회원가입 중 오류가 발생했습니다.'
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
      <h1 class="text-2xl font-bold">회원가입</h1>
      <p class="text-sm text-muted-foreground">
        namgun.or.kr 포털 계정을 만드세요
      </p>
    </div>

    <!-- Success message -->
    <div v-if="success" class="rounded-lg border border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950 p-4 space-y-3">
      <div class="flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-5 w-5 text-green-600 dark:text-green-400">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" />
        </svg>
        <p class="font-medium text-green-800 dark:text-green-200">가입 신청 완료</p>
      </div>
      <p class="text-sm text-green-700 dark:text-green-300">
        복구 이메일로 인증 링크를 전송했습니다. 이메일을 확인하여 인증을 완료해주세요.
        인증 완료 후 관리자 승인이 이루어지면 로그인이 가능합니다.
      </p>
      <NuxtLink
        to="/login"
        class="inline-block text-sm font-medium text-primary hover:underline"
      >
        로그인 페이지로 돌아가기
      </NuxtLink>
    </div>

    <!-- Registration form -->
    <form v-else @submit.prevent="handleSubmit" class="space-y-4">
      <div>
        <label for="username" class="block text-sm font-medium mb-1.5">사용자명</label>
        <input
          id="username"
          v-model="form.username"
          type="text"
          autocomplete="username"
          placeholder="영문 소문자, 숫자, 점, 하이픈 (3~30자)"
          class="w-full px-3 py-2.5 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
          autofocus
        />
        <p v-if="emailPreview" class="mt-1 text-xs text-muted-foreground">
          이메일: <span class="font-medium">{{ emailPreview }}</span>
        </p>
      </div>

      <div>
        <label for="display_name" class="block text-sm font-medium mb-1.5">표시 이름</label>
        <input
          id="display_name"
          v-model="form.display_name"
          type="text"
          placeholder="다른 사용자에게 표시될 이름"
          class="w-full px-3 py-2.5 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
        />
      </div>

      <div>
        <label for="password" class="block text-sm font-medium mb-1.5">비밀번호</label>
        <input
          id="password"
          v-model="form.password"
          type="password"
          autocomplete="new-password"
          placeholder="최소 8자"
          class="w-full px-3 py-2.5 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
        />
      </div>

      <div>
        <label for="passwordConfirm" class="block text-sm font-medium mb-1.5">비밀번호 확인</label>
        <input
          id="passwordConfirm"
          v-model="form.passwordConfirm"
          type="password"
          autocomplete="new-password"
          placeholder="비밀번호를 다시 입력하세요"
          class="w-full px-3 py-2.5 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
        />
      </div>

      <div>
        <label for="recovery_email" class="block text-sm font-medium mb-1.5">복구 이메일</label>
        <input
          id="recovery_email"
          v-model="form.recovery_email"
          type="email"
          placeholder="비밀번호 찾기에 사용할 외부 이메일"
          class="w-full px-3 py-2.5 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
        />
        <p class="mt-1 text-xs text-muted-foreground">
          @namgun.or.kr 이외의 외부 이메일을 입력해주세요
        </p>
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
        {{ submitting ? '처리 중...' : '회원가입' }}
      </UiButton>

      <p class="text-center text-sm text-muted-foreground">
        이미 계정이 있으신가요?
        <NuxtLink to="/login" class="text-primary hover:underline font-medium">로그인</NuxtLink>
      </p>
    </form>
  </div>
</template>

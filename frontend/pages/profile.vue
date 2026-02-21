<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { user, updateProfile, changePassword } = useAuth()

// Profile form
const profileForm = reactive({
  display_name: user.value?.display_name || '',
  recovery_email: user.value?.recovery_email || '',
})
const profileError = ref('')
const profileSuccess = ref('')
const profileSubmitting = ref(false)

// Password form
const passwordForm = reactive({
  current: '',
  newPassword: '',
  confirm: '',
})
const passwordError = ref('')
const passwordSuccess = ref('')
const passwordSubmitting = ref(false)

// Track original recovery_email for change detection
const originalRecoveryEmail = ref(user.value?.recovery_email || '')

// Sync profile form when user loads
watch(user, (u) => {
  if (u) {
    profileForm.display_name = u.display_name || ''
    profileForm.recovery_email = u.recovery_email || ''
    originalRecoveryEmail.value = u.recovery_email || ''
  }
}, { immediate: true })

async function handleProfileSubmit() {
  profileError.value = ''
  profileSuccess.value = ''
  profileSubmitting.value = true

  try {
    const updates: { display_name?: string; recovery_email?: string } = {}
    if (profileForm.display_name !== (user.value?.display_name || '')) {
      updates.display_name = profileForm.display_name.trim()
    }
    if (profileForm.recovery_email !== originalRecoveryEmail.value) {
      updates.recovery_email = profileForm.recovery_email.trim()
    }

    if (Object.keys(updates).length === 0) {
      profileError.value = '변경된 항목이 없습니다.'
      return
    }

    await updateProfile(updates)
    originalRecoveryEmail.value = profileForm.recovery_email
    profileSuccess.value = '프로필이 수정되었습니다.'
  } catch (e: any) {
    const detail = e?.data?.detail
    if (Array.isArray(detail)) {
      profileError.value = detail.map((d: any) => d.msg?.replace('Value error, ', '') || d.msg).join(', ')
    } else {
      profileError.value = typeof detail === 'string' ? detail : '프로필 수정 중 오류가 발생했습니다.'
    }
  } finally {
    profileSubmitting.value = false
  }
}

async function handlePasswordSubmit() {
  passwordError.value = ''
  passwordSuccess.value = ''

  if (!passwordForm.current || !passwordForm.newPassword) {
    passwordError.value = '모든 필드를 입력해주세요.'
    return
  }

  if (passwordForm.newPassword !== passwordForm.confirm) {
    passwordError.value = '새 비밀번호가 일치하지 않습니다.'
    return
  }

  if (passwordForm.newPassword.length < 8) {
    passwordError.value = '비밀번호는 최소 8자 이상이어야 합니다.'
    return
  }

  passwordSubmitting.value = true
  try {
    await changePassword(passwordForm.current, passwordForm.newPassword)
    passwordSuccess.value = '비밀번호가 변경되었습니다.'
    passwordForm.current = ''
    passwordForm.newPassword = ''
    passwordForm.confirm = ''
  } catch (e: any) {
    passwordError.value = e?.data?.detail || '비밀번호 변경 중 오류가 발생했습니다.'
  } finally {
    passwordSubmitting.value = false
  }
}
</script>

<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold tracking-tight">프로필</h1>
      <p class="text-muted-foreground mt-1">계정 정보 및 비밀번호를 관리하세요</p>
    </div>

    <div class="grid gap-6 max-w-2xl">
      <!-- Profile section -->
      <div class="rounded-lg border bg-card p-6 space-y-4">
        <h2 class="text-lg font-semibold">사용자 정보</h2>

        <form @submit.prevent="handleProfileSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1.5 text-muted-foreground">사용자명</label>
            <input
              :value="user?.username"
              disabled
              class="w-full px-3 py-2.5 text-sm border rounded-lg bg-muted cursor-not-allowed"
            />
          </div>

          <div>
            <label class="block text-sm font-medium mb-1.5 text-muted-foreground">이메일</label>
            <input
              :value="user?.email"
              disabled
              class="w-full px-3 py-2.5 text-sm border rounded-lg bg-muted cursor-not-allowed"
            />
          </div>

          <div>
            <label for="display_name" class="block text-sm font-medium mb-1.5">표시 이름</label>
            <input
              id="display_name"
              v-model="profileForm.display_name"
              type="text"
              class="w-full px-3 py-2.5 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
            />
          </div>

          <div>
            <label for="recovery_email" class="block text-sm font-medium mb-1.5">복구 이메일</label>
            <input
              id="recovery_email"
              v-model="profileForm.recovery_email"
              type="email"
              placeholder="비밀번호 찾기에 사용할 외부 이메일"
              class="w-full px-3 py-2.5 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
            />
            <p class="mt-1 text-xs text-muted-foreground">@namgun.or.kr 이외의 외부 이메일</p>
          </div>

          <p v-if="profileError" class="text-sm text-destructive">{{ profileError }}</p>
          <p v-if="profileSuccess" class="text-sm text-green-600 dark:text-green-400">{{ profileSuccess }}</p>

          <UiButton type="submit" :disabled="profileSubmitting">
            {{ profileSubmitting ? '저장 중...' : '저장' }}
          </UiButton>
        </form>
      </div>

      <!-- Password section -->
      <div class="rounded-lg border bg-card p-6 space-y-4">
        <h2 class="text-lg font-semibold">비밀번호 변경</h2>

        <form @submit.prevent="handlePasswordSubmit" class="space-y-4">
          <div>
            <label for="current_password" class="block text-sm font-medium mb-1.5">현재 비밀번호</label>
            <input
              id="current_password"
              v-model="passwordForm.current"
              type="password"
              autocomplete="current-password"
              class="w-full px-3 py-2.5 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
            />
          </div>

          <div>
            <label for="new_password" class="block text-sm font-medium mb-1.5">새 비밀번호</label>
            <input
              id="new_password"
              v-model="passwordForm.newPassword"
              type="password"
              autocomplete="new-password"
              placeholder="최소 8자"
              class="w-full px-3 py-2.5 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
            />
          </div>

          <div>
            <label for="confirm_password" class="block text-sm font-medium mb-1.5">새 비밀번호 확인</label>
            <input
              id="confirm_password"
              v-model="passwordForm.confirm"
              type="password"
              autocomplete="new-password"
              class="w-full px-3 py-2.5 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
            />
          </div>

          <p v-if="passwordError" class="text-sm text-destructive">{{ passwordError }}</p>
          <p v-if="passwordSuccess" class="text-sm text-green-600 dark:text-green-400">{{ passwordSuccess }}</p>

          <UiButton type="submit" :disabled="passwordSubmitting">
            {{ passwordSubmitting ? '변경 중...' : '비밀번호 변경' }}
          </UiButton>
        </form>
      </div>
    </div>
  </div>
</template>

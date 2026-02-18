<script setup lang="ts">
definePageMeta({ layout: 'auth' })

const { login, user } = useAuth()

// If already logged in, redirect to dashboard
watch(user, (u) => {
  if (u) navigateTo('/')
}, { immediate: true })
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

    <UiButton class="w-full" size="lg" @click="login">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5 mr-2">
        <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" /><polyline points="10 17 15 12 10 7" /><line x1="15" y1="12" x2="3" y2="12" />
      </svg>
      Authentik으로 로그인
    </UiButton>
  </div>
</template>

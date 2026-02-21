<script setup lang="ts">
definePageMeta({ layout: 'auth' })

onMounted(() => {
  window.close()
})
</script>

<template>
  <div class="flex flex-col items-center justify-center min-h-screen gap-4 text-center px-4">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="h-16 w-16 text-muted-foreground/50">
      <path d="M23 7l-7 5 7 5V7z" /><rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
    </svg>
    <h1 class="text-lg font-semibold">회의가 종료되었습니다</h1>
    <p class="text-sm text-muted-foreground">이 탭을 닫아도 됩니다.</p>
    <NuxtLink to="/meetings" class="text-sm text-primary hover:underline">
      포털로 돌아가기
    </NuxtLink>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'auth' })

// Fallback page - actual callback is handled by FastAPI
// This page shows while waiting for redirect
</script>

<template>
  <div class="text-center space-y-4">
    <div class="animate-spin h-8 w-8 mx-auto border-4 border-primary border-t-transparent rounded-full" />
    <p class="text-muted-foreground">인증 처리 중...</p>
  </div>
</template>

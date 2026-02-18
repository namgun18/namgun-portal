<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { user } = useAuth()
</script>

<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold tracking-tight">
        대시보드
      </h1>
      <p class="text-muted-foreground mt-1">
        서비스 상태를 한눈에 확인하세요
      </p>
    </div>

    <DashboardServiceGrid />
  </div>
</template>

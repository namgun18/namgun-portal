<script setup lang="ts">
const { services, loading, fetchServices } = useServices()

onMounted(() => {
  fetchServices()
  const interval = setInterval(fetchServices, 60_000)
  onUnmounted(() => clearInterval(interval))
})
</script>

<template>
  <div class="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-lg border bg-card px-4 py-3">
    <template v-if="loading && services.length === 0">
      <div v-for="i in 6" :key="i" class="flex items-center gap-1.5">
        <UiSkeleton class="h-2.5 w-2.5 rounded-full" />
        <UiSkeleton class="h-4 w-16" />
      </div>
    </template>
    <template v-else>
      <div v-for="svc in services" :key="svc.name" class="flex items-center gap-1.5">
        <span
          class="inline-block h-2.5 w-2.5 rounded-full"
          :class="{
            'bg-green-500': svc.status === 'ok',
            'bg-red-500': svc.status === 'down',
            'bg-yellow-500 animate-pulse': svc.status === 'checking',
          }"
        />
        <span class="text-sm">{{ svc.name }}</span>
      </div>
    </template>
  </div>
</template>

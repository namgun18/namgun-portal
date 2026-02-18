<script setup lang="ts">
const { services, loading, fetchServices } = useServices()

// Fetch on mount and refresh every 60s
onMounted(() => {
  fetchServices()
  const interval = setInterval(fetchServices, 60_000)
  onUnmounted(() => clearInterval(interval))
})
</script>

<template>
  <div>
    <!-- Loading skeleton -->
    <div v-if="loading && services.length === 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <UiCard v-for="i in 6" :key="i" class="p-6">
        <UiSkeleton class="h-5 w-24 mb-3" />
        <UiSkeleton class="h-4 w-16 mb-2" />
        <UiSkeleton class="h-4 w-20" />
      </UiCard>
    </div>

    <!-- Service cards -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <DashboardServiceCard
        v-for="svc in services"
        :key="svc.name"
        :name="svc.name"
        :url="svc.url"
        :status="svc.status"
        :response-ms="svc.response_ms"
        :internal-only="svc.internal_only"
      />
    </div>
  </div>
</template>

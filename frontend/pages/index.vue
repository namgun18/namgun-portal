<script setup lang="ts">
definePageMeta({ layout: 'default' })
</script>

<template>
  <div class="h-full overflow-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
    <!-- Greeting -->
    <DashboardGreeting />

    <!-- Service status bar -->
    <DashboardServiceStatus />

    <!-- Main grid: 3 columns on lg -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
      <!-- Left 2 cols: recent mail -->
      <DashboardRecentMail />

      <!-- Right col: shortcuts + storage -->
      <div class="space-y-4">
        <DashboardShortcuts />
        <DashboardStorage />
      </div>

      <!-- Left 2 cols: recent git -->
      <DashboardRecentGit />

      <!-- Right col: game servers -->
      <div class="space-y-4">
        <DashboardGameServers />
      </div>
    </div>
  </div>
</template>

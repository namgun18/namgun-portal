<template>
  <div class="h-screen flex flex-col overflow-hidden">
    <LayoutAppHeader />
    <main class="flex-1 min-h-0">
      <slot />
    </main>
  </div>
</template>

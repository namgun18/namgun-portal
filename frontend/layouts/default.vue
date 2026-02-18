<template>
  <div class="min-h-screen flex flex-col">
    <LayoutAppHeader />
    <main class="flex-1 container px-4 py-6 mx-auto max-w-7xl">
      <slot />
    </main>
    <LayoutAppFooter />
  </div>
</template>

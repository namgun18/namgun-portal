<template>
  <div class="min-h-screen flex flex-col">
    <LayoutAppHeader />
    <main class="flex-1 container px-4 sm:px-6 lg:px-8 py-6 mx-auto max-w-[1400px]">
      <slot />
    </main>
    <LayoutAppFooter />
  </div>
</template>

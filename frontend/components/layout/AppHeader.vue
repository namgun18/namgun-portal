<script setup lang="ts">
const { user, logout } = useAuth()
const colorMode = useColorMode()
const route = useRoute()
const mobileMenuOpen = ref(false)

function toggleDark() {
  colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
}
</script>

<template>
  <header class="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
    <div class="flex h-14 items-center justify-between px-3 sm:px-4 mx-auto max-w-7xl">
      <!-- Logo + Nav -->
      <div class="flex items-center gap-2 sm:gap-6">
        <NuxtLink to="/" class="flex items-center gap-2 font-bold text-lg shrink-0">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-6 w-6">
            <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
            <polyline points="9 22 9 12 15 12 15 22" />
          </svg>
          <span class="hidden sm:inline">namgun.or.kr</span>
        </NuxtLink>

        <!-- Desktop nav -->
        <nav v-if="user" class="hidden sm:flex items-center gap-1">
          <NuxtLink
            to="/"
            class="px-3 py-1.5 text-sm font-medium rounded-md transition-colors"
            :class="route.path === '/' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'"
          >
            대시보드
          </NuxtLink>
          <NuxtLink
            to="/files"
            class="px-3 py-1.5 text-sm font-medium rounded-md transition-colors"
            :class="route.path.startsWith('/files') ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'"
          >
            파일
          </NuxtLink>
          <NuxtLink
            to="/mail"
            class="px-3 py-1.5 text-sm font-medium rounded-md transition-colors"
            :class="route.path === '/mail' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'"
          >
            메일
          </NuxtLink>
          <NuxtLink
            to="/meetings"
            class="px-3 py-1.5 text-sm font-medium rounded-md transition-colors"
            :class="route.path === '/meetings' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'"
          >
            회의
          </NuxtLink>
        </nav>
      </div>

      <!-- Right side -->
      <div class="flex items-center gap-1 sm:gap-3">
        <!-- Mobile nav toggle -->
        <button
          v-if="user"
          @click="mobileMenuOpen = !mobileMenuOpen"
          class="sm:hidden inline-flex items-center justify-center h-9 w-9 rounded-md hover:bg-accent transition-colors"
        >
          <svg v-if="!mobileMenuOpen" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5">
            <line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="18" x2="21" y2="18" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        <!-- Dark mode toggle -->
        <button
          @click="toggleDark"
          class="inline-flex items-center justify-center h-9 w-9 rounded-md hover:bg-accent transition-colors"
          :title="colorMode.value === 'dark' ? '라이트 모드' : '다크 모드'"
        >
          <svg v-if="colorMode.value === 'dark'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5">
            <circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" /><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
          </svg>
        </button>

        <!-- User dropdown -->
        <UiDropdownMenu v-if="user">
          <template #trigger>
            <button class="flex items-center gap-2 rounded-md px-1.5 sm:px-2 py-1 hover:bg-accent transition-colors">
              <UiAvatar
                :src="user.avatar_url"
                :alt="user.display_name ?? user.username"
                :fallback="(user.display_name ?? user.username).charAt(0).toUpperCase()"
                class="h-8 w-8"
              />
              <span class="hidden sm:inline text-sm font-medium max-w-[120px] truncate">
                {{ user.display_name ?? user.username }}
              </span>
            </button>
          </template>
          <template #content>
            <div class="px-3 py-2 text-sm text-muted-foreground border-b">
              {{ user.email }}
            </div>
            <button
              @click="logout"
              class="w-full px-3 py-2 text-sm text-left hover:bg-accent transition-colors text-destructive"
            >
              로그아웃
            </button>
          </template>
        </UiDropdownMenu>
      </div>
    </div>

    <!-- Mobile navigation dropdown -->
    <div
      v-if="mobileMenuOpen && user"
      class="sm:hidden border-t bg-background px-3 py-2 space-y-1"
    >
      <NuxtLink
        to="/"
        @click="mobileMenuOpen = false"
        class="block px-3 py-2 text-sm font-medium rounded-md transition-colors"
        :class="route.path === '/' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50'"
      >
        대시보드
      </NuxtLink>
      <NuxtLink
        to="/files"
        @click="mobileMenuOpen = false"
        class="block px-3 py-2 text-sm font-medium rounded-md transition-colors"
        :class="route.path.startsWith('/files') ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50'"
      >
        파일
      </NuxtLink>
      <NuxtLink
        to="/mail"
        @click="mobileMenuOpen = false"
        class="block px-3 py-2 text-sm font-medium rounded-md transition-colors"
        :class="route.path === '/mail' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50'"
      >
        메일
      </NuxtLink>
      <NuxtLink
        to="/meetings"
        @click="mobileMenuOpen = false"
        class="block px-3 py-2 text-sm font-medium rounded-md transition-colors"
        :class="route.path === '/meetings' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50'"
      >
        회의
      </NuxtLink>
    </div>
  </header>
</template>

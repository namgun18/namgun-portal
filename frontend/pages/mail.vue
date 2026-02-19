<script setup lang="ts">
import MailSidebar from '~/components/mail/MailSidebar.vue'
import MailList from '~/components/mail/MailList.vue'
import MailView from '~/components/mail/MailView.vue'
import MailCompose from '~/components/mail/MailCompose.vue'

definePageMeta({ layout: 'default' })

const {
  fetchMailboxes,
  fetchMessages,
  openCompose,
  refresh,
  selectedMessage,
  showCompose,
} = useMail()

const showMobileSidebar = ref(false)

onMounted(async () => {
  await fetchMailboxes()
  await fetchMessages()
})
</script>

<template>
  <div class="flex h-[calc(100vh-3.5rem)] overflow-hidden relative">
    <!-- Mobile sidebar overlay -->
    <div
      v-if="showMobileSidebar"
      class="md:hidden fixed inset-0 z-30 bg-black/40"
      @click="showMobileSidebar = false"
    />

    <!-- Sidebar -->
    <div
      class="shrink-0 h-full z-30 transition-transform duration-200
        fixed md:relative
        w-64 md:w-56
        bg-background md:bg-transparent
        shadow-xl md:shadow-none"
      :class="showMobileSidebar ? 'translate-x-0' : '-translate-x-full md:translate-x-0'"
    >
      <MailSidebar @navigate="showMobileSidebar = false" />
    </div>

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Command bar -->
      <div class="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-4 py-2 border-b bg-background">
        <!-- Mobile sidebar toggle -->
        <button
          @click="showMobileSidebar = !showMobileSidebar"
          class="md:hidden inline-flex items-center justify-center h-8 w-8 rounded-md hover:bg-accent transition-colors shrink-0"
          title="메뉴"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
            <line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>

        <!-- New mail button -->
        <button
          @click="openCompose('new')"
          class="inline-flex items-center gap-1.5 px-2 sm:px-3 py-1.5 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          <span class="hidden sm:inline">새 메일</span>
        </button>

        <!-- Refresh -->
        <button
          @click="refresh"
          class="inline-flex items-center gap-1.5 px-2 sm:px-3 py-1.5 text-sm font-medium rounded-md border hover:bg-accent transition-colors"
          title="새로고침"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
            <polyline points="23 4 23 10 17 10" /><polyline points="1 20 1 14 7 14" /><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
          </svg>
          <span class="hidden sm:inline">새로고침</span>
        </button>

        <div class="flex-1" />
      </div>

      <!-- Mail content: list + view -->
      <div class="flex flex-1 min-h-0">
        <!-- Message list (hide on mobile when viewing a message) -->
        <div
          class="flex flex-col min-w-0"
          :class="selectedMessage ? 'hidden md:flex md:w-80 md:shrink-0 md:border-r' : 'flex-1'"
        >
          <MailList />
        </div>

        <!-- Message view -->
        <MailView />
      </div>
    </div>

    <!-- Compose modal -->
    <MailCompose />
  </div>
</template>

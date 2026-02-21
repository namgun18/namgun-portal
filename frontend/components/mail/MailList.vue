<script setup lang="ts">
const {
  messages,
  loadingMessages,
  selectedMessage,
  currentPage,
  totalMessages,
  totalPages,
  hasNextPage,
  hasPrevPage,
  openMessage,
  toggleStar,
  toggleRead,
  nextPage,
  prevPage,
  limit,
  searchQuery,
  setSearchQuery,
  selectedIds,
  toggleSelect,
  selectAll,
  deselectAll,
  bulkAction,
} = useMail()

const hasSelection = computed(() => selectedIds.value.size > 0)
const allSelected = computed(() =>
  messages.value.length > 0 && messages.value.every(m => selectedIds.value.has(m.id))
)

function handleSelectAll() {
  if (allSelected.value) deselectAll()
  else selectAll()
}

function handleCheckbox(e: Event, id: string) {
  e.stopPropagation()
  toggleSelect(id)
}

const localSearch = ref('')
let searchTimeout: ReturnType<typeof setTimeout> | null = null

function handleSearchInput() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    setSearchQuery(localSearch.value)
  }, 300)
}

function clearSearch() {
  localSearch.value = ''
  setSearchQuery('')
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  if (isToday) {
    return d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
  }
  const thisYear = d.getFullYear() === now.getFullYear()
  if (thisYear) {
    return `${d.getMonth() + 1}/${d.getDate()}`
  }
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`
}

function senderName(msg: any): string {
  if (!msg.from_ || msg.from_.length === 0) return '(발신자 없음)'
  const addr = msg.from_[0]
  return addr.name || addr.email
}

function handleStarClick(e: Event, id: string) {
  e.stopPropagation()
  toggleStar(id)
}

function handleReadClick(e: Event, id: string) {
  e.stopPropagation()
  toggleRead(id)
}
</script>

<template>
  <div class="flex flex-col flex-1 min-w-0">
    <!-- Search bar -->
    <div class="px-3 sm:px-4 py-2 border-b">
      <div class="relative">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground">
          <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          v-model="localSearch"
          @input="handleSearchInput"
          type="text"
          placeholder="메일 검색..."
          class="w-full pl-9 pr-8 py-1.5 text-sm bg-muted/50 border-0 rounded-md focus:outline-none focus:ring-1 focus:ring-primary"
        />
        <button
          v-if="localSearch"
          @click="clearSearch"
          class="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Bulk action bar -->
    <div v-if="hasSelection" class="flex items-center gap-2 px-3 sm:px-4 py-2 border-b bg-primary/5">
      <input
        type="checkbox"
        :checked="allSelected"
        @change="handleSelectAll"
        class="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary/50"
      />
      <span class="text-sm text-muted-foreground">{{ selectedIds.size }}건 선택</span>
      <div class="flex items-center gap-1 ml-auto">
        <button @click="bulkAction('read')" class="px-2 py-1 text-xs rounded hover:bg-accent" title="읽음 표시">읽음</button>
        <button @click="bulkAction('unread')" class="px-2 py-1 text-xs rounded hover:bg-accent" title="안읽음 표시">안읽음</button>
        <button @click="bulkAction('delete')" class="px-2 py-1 text-xs rounded hover:bg-accent text-destructive" title="삭제">삭제</button>
        <button @click="deselectAll" class="px-2 py-1 text-xs rounded hover:bg-accent" title="선택 해제">취소</button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loadingMessages" class="flex-1 p-4 space-y-2">
      <div v-for="i in 8" :key="i" class="h-16 bg-muted/50 rounded animate-pulse" />
    </div>

    <!-- Empty state -->
    <div v-else-if="messages.length === 0" class="flex-1 flex flex-col items-center justify-center text-muted-foreground">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="h-12 w-12 mb-3 opacity-50">
        <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" /><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
      </svg>
      <p class="text-sm">메일이 없습니다</p>
    </div>

    <!-- Message list -->
    <div v-else class="flex-1 overflow-auto">
      <div
        v-for="msg in messages"
        :key="msg.id"
        @click="openMessage(msg.id)"
        class="flex items-start gap-3 px-3 sm:px-4 py-3 border-b cursor-pointer transition-colors hover:bg-accent/50"
        :class="[
          selectedMessage?.id === msg.id ? 'bg-accent/40' : '',
          msg.is_unread ? 'bg-primary/5' : '',
        ]"
      >
        <!-- Checkbox / Unread dot -->
        <div class="pt-1 shrink-0 w-5 flex items-center justify-center">
          <input
            v-if="hasSelection"
            type="checkbox"
            :checked="selectedIds.has(msg.id)"
            @click="handleCheckbox($event, msg.id)"
            class="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary/50"
          />
          <template v-else>
            <div
              v-if="msg.is_unread"
              class="w-2 h-2 rounded-full bg-primary"
              title="읽지 않음"
              @click="handleReadClick($event, msg.id)"
            />
            <div
              v-else
              class="w-2 h-2 rounded-full cursor-pointer hover:bg-muted-foreground/30"
              @click="handleReadClick($event, msg.id)"
            />
          </template>
        </div>

        <!-- Star -->
        <button
          @click="handleStarClick($event, msg.id)"
          class="shrink-0 mt-0.5"
          :title="msg.is_flagged ? '별표 해제' : '별표'"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
            :fill="msg.is_flagged ? 'currentColor' : 'none'"
            stroke="currentColor" stroke-width="2"
            class="h-4 w-4 transition-colors"
            :class="msg.is_flagged ? 'text-yellow-500' : 'text-muted-foreground/40 hover:text-yellow-500'"
          >
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
          </svg>
        </button>

        <!-- Content -->
        <div class="flex-1 min-w-0">
          <div class="flex items-baseline gap-2">
            <span
              class="text-sm truncate"
              :class="msg.is_unread ? 'font-semibold text-foreground' : 'text-foreground'"
            >
              {{ senderName(msg) }}
            </span>
            <span class="text-xs text-muted-foreground shrink-0 ml-auto">
              {{ formatDate(msg.received_at) }}
            </span>
          </div>
          <div class="flex items-center gap-1.5">
            <span
              class="text-sm truncate"
              :class="msg.is_unread ? 'font-medium text-foreground' : 'text-muted-foreground'"
            >
              {{ msg.subject || '(제목 없음)' }}
            </span>
            <!-- Attachment icon -->
            <svg
              v-if="msg.has_attachment"
              xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
              class="h-3.5 w-3.5 shrink-0 text-muted-foreground"
            >
              <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48" />
            </svg>
          </div>
          <p class="text-xs text-muted-foreground truncate mt-0.5">
            {{ msg.preview || '' }}
          </p>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalMessages > 0" class="flex items-center justify-between px-3 sm:px-4 py-2 border-t bg-background text-xs text-muted-foreground">
      <span>
        {{ currentPage * limit + 1 }}-{{ Math.min((currentPage + 1) * limit, totalMessages) }} / {{ totalMessages }}건
      </span>
      <div class="flex items-center gap-1">
        <button
          @click="prevPage"
          :disabled="!hasPrevPage"
          class="h-7 w-7 flex items-center justify-center rounded hover:bg-accent transition-colors disabled:opacity-30"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
        <button
          @click="nextPage"
          :disabled="!hasNextPage"
          class="h-7 w-7 flex items-center justify-center rounded hover:bg-accent transition-colors disabled:opacity-30"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

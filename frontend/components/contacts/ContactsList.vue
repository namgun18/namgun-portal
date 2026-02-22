<script setup lang="ts">
import type { Contact } from '~/composables/useContacts'

const {
  contacts, selectedContact, loadingContacts, searchQuery, totalContacts,
  currentPage, totalPages, hasNextPage, hasPrevPage,
  setSearchQuery, selectContact, nextPage, prevPage,
} = useContacts()

const localSearch = ref(searchQuery.value)
let searchTimer: ReturnType<typeof setTimeout> | null = null

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    setSearchQuery(localSearch.value)
  }, 300)
}

function getInitials(contact: Contact) {
  if (contact.name) return contact.name.charAt(0).toUpperCase()
  if (contact.first_name) return contact.first_name.charAt(0).toUpperCase()
  return '?'
}

function getPrimaryEmail(contact: Contact) {
  return contact.emails?.[0]?.value || ''
}

const AVATAR_COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4']

function avatarColor(contact: Contact) {
  const hash = contact.id.split('').reduce((a, c) => a + c.charCodeAt(0), 0)
  return AVATAR_COLORS[hash % AVATAR_COLORS.length]
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Search -->
    <div class="p-3 border-b shrink-0">
      <div class="relative">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input
          v-model="localSearch"
          @input="onSearchInput"
          type="text"
          placeholder="연락처 검색..."
          class="w-full pl-9 pr-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
        />
      </div>
      <div class="mt-1 text-xs text-muted-foreground">{{ totalContacts }}명의 연락처</div>
    </div>

    <!-- List -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="loadingContacts" class="p-4 text-sm text-muted-foreground text-center">불러오는 중...</div>
      <div v-else-if="contacts.length === 0" class="p-4 text-sm text-muted-foreground text-center">연락처가 없습니다</div>
      <div v-else>
        <button
          v-for="contact in contacts"
          :key="contact.id"
          @click="selectContact(contact)"
          class="w-full flex items-center gap-3 px-3 py-2.5 text-left hover:bg-accent/50 transition-colors border-b last:border-b-0"
          :class="{ 'bg-accent': selectedContact?.id === contact.id }"
        >
          <div
            class="w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-medium shrink-0"
            :style="{ backgroundColor: avatarColor(contact) }"
          >
            {{ getInitials(contact) }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium truncate">{{ contact.name }}</div>
            <div v-if="getPrimaryEmail(contact)" class="text-xs text-muted-foreground truncate">
              {{ getPrimaryEmail(contact) }}
            </div>
            <div v-else-if="contact.organization" class="text-xs text-muted-foreground truncate">
              {{ contact.organization }}
            </div>
          </div>
        </button>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-between px-3 py-2 border-t text-xs shrink-0">
      <button @click="prevPage" :disabled="!hasPrevPage" class="px-2 py-1 rounded hover:bg-accent disabled:opacity-30">이전</button>
      <span class="text-muted-foreground">{{ currentPage + 1 }} / {{ totalPages }}</span>
      <button @click="nextPage" :disabled="!hasNextPage" class="px-2 py-1 rounded hover:bg-accent disabled:opacity-30">다음</button>
    </div>
  </div>
</template>

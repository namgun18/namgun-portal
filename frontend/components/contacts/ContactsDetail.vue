<script setup lang="ts">
import type { Contact } from '~/composables/useContacts'

const { selectedContact, openEditModal, deleteContact } = useContacts()

const AVATAR_COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4']

function avatarColor(contact: Contact) {
  const hash = contact.id.split('').reduce((a, c) => a + c.charCodeAt(0), 0)
  return AVATAR_COLORS[hash % AVATAR_COLORS.length]
}

function getInitials(contact: Contact) {
  if (contact.name) return contact.name.charAt(0).toUpperCase()
  return '?'
}

function typeLabel(type: string) {
  const map: Record<string, string> = { home: '개인', work: '직장', other: '기타' }
  return map[type] || type
}

async function handleDelete() {
  if (!selectedContact.value) return
  if (!confirm(`'${selectedContact.value.name}' 연락처를 삭제하시겠습니까?`)) return
  await deleteContact(selectedContact.value.id)
}
</script>

<template>
  <div class="h-full overflow-y-auto">
    <!-- Empty state -->
    <div v-if="!selectedContact" class="h-full flex items-center justify-center text-muted-foreground text-sm">
      연락처를 선택하세요
    </div>

    <!-- Detail view -->
    <div v-else class="p-6 space-y-6">
      <!-- Header -->
      <div class="flex items-center gap-4">
        <div
          class="w-16 h-16 rounded-full flex items-center justify-center text-white text-2xl font-medium shrink-0"
          :style="{ backgroundColor: avatarColor(selectedContact) }"
        >
          {{ getInitials(selectedContact) }}
        </div>
        <div class="flex-1 min-w-0">
          <h2 class="text-xl font-semibold truncate">{{ selectedContact.name }}</h2>
          <p v-if="selectedContact.organization" class="text-sm text-muted-foreground">
            {{ selectedContact.organization }}
          </p>
        </div>
        <div class="flex gap-1 shrink-0">
          <button
            @click="openEditModal(selectedContact)"
            class="px-3 py-1.5 text-sm rounded-md hover:bg-accent transition-colors"
          >
            편집
          </button>
          <button
            @click="handleDelete"
            class="px-3 py-1.5 text-sm rounded-md hover:bg-accent text-destructive transition-colors"
          >
            삭제
          </button>
        </div>
      </div>

      <!-- Email -->
      <div v-if="selectedContact.emails.length > 0">
        <h3 class="text-sm font-medium text-muted-foreground mb-2">이메일</h3>
        <div class="space-y-1.5">
          <div v-for="(email, i) in selectedContact.emails" :key="i" class="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 text-muted-foreground shrink-0"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
            <a :href="`mailto:${email.value}`" class="text-sm text-primary hover:underline">{{ email.value }}</a>
            <span class="text-xs text-muted-foreground">({{ typeLabel(email.type) }})</span>
          </div>
        </div>
      </div>

      <!-- Phone -->
      <div v-if="selectedContact.phones.length > 0">
        <h3 class="text-sm font-medium text-muted-foreground mb-2">전화번호</h3>
        <div class="space-y-1.5">
          <div v-for="(phone, i) in selectedContact.phones" :key="i" class="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 text-muted-foreground shrink-0"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
            <a :href="`tel:${phone.value}`" class="text-sm text-primary hover:underline">{{ phone.value }}</a>
            <span class="text-xs text-muted-foreground">({{ typeLabel(phone.type) }})</span>
          </div>
        </div>
      </div>

      <!-- Address -->
      <div v-if="selectedContact.addresses.length > 0">
        <h3 class="text-sm font-medium text-muted-foreground mb-2">주소</h3>
        <div class="space-y-1.5">
          <div v-for="(addr, i) in selectedContact.addresses" :key="i" class="flex items-start gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 text-muted-foreground shrink-0 mt-0.5"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
            <div>
              <p class="text-sm">{{ addr.value }}</p>
              <span class="text-xs text-muted-foreground">({{ typeLabel(addr.type) }})</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Notes -->
      <div v-if="selectedContact.notes">
        <h3 class="text-sm font-medium text-muted-foreground mb-2">메모</h3>
        <p class="text-sm whitespace-pre-wrap">{{ selectedContact.notes }}</p>
      </div>
    </div>
  </div>
</template>

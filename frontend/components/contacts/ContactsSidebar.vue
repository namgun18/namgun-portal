<script setup lang="ts">
const {
  addressBooks, selectedBookId, loadingBooks,
  fetchAddressBooks, selectBook, createAddressBook, deleteAddressBook, openCreateModal,
} = useContacts()

const showNewForm = ref(false)
const newName = ref('')

onMounted(() => {
  if (addressBooks.value.length === 0) fetchAddressBooks()
})

async function handleCreate() {
  if (!newName.value.trim()) return
  try {
    await createAddressBook(newName.value.trim())
    newName.value = ''
    showNewForm.value = false
  } catch {}
}

async function handleDelete(id: string, name: string) {
  if (!confirm(`'${name}' 주소록을 삭제하시겠습니까?`)) return
  await deleteAddressBook(id)
}
</script>

<template>
  <div class="space-y-4">
    <button
      @click="openCreateModal()"
      class="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 text-sm font-medium transition-colors"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
      새 연락처
    </button>

    <div>
      <div class="flex items-center justify-between mb-2">
        <h3 class="text-sm font-medium">주소록</h3>
        <button @click="showNewForm = !showNewForm" class="p-1 rounded hover:bg-accent" title="주소록 추가">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        </button>
      </div>

      <div v-if="loadingBooks" class="text-sm text-muted-foreground">불러오는 중...</div>

      <div v-else class="space-y-0.5">
        <!-- All contacts -->
        <button
          @click="selectBook(null)"
          class="w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md transition-colors"
          :class="!selectedBookId ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50'"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          전체 연락처
        </button>

        <div
          v-for="book in addressBooks"
          :key="book.id"
          class="flex items-center group"
        >
          <button
            @click="selectBook(book.id)"
            class="flex-1 flex items-center gap-2 px-3 py-2 text-sm rounded-md transition-colors"
            :class="selectedBookId === book.id ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
            {{ book.name }}
          </button>
          <button
            @click="handleDelete(book.id, book.name)"
            class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-accent text-muted-foreground shrink-0"
            title="삭제"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
      </div>

      <!-- New address book form -->
      <div v-if="showNewForm" class="mt-2 p-2 border rounded-lg space-y-2 bg-muted/30">
        <input
          v-model="newName"
          type="text"
          placeholder="주소록 이름"
          class="w-full px-2 py-1.5 text-sm border rounded bg-background focus:outline-none focus:ring-1 focus:ring-primary/50"
          @keyup.enter="handleCreate"
        />
        <div class="flex gap-1">
          <button @click="handleCreate" class="px-2 py-1 text-xs rounded bg-primary text-primary-foreground hover:bg-primary/90">추가</button>
          <button @click="showNewForm = false" class="px-2 py-1 text-xs rounded hover:bg-accent">취소</button>
        </div>
      </div>
    </div>
  </div>
</template>

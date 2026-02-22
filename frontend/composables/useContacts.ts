export interface TypedValue {
  type: string
  value: string
}

export interface AddressBook {
  id: string
  name: string
}

export interface Contact {
  id: string
  address_book_id: string
  name: string
  first_name: string | null
  last_name: string | null
  organization: string | null
  emails: TypedValue[]
  phones: TypedValue[]
  addresses: TypedValue[]
  notes: string | null
  created: string | null
  updated: string | null
}

// Module-level singleton state
const addressBooks = ref<AddressBook[]>([])
const contacts = ref<Contact[]>([])
const totalContacts = ref(0)
const selectedContact = ref<Contact | null>(null)
const selectedBookId = ref<string | null>(null)
const searchQuery = ref('')
const currentPage = ref(0)
const limit = ref(50)
const loadingBooks = ref(false)
const loadingContacts = ref(false)
const showEditModal = ref(false)
const editingContact = ref<Contact | null>(null)

export function useContacts() {
  // ─── Computed ───

  const totalPages = computed(() => Math.ceil(totalContacts.value / limit.value))
  const hasNextPage = computed(() => currentPage.value < totalPages.value - 1)
  const hasPrevPage = computed(() => currentPage.value > 0)

  // ─── Actions ───

  async function fetchAddressBooks() {
    loadingBooks.value = true
    try {
      const data = await $fetch<{ address_books: AddressBook[] }>('/api/contacts/address-books')
      addressBooks.value = data.address_books
    } catch (e: any) {
      console.error('fetchAddressBooks error:', e)
    } finally {
      loadingBooks.value = false
    }
  }

  async function fetchContacts() {
    loadingContacts.value = true
    try {
      const params: Record<string, any> = {
        page: currentPage.value,
        limit: limit.value,
      }
      if (searchQuery.value.trim()) params.q = searchQuery.value.trim()
      if (selectedBookId.value) params.book_id = selectedBookId.value

      const data = await $fetch<{ contacts: Contact[]; total: number }>('/api/contacts/', { params })
      contacts.value = data.contacts
      totalContacts.value = data.total
    } catch (e: any) {
      console.error('fetchContacts error:', e)
      contacts.value = []
    } finally {
      loadingContacts.value = false
    }
  }

  function selectBook(id: string | null) {
    selectedBookId.value = id
    currentPage.value = 0
    selectedContact.value = null
    fetchContacts()
  }

  function setSearchQuery(q: string) {
    searchQuery.value = q
    currentPage.value = 0
    fetchContacts()
  }

  function selectContact(contact: Contact) {
    selectedContact.value = contact
  }

  async function createAddressBook(name: string) {
    try {
      await $fetch('/api/contacts/address-books', {
        method: 'POST',
        body: { name },
      })
      await fetchAddressBooks()
    } catch (e: any) {
      console.error('createAddressBook error:', e)
      throw e
    }
  }

  async function deleteAddressBook(id: string) {
    try {
      await $fetch(`/api/contacts/address-books/${id}`, { method: 'DELETE' })
      if (selectedBookId.value === id) selectedBookId.value = null
      await fetchAddressBooks()
      await fetchContacts()
    } catch (e: any) {
      console.error('deleteAddressBook error:', e)
    }
  }

  async function createContact(data: {
    address_book_id: string
    name: string
    first_name?: string
    last_name?: string
    organization?: string
    emails?: TypedValue[]
    phones?: TypedValue[]
    addresses?: TypedValue[]
    notes?: string
  }) {
    try {
      const result = await $fetch<Contact>('/api/contacts/', {
        method: 'POST',
        body: data,
      })
      await fetchContacts()
      return result
    } catch (e: any) {
      console.error('createContact error:', e)
      throw e
    }
  }

  async function updateContact(id: string, data: Record<string, any>) {
    try {
      await $fetch(`/api/contacts/${id}`, {
        method: 'PATCH',
        body: data,
      })
      await fetchContacts()
      if (selectedContact.value?.id === id) {
        // Refresh detail
        const updated = contacts.value.find(c => c.id === id)
        if (updated) selectedContact.value = updated
      }
    } catch (e: any) {
      console.error('updateContact error:', e)
      throw e
    }
  }

  async function deleteContact(id: string) {
    try {
      await $fetch(`/api/contacts/${id}`, { method: 'DELETE' })
      contacts.value = contacts.value.filter(c => c.id !== id)
      if (selectedContact.value?.id === id) selectedContact.value = null
    } catch (e: any) {
      console.error('deleteContact error:', e)
    }
  }

  function openCreateModal() {
    editingContact.value = null
    showEditModal.value = true
  }

  function openEditModal(contact: Contact) {
    editingContact.value = contact
    showEditModal.value = true
  }

  function closeModal() {
    showEditModal.value = false
    editingContact.value = null
  }

  async function nextPage() {
    if (hasNextPage.value) {
      currentPage.value++
      await fetchContacts()
    }
  }

  async function prevPage() {
    if (hasPrevPage.value) {
      currentPage.value--
      await fetchContacts()
    }
  }

  return {
    // State
    addressBooks: readonly(addressBooks),
    contacts: readonly(contacts),
    totalContacts: readonly(totalContacts),
    selectedContact,
    selectedBookId,
    searchQuery,
    currentPage: readonly(currentPage),
    loadingBooks: readonly(loadingBooks),
    loadingContacts: readonly(loadingContacts),
    showEditModal,
    editingContact: readonly(editingContact),
    // Computed
    totalPages,
    hasNextPage,
    hasPrevPage,
    // Actions
    fetchAddressBooks,
    fetchContacts,
    selectBook,
    setSearchQuery,
    selectContact,
    createAddressBook,
    deleteAddressBook,
    createContact,
    updateContact,
    deleteContact,
    openCreateModal,
    openEditModal,
    closeModal,
    nextPage,
    prevPage,
  }
}

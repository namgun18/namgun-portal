<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { fetchAddressBooks, fetchContacts } = useContacts()

onMounted(async () => {
  await fetchAddressBooks()
  await fetchContacts()
})
</script>

<template>
  <div class="h-full flex overflow-hidden">
    <!-- Sidebar -->
    <aside class="hidden lg:block w-56 shrink-0 border-r p-4 overflow-y-auto">
      <ContactsSidebar />
    </aside>

    <!-- Contact list -->
    <div class="w-72 sm:w-80 shrink-0 border-r">
      <ContactsList />
    </div>

    <!-- Detail -->
    <div class="flex-1 overflow-hidden">
      <ContactsDetail />
    </div>

    <!-- Edit modal -->
    <ContactsEditModal />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const open = ref(false)

function close() {
  open.value = false
}

// Close on outside click
function onClickOutside(e: Event) {
  open.value = false
}
</script>

<template>
  <div class="relative inline-block text-left" v-click-outside="onClickOutside">
    <div @click="open = !open">
      <slot name="trigger" />
    </div>
    <Transition
      enter-active-class="transition ease-out duration-100"
      enter-from-class="transform opacity-0 scale-95"
      enter-to-class="transform opacity-100 scale-100"
      leave-active-class="transition ease-in duration-75"
      leave-from-class="transform opacity-100 scale-100"
      leave-to-class="transform opacity-0 scale-95"
    >
      <div
        v-if="open"
        class="absolute right-0 z-50 mt-2 w-56 origin-top-right rounded-md border bg-card shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none"
        @click="close"
      >
        <div class="py-1">
          <slot name="content" />
        </div>
      </div>
    </Transition>
  </div>
</template>

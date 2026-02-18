<script setup lang="ts">
import { cn } from '~/lib/utils'

const props = defineProps<{
  src?: string | null
  alt?: string
  fallback?: string
}>()
</script>

<template>
  <div :class="cn('relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full', $attrs.class ?? '')">
    <img
      v-if="src"
      :src="src"
      :alt="alt ?? ''"
      class="aspect-square h-full w-full object-cover"
    />
    <div
      v-else
      class="flex h-full w-full items-center justify-center rounded-full bg-muted text-sm font-medium"
    >
      {{ fallback ?? '?' }}
    </div>
  </div>
</template>

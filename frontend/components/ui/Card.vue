<script setup lang="ts">
import { cn } from '~/lib/utils'
</script>

<template>
  <div :class="cn('rounded-lg border bg-card text-card-foreground shadow-sm hover:shadow-md transition-shadow duration-200', $attrs.class ?? '')">
    <slot />
  </div>
</template>

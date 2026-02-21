<script setup lang="ts">
import DOMPurify from 'dompurify'

const props = defineProps<{ content: string }>()

const rendered = ref('')

async function render() {
  if (!props.content) {
    rendered.value = ''
    return
  }
  try {
    const MarkdownIt = (await import('markdown-it')).default
    const md = new MarkdownIt({
      html: false,
      linkify: true,
      breaks: true,
    })
    rendered.value = DOMPurify.sanitize(md.render(props.content))
  } catch {
    rendered.value = DOMPurify.sanitize(props.content.replace(/\n/g, '<br>'))
  }
}

onMounted(render)
watch(() => props.content, render)
</script>

<template>
  <div
    v-if="rendered"
    class="prose prose-sm dark:prose-invert max-w-none
      prose-headings:border-b prose-headings:pb-2 prose-headings:mb-3
      prose-a:text-primary prose-code:text-sm
      prose-pre:bg-muted/50 prose-pre:border prose-pre:rounded-md
      prose-img:rounded-md prose-img:max-w-full"
    v-html="rendered"
  />
</template>

<script setup lang="ts">
import GitBreadcrumb from './GitBreadcrumb.vue'

const { fileContent, currentPath } = useGit()

const highlightedHtml = ref('')
const loading = ref(true)

const lineCount = computed(() => {
  if (!fileContent.value?.content) return 0
  return fileContent.value.content.split('\n').length
})

// File extension to shiki language mapping
const EXT_LANG: Record<string, string> = {
  ts: 'typescript', tsx: 'tsx', js: 'javascript', jsx: 'jsx',
  py: 'python', rs: 'rust', go: 'go', java: 'java',
  c: 'c', cpp: 'cpp', h: 'c', hpp: 'cpp',
  rb: 'ruby', php: 'php', swift: 'swift', kt: 'kotlin',
  cs: 'csharp', css: 'css', scss: 'scss', less: 'less',
  html: 'html', vue: 'vue', svelte: 'svelte',
  json: 'json', yaml: 'yaml', yml: 'yaml', toml: 'toml',
  xml: 'xml', sql: 'sql', sh: 'bash', bash: 'bash', zsh: 'bash',
  md: 'markdown', dockerfile: 'dockerfile',
  makefile: 'makefile', nginx: 'nginx',
  env: 'dotenv', ini: 'ini', conf: 'ini',
}

function detectLang(filename: string): string {
  const name = filename.toLowerCase()
  if (name === 'dockerfile') return 'dockerfile'
  if (name === 'makefile') return 'makefile'
  const ext = name.split('.').pop() || ''
  return EXT_LANG[ext] || 'text'
}

async function highlight() {
  if (!fileContent.value?.content) {
    highlightedHtml.value = ''
    loading.value = false
    return
  }

  loading.value = true
  try {
    const { codeToHtml } = await import('shiki')
    const lang = detectLang(fileContent.value.name)
    highlightedHtml.value = await codeToHtml(fileContent.value.content, {
      lang,
      themes: { light: 'github-light', dark: 'github-dark' },
    })
  } catch {
    highlightedHtml.value = ''
  } finally {
    loading.value = false
  }
}

onMounted(highlight)
watch(() => fileContent.value, highlight)
</script>

<template>
  <div class="flex-1 overflow-y-auto p-4">
    <!-- Breadcrumb -->
    <GitBreadcrumb />

    <div class="border rounded-md overflow-hidden mt-2">
      <!-- Header -->
      <div v-if="fileContent" class="flex items-center justify-between px-4 py-2.5 border-b bg-muted/30">
        <div class="flex items-center gap-2 text-sm">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" class="h-4 w-4 text-muted-foreground">
            <path fill="currentColor" d="M2 1.75C2 .784 2.784 0 3.75 0h6.586c.464 0 .909.184 1.237.513l2.914 2.914c.329.328.513.773.513 1.237v9.586A1.75 1.75 0 0 1 13.25 16h-9.5A1.75 1.75 0 0 1 2 14.25Zm1.75-.25a.25.25 0 0 0-.25.25v12.5c0 .138.112.25.25.25h9.5a.25.25 0 0 0 .25-.25V6h-2.75A1.75 1.75 0 0 1 9 4.25V1.5Zm6.75.062V4.25c0 .138.112.25.25.25h2.688l-.011-.013-2.914-2.914-.013-.011Z" />
          </svg>
          <span class="font-medium">{{ fileContent.name }}</span>
        </div>
        <div class="flex items-center gap-3 text-xs text-muted-foreground">
          <span>{{ lineCount }} lines</span>
          <span>{{ fileContent.size > 1024 ? `${(fileContent.size / 1024).toFixed(1)} KB` : `${fileContent.size} Bytes` }}</span>
        </div>
      </div>

      <!-- Content -->
      <div v-if="loading" class="flex items-center justify-center py-12">
        <div class="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>

      <div v-else-if="fileContent?.too_large" class="px-4 py-8 text-center text-sm text-muted-foreground">
        파일이 너무 큽니다 (1MB 초과). 직접 다운로드하세요.
      </div>

      <div v-else-if="!fileContent?.content" class="px-4 py-8 text-center text-sm text-muted-foreground">
        바이너리 파일이거나 내용이 없습니다.
      </div>

      <div
        v-else-if="highlightedHtml"
        class="overflow-x-auto text-[13px] leading-5 [&_pre]:!p-4 [&_pre]:!m-0 [&_pre]:!rounded-none [&_.shiki]:!bg-transparent"
        v-html="highlightedHtml"
      />

      <!-- Fallback plain text -->
      <pre
        v-else-if="fileContent?.content"
        class="p-4 overflow-x-auto text-[13px] leading-5 font-mono"
      >{{ fileContent.content }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
const {
  selectedEnv, fetchTopology, fetchAllResources,
  tfFiles, tfOutput, tfRunning, tfTemplates,
  fetchTfFiles, saveTfFiles, deleteTfFile, runTfCommand,
  fetchTfTemplates, loadTfTemplate,
} = useLab()

const activeFile = ref('main.tf')
const newFileName = ref('')
const showNewFile = ref(false)
const showTemplates = ref(false)
const dirty = ref(false)
const saving = ref(false)
const autoSaveTimer = ref<ReturnType<typeof setTimeout> | null>(null)

// Local editor content (not synced until save)
const editorContent = ref('')

// File tabs
const fileNames = computed(() => Object.keys(tfFiles.value).filter(f => f !== 'provider.tf').sort())
const providerExists = computed(() => 'provider.tf' in tfFiles.value)

function selectFile(name: string) {
  if (dirty.value) saveCurrentFile()
  activeFile.value = name
  editorContent.value = tfFiles.value[name] || ''
  dirty.value = false
}

function onEditorInput() {
  dirty.value = true
  // Auto-save after 2s of inactivity
  if (autoSaveTimer.value) clearTimeout(autoSaveTimer.value)
  autoSaveTimer.value = setTimeout(() => saveCurrentFile(), 2000)
}

async function saveCurrentFile() {
  if (!dirty.value) return
  saving.value = true
  try {
    await saveTfFiles({ [activeFile.value]: editorContent.value })
    dirty.value = false
  } catch { /* ignore */ }
  finally { saving.value = false }
}

async function handleCreateFile() {
  let name = newFileName.value.trim()
  if (!name) return
  if (!name.endsWith('.tf')) name += '.tf'
  if (name === 'provider.tf') return
  await saveTfFiles({ [name]: '' })
  await fetchTfFiles()
  selectFile(name)
  showNewFile.value = false
  newFileName.value = ''
}

async function handleDeleteFile(name: string) {
  if (!confirm(`"${name}" 파일을 삭제하시겠습니까?`)) return
  await deleteTfFile(name)
  if (activeFile.value === name) {
    activeFile.value = 'main.tf'
    editorContent.value = tfFiles.value['main.tf'] || ''
  }
}

async function handleInit() {
  await saveCurrentFile()
  await runTfCommand('init')
}

async function handlePlan() {
  await saveCurrentFile()
  await runTfCommand('plan')
}

async function handleApply() {
  await saveCurrentFile()
  const result = await runTfCommand('apply')
  if (result && result.exit_code === 0) {
    await fetchTfFiles()
  }
}

async function handleDestroy() {
  if (!confirm('모든 리소스를 삭제합니다. 계속하시겠습니까?')) return
  await runTfCommand('destroy')
}

async function handleLoadTemplate(id: string) {
  const code = await loadTfTemplate(id)
  if (code) {
    editorContent.value = code
    dirty.value = true
    showTemplates.value = false
    await saveCurrentFile()
  }
}

// Load files when env changes
watch(() => selectedEnv.value?.id, async (id) => {
  if (id) {
    await fetchTfFiles()
    await fetchTfTemplates()
    if (tfFiles.value['main.tf'] !== undefined) {
      selectFile('main.tf')
    }
  }
}, { immediate: true })

// Keyboard shortcut: Ctrl+S to save
function handleKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    saveCurrentFile()
  }
}
</script>

<template>
  <div class="flex flex-col h-full border rounded-lg bg-card overflow-hidden">
    <!-- Toolbar -->
    <div class="flex items-center gap-1 px-2 py-1.5 border-b bg-background/80 overflow-x-auto">
      <span class="text-xs font-semibold text-muted-foreground uppercase tracking-wider shrink-0 mr-1">Terraform</span>

      <button
        @click="handleInit"
        :disabled="tfRunning || selectedEnv?.status !== 'running'"
        class="px-2 py-1 text-xs font-medium rounded-md border hover:bg-accent transition-colors disabled:opacity-50 shrink-0"
      >
        Init
      </button>
      <button
        @click="handlePlan"
        :disabled="tfRunning || selectedEnv?.status !== 'running'"
        class="px-2 py-1 text-xs font-medium rounded-md border hover:bg-accent transition-colors disabled:opacity-50 shrink-0"
      >
        Plan
      </button>
      <button
        @click="handleApply"
        :disabled="tfRunning || selectedEnv?.status !== 'running'"
        class="px-2 py-1 text-xs font-medium rounded-md bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition-colors shrink-0"
      >
        Apply
      </button>
      <button
        @click="handleDestroy"
        :disabled="tfRunning || selectedEnv?.status !== 'running'"
        class="px-2 py-1 text-xs font-medium rounded-md border border-destructive text-destructive hover:bg-destructive hover:text-destructive-foreground disabled:opacity-50 transition-colors shrink-0"
      >
        Destroy
      </button>

      <div class="flex-1" />

      <!-- Template dropdown -->
      <div class="relative shrink-0">
        <button
          @click="showTemplates = !showTemplates"
          class="px-2 py-1 text-xs font-medium rounded-md border hover:bg-accent transition-colors"
        >
          템플릿
        </button>
        <div v-if="showTemplates" class="absolute right-0 top-full mt-1 z-20 bg-popover border rounded-md shadow-lg py-1 w-56">
          <div
            @click="showTemplates = false"
            class="fixed inset-0 z-[-1]"
          />
          <button
            v-for="t in tfTemplates"
            :key="t.id"
            @click="handleLoadTemplate(t.id)"
            class="w-full text-left px-3 py-1.5 text-xs hover:bg-accent transition-colors"
          >
            {{ t.label }}
          </button>
          <div v-if="tfTemplates.length === 0" class="px-3 py-1.5 text-xs text-muted-foreground">템플릿 없음</div>
        </div>
      </div>

      <!-- Save indicator -->
      <span v-if="dirty" class="text-xs text-yellow-500 shrink-0">수정됨</span>
      <span v-else-if="saving" class="text-xs text-muted-foreground shrink-0">저장 중...</span>
    </div>

    <!-- File tabs -->
    <div class="flex items-center gap-0.5 px-2 py-1 border-b bg-background/50 overflow-x-auto">
      <button
        v-for="name in fileNames"
        :key="name"
        @click="selectFile(name)"
        class="group flex items-center gap-1 px-2 py-1 text-xs rounded-md transition-colors shrink-0"
        :class="activeFile === name ? 'bg-accent text-accent-foreground font-medium' : 'text-muted-foreground hover:bg-accent/50'"
      >
        {{ name }}
        <span
          v-if="name !== 'main.tf'"
          @click.stop="handleDeleteFile(name)"
          class="hidden group-hover:inline-flex items-center justify-center w-3 h-3 rounded-full hover:bg-destructive/20 text-destructive"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="w-2 h-2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </span>
      </button>
      <!-- View provider.tf (read-only indicator) -->
      <button
        v-if="providerExists"
        @click="selectFile('provider.tf')"
        class="px-2 py-1 text-xs rounded-md transition-colors shrink-0"
        :class="activeFile === 'provider.tf' ? 'bg-accent text-accent-foreground font-medium' : 'text-muted-foreground/50 hover:text-muted-foreground hover:bg-accent/30'"
      >
        provider.tf
      </button>
      <!-- Add file -->
      <template v-if="!showNewFile">
        <button
          @click="showNewFile = true"
          class="px-1.5 py-1 text-xs text-muted-foreground hover:text-foreground rounded-md hover:bg-accent/50 transition-colors shrink-0"
        >+</button>
      </template>
      <form v-else @submit.prevent="handleCreateFile" class="flex items-center gap-1 shrink-0">
        <input
          v-model="newFileName"
          type="text"
          placeholder="filename.tf"
          class="w-28 px-2 py-0.5 text-xs rounded border bg-background focus:outline-none focus:ring-1 focus:ring-ring"
          autofocus
          @keydown.escape="showNewFile = false; newFileName = ''"
        />
        <button type="submit" class="text-xs text-green-500 hover:text-green-400">OK</button>
        <button type="button" @click="showNewFile = false; newFileName = ''" class="text-xs text-muted-foreground">X</button>
      </form>
    </div>

    <!-- Editor + Output split -->
    <div class="flex-1 flex flex-col min-h-0">
      <!-- Code editor -->
      <div class="flex-1 min-h-[120px] relative">
        <textarea
          v-model="editorContent"
          @input="onEditorInput"
          @keydown="handleKeydown"
          :readonly="activeFile === 'provider.tf'"
          class="absolute inset-0 w-full h-full px-3 py-2 text-xs font-mono leading-relaxed bg-[#1e1e2e] text-[#cdd6f4] resize-none focus:outline-none"
          :class="activeFile === 'provider.tf' ? 'opacity-60 cursor-not-allowed' : ''"
          spellcheck="false"
          wrap="off"
        />
        <div v-if="activeFile === 'provider.tf'" class="absolute top-2 right-2 text-xs px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-400">
          읽기 전용
        </div>
      </div>

      <!-- Output terminal -->
      <div class="border-t">
        <div class="flex items-center px-2 py-1 bg-background/80 border-b">
          <span class="text-xs font-semibold text-muted-foreground uppercase tracking-wider">출력</span>
          <div class="flex-1" />
          <span v-if="tfRunning" class="text-xs text-yellow-500 animate-pulse">실행 중...</span>
        </div>
        <pre class="h-[140px] overflow-auto px-3 py-2 text-xs font-mono leading-relaxed bg-[#1e1e2e] text-[#a6adc8] whitespace-pre-wrap">{{ tfOutput || '아직 실행된 명령이 없습니다.\n[Init] → [Plan] → [Apply] 순서로 실행하세요.' }}</pre>
      </div>
    </div>
  </div>
</template>

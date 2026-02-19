<script setup lang="ts">
const { user } = useAuth()
const { showCompose, composeMode, composeDefaults, sending, sendMessage } = useMail()

const toField = ref('')
const ccField = ref('')
const bccField = ref('')
const subjectField = ref('')
const bodyField = ref('')
const showCc = ref(false)
const showBcc = ref(false)
const error = ref('')

// Populate fields when defaults change
watch(composeDefaults, (defaults) => {
  if (!defaults) return
  toField.value = defaults.to.map(a => a.email).join(', ')
  ccField.value = defaults.cc.map(a => a.email).join(', ')
  subjectField.value = defaults.subject
  bodyField.value = defaults.body
  bccField.value = ''
  showCc.value = defaults.cc.length > 0
  showBcc.value = false
  error.value = ''
}, { immediate: true })

function parseAddresses(raw: string): { name: string | null; email: string }[] {
  if (!raw.trim()) return []
  return raw.split(',').map(s => s.trim()).filter(Boolean).map(email => ({
    name: null,
    email: email.replace(/.*<(.+)>.*/, '$1').trim(),
  }))
}

const modeLabel = computed(() => {
  switch (composeMode.value) {
    case 'reply': return '답장'
    case 'replyAll': return '전체 답장'
    case 'forward': return '전달'
    default: return '새 메일'
  }
})

async function handleSend() {
  const to = parseAddresses(toField.value)
  if (to.length === 0) {
    error.value = '받는사람을 입력해주세요.'
    return
  }
  error.value = ''

  try {
    await sendMessage({
      to,
      cc: parseAddresses(ccField.value),
      bcc: parseAddresses(bccField.value),
      subject: subjectField.value,
      text_body: bodyField.value,
      in_reply_to: composeDefaults.value?.in_reply_to || null,
      references: composeDefaults.value?.references || [],
    })
  } catch (e: any) {
    error.value = e?.data?.detail || '메일 발송에 실패했습니다.'
  }
}

function handleClose() {
  if (bodyField.value.trim() || subjectField.value.trim()) {
    if (!confirm('작성 중인 메일을 취소하시겠습니까?')) return
  }
  showCompose.value = false
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="showCompose"
      class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50"
      @click.self="handleClose"
    >
      <div class="bg-background w-full sm:max-w-2xl sm:mx-4 rounded-t-xl sm:rounded-lg shadow-xl flex flex-col max-h-[90vh]">
        <!-- Header -->
        <div class="flex items-center justify-between px-4 sm:px-6 py-3 border-b shrink-0">
          <h2 class="text-base font-semibold">{{ modeLabel }}</h2>
          <button
            @click="handleClose"
            class="h-8 w-8 flex items-center justify-center rounded-md hover:bg-accent"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <!-- Form -->
        <div class="flex-1 overflow-auto px-4 sm:px-6 py-3 space-y-3">
          <!-- From (readonly) -->
          <div class="flex items-center gap-2 text-sm">
            <label class="w-16 text-muted-foreground shrink-0">보내는사람</label>
            <span class="text-foreground">{{ user?.display_name || user?.username }} &lt;{{ user?.email }}&gt;</span>
          </div>

          <!-- To -->
          <div class="flex items-center gap-2 text-sm">
            <label class="w-16 text-muted-foreground shrink-0">받는사람</label>
            <input
              v-model="toField"
              type="text"
              placeholder="이메일 주소 (쉼표로 구분)"
              class="flex-1 px-2 py-1.5 text-sm bg-background border rounded-md focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <button
              v-if="!showCc"
              @click="showCc = true"
              class="text-xs text-muted-foreground hover:text-foreground shrink-0"
            >참조</button>
            <button
              v-if="!showBcc"
              @click="showBcc = true"
              class="text-xs text-muted-foreground hover:text-foreground shrink-0"
            >숨은참조</button>
          </div>

          <!-- CC -->
          <div v-if="showCc" class="flex items-center gap-2 text-sm">
            <label class="w-16 text-muted-foreground shrink-0">참조</label>
            <input
              v-model="ccField"
              type="text"
              placeholder="이메일 주소"
              class="flex-1 px-2 py-1.5 text-sm bg-background border rounded-md focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <!-- BCC -->
          <div v-if="showBcc" class="flex items-center gap-2 text-sm">
            <label class="w-16 text-muted-foreground shrink-0">숨은참조</label>
            <input
              v-model="bccField"
              type="text"
              placeholder="이메일 주소"
              class="flex-1 px-2 py-1.5 text-sm bg-background border rounded-md focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <!-- Subject -->
          <div class="flex items-center gap-2 text-sm">
            <label class="w-16 text-muted-foreground shrink-0">제목</label>
            <input
              v-model="subjectField"
              type="text"
              placeholder="제목"
              class="flex-1 px-2 py-1.5 text-sm bg-background border rounded-md focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <!-- Body -->
          <textarea
            v-model="bodyField"
            placeholder="내용을 입력하세요..."
            rows="12"
            class="w-full px-3 py-2 text-sm bg-background border rounded-md focus:outline-none focus:ring-1 focus:ring-primary resize-none"
          />

          <!-- Error -->
          <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-between px-4 sm:px-6 py-3 border-t shrink-0">
          <button
            @click="handleClose"
            class="px-4 py-2 text-sm rounded-md hover:bg-accent transition-colors"
          >
            취소
          </button>
          <button
            @click="handleSend"
            :disabled="sending"
            class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            <div v-if="sending" class="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
            <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
              <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
            보내기
          </button>
        </div>
        <div class="h-safe-area-inset-bottom sm:hidden" />
      </div>
    </div>
  </Teleport>
</template>

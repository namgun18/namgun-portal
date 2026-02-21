<script setup lang="ts">
import type { UploadedAttachment } from '~/composables/useMail'

const { user } = useAuth()
const { showCompose, composeMode, composeDefaults, sending, sendMessage, uploadAttachment } = useMail()
const { getDefaultSignature } = useMailSignature()

const toField = ref('')
const ccField = ref('')
const bccField = ref('')
const subjectField = ref('')
const bodyField = ref('')
const htmlBody = ref<string | null>(null)
const showCc = ref(false)
const showBcc = ref(false)
const error = ref('')
const attachments = ref<UploadedAttachment[]>([])
const uploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

// Populate fields when defaults change
watch(composeDefaults, async (defaults) => {
  if (!defaults) return
  toField.value = defaults.to.map(a => a.email).join(', ')
  ccField.value = defaults.cc.map(a => a.email).join(', ')
  subjectField.value = defaults.subject
  bodyField.value = defaults.body
  htmlBody.value = null
  bccField.value = ''
  showCc.value = defaults.cc.length > 0
  showBcc.value = false
  error.value = ''
  attachments.value = []

  // Auto-insert default signature for new messages
  if (composeMode.value === 'new') {
    try {
      const sig = await getDefaultSignature()
      if (sig) {
        const sigBlock = `\n\n--\n`
        bodyField.value = sigBlock
        htmlBody.value = `<p></p><div class="signature"><p>--</p>${sig.html_content}</div>`
      }
    } catch { /* ignore */ }
  }
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

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

async function handleFiles(files: FileList | null) {
  if (!files) return
  const totalSize = attachments.value.reduce((s, a) => s + a.size, 0)
  for (const file of Array.from(files)) {
    if (totalSize + file.size > 25 * 1024 * 1024) {
      error.value = '첨부파일 총 크기는 25MB를 초과할 수 없습니다.'
      return
    }
    uploading.value = true
    try {
      const uploaded = await uploadAttachment(file)
      attachments.value.push(uploaded)
    } catch (e: any) {
      error.value = e?.data?.detail || '파일 업로드에 실패했습니다.'
    } finally {
      uploading.value = false
    }
  }
}

function handleFileSelect() {
  fileInput.value?.click()
}

function removeAttachment(index: number) {
  attachments.value.splice(index, 1)
}

function handleDrop(e: DragEvent) {
  e.preventDefault()
  handleFiles(e.dataTransfer?.files || null)
}

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
      html_body: htmlBody.value,
      in_reply_to: composeDefaults.value?.in_reply_to || null,
      references: composeDefaults.value?.references || [],
      attachments: attachments.value.length > 0 ? attachments.value : undefined,
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
          <div @drop.prevent="handleDrop" @dragover.prevent>
            <MailEditor
              v-model:text="bodyField"
              v-model:html="htmlBody"
              :initial-content="composeDefaults?.body || ''"
            />
          </div>

          <!-- Attachments -->
          <div v-if="attachments.length > 0" class="space-y-1">
            <div
              v-for="(att, idx) in attachments"
              :key="att.blobId"
              class="flex items-center gap-2 px-2 py-1 bg-muted/50 rounded text-sm"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4 shrink-0 text-muted-foreground">
                <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48" />
              </svg>
              <span class="truncate flex-1">{{ att.name }}</span>
              <span class="text-xs text-muted-foreground shrink-0">{{ formatFileSize(att.size) }}</span>
              <button @click="removeAttachment(idx)" class="text-muted-foreground hover:text-destructive shrink-0">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-3.5 w-3.5">
                  <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Upload progress -->
          <div v-if="uploading" class="flex items-center gap-2 text-sm text-muted-foreground">
            <div class="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            파일 업로드 중...
          </div>

          <input ref="fileInput" type="file" multiple class="hidden" @change="handleFiles(($event.target as HTMLInputElement).files)" />

          <!-- Error -->
          <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-between px-4 sm:px-6 py-3 border-t shrink-0">
          <div class="flex items-center gap-1">
            <button
              @click="handleClose"
              class="px-4 py-2 text-sm rounded-md hover:bg-accent transition-colors"
            >
              취소
            </button>
            <button
              @click="handleFileSelect"
              :disabled="uploading"
              class="h-9 w-9 flex items-center justify-center rounded-md hover:bg-accent transition-colors text-muted-foreground hover:text-foreground"
              title="파일 첨부"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
                <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48" />
              </svg>
            </button>
          </div>
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

<script setup lang="ts">
import type { UploadedAttachment, ComposeMode, EmailAddress, MessageDetail } from '~/composables/useMail'
import type { Signature } from '~/composables/useMailSignature'

definePageMeta({ layout: false })

const route = useRoute()
const { user } = useAuth()
const { sendMessage, uploadAttachment } = useMail()
const { signatures, fetchSignatures, getDefaultSignature } = useMailSignature()

const mode = computed<ComposeMode>(() => (route.query.mode as ComposeMode) || 'new')
const msgId = computed(() => route.query.msgId as string | undefined)

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
const sending = ref(false)
const ready = ref(false)

// Signature
const selectedSignatureId = ref<string | null>(null)
const sigLoaded = ref(false)

const modeLabel = computed(() => {
  switch (mode.value) {
    case 'reply': return '답장'
    case 'replyAll': return '전체 답장'
    case 'forward': return '전달'
    default: return '새 메일'
  }
})

function parseAddresses(raw: string): EmailAddress[] {
  if (!raw.trim()) return []
  return raw.split(',').map(s => s.trim()).filter(Boolean).map(email => ({
    name: null,
    email: email.replace(/.*<(.+)>.*/, '$1').trim(),
  }))
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function buildQuoteBody(msg: MessageDetail): string {
  const from = msg.from_.map(a => a.name || a.email).join(', ')
  const date = msg.received_at ? new Date(msg.received_at).toLocaleString('ko-KR') : ''
  const body = msg.text_body || ''
  return `\n\n${date}, ${from}:\n> ${body.split('\n').join('\n> ')}`
}

function buildForwardBody(msg: MessageDetail): string {
  const from = msg.from_.map(a => `${a.name || ''} <${a.email}>`).join(', ')
  const to = msg.to.map(a => `${a.name || ''} <${a.email}>`).join(', ')
  const date = msg.received_at ? new Date(msg.received_at).toLocaleString('ko-KR') : ''
  const body = msg.text_body || ''
  return `\n\n---------- Forwarded message ----------\nFrom: ${from}\nDate: ${date}\nSubject: ${msg.subject || ''}\nTo: ${to}\n\n${body}`
}

async function loadOriginalMessage(): Promise<MessageDetail | null> {
  if (!msgId.value) return null
  try {
    return await $fetch<MessageDetail>(`/api/mail/messages/${msgId.value}`)
  } catch {
    return null
  }
}

function applySignature(sigId: string | null) {
  // Remove existing signature block from HTML
  if (htmlBody.value) {
    htmlBody.value = htmlBody.value.replace(/<div class="signature">[\s\S]*?<\/div>/, '')
  }
  // Remove from text
  const sigMarkerIdx = bodyField.value.indexOf('\n\n--\n')
  if (sigMarkerIdx >= 0) {
    bodyField.value = bodyField.value.substring(0, sigMarkerIdx)
  }

  if (!sigId) return

  const sig = signatures.value.find(s => s.id === sigId)
  if (!sig) return

  bodyField.value += '\n\n--\n'
  if (htmlBody.value) {
    htmlBody.value += `<div class="signature"><p>--</p>${sig.html_content}</div>`
  } else {
    htmlBody.value = `<div class="signature"><p>--</p>${sig.html_content}</div>`
  }
}

watch(selectedSignatureId, (newId) => {
  if (sigLoaded.value) {
    applySignature(newId)
  }
})

onMounted(async () => {
  // Load signatures
  await fetchSignatures()

  // Load original message for reply/forward
  const originalMsg = await loadOriginalMessage()

  if (mode.value === 'new' || !originalMsg) {
    // New message
  } else if (mode.value === 'reply') {
    const replyTo = originalMsg.reply_to.length > 0 ? originalMsg.reply_to : originalMsg.from_
    toField.value = replyTo.map(a => a.email).join(', ')
    subjectField.value = originalMsg.subject?.startsWith('Re:') ? originalMsg.subject : `Re: ${originalMsg.subject || ''}`
    bodyField.value = buildQuoteBody(originalMsg)
  } else if (mode.value === 'replyAll') {
    const replyTo = originalMsg.reply_to.length > 0 ? originalMsg.reply_to : originalMsg.from_
    toField.value = replyTo.map(a => a.email).join(', ')
    ccField.value = [...originalMsg.to, ...originalMsg.cc].map(a => a.email).join(', ')
    showCc.value = true
    subjectField.value = originalMsg.subject?.startsWith('Re:') ? originalMsg.subject : `Re: ${originalMsg.subject || ''}`
    bodyField.value = buildQuoteBody(originalMsg)
  } else if (mode.value === 'forward') {
    subjectField.value = originalMsg.subject?.startsWith('Fwd:') ? originalMsg.subject : `Fwd: ${originalMsg.subject || ''}`
    bodyField.value = buildForwardBody(originalMsg)
  }

  // Auto-insert default signature
  try {
    const defaultSig = await getDefaultSignature()
    if (defaultSig) {
      selectedSignatureId.value = defaultSig.id
      applySignature(defaultSig.id)
    }
  } catch { /* ignore */ }

  sigLoaded.value = true
  ready.value = true
})

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
  sending.value = true

  try {
    await sendMessage({
      to,
      cc: parseAddresses(ccField.value),
      bcc: parseAddresses(bccField.value),
      subject: subjectField.value,
      text_body: bodyField.value,
      html_body: htmlBody.value,
      in_reply_to: msgId.value || null,
      references: [],
      attachments: attachments.value.length > 0 ? attachments.value : undefined,
    })
    // Notify parent window to refresh
    if (window.opener) {
      window.opener.postMessage({ type: 'mail-sent' }, '*')
    }
    window.close()
  } catch (e: any) {
    error.value = e?.data?.detail || '메일 발송에 실패했습니다.'
  } finally {
    sending.value = false
  }
}

function handleClose() {
  if (bodyField.value.trim() || subjectField.value.trim()) {
    if (!confirm('작성 중인 메일을 취소하시겠습니까?')) return
  }
  window.close()
}
</script>

<template>
  <div class="h-screen flex flex-col bg-background text-foreground">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-2.5 border-b bg-background shrink-0">
      <h1 class="text-base font-semibold">{{ modeLabel }}</h1>
      <button
        @click="handleClose"
        class="h-8 w-8 flex items-center justify-center rounded-md hover:bg-accent"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
          <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>

    <!-- Loading -->
    <div v-if="!ready" class="flex-1 flex items-center justify-center">
      <div class="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
    </div>

    <!-- Form -->
    <div v-else class="flex-1 overflow-auto px-4 py-3 space-y-3">
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
          :initial-content="bodyField"
        />
      </div>

      <!-- Signature selector -->
      <div class="flex items-center gap-2 text-sm">
        <label class="w-16 text-muted-foreground shrink-0">서명</label>
        <select
          v-model="selectedSignatureId"
          class="flex-1 px-2 py-1.5 text-sm bg-background border rounded-md focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option :value="null">서명 없음</option>
          <option v-for="sig in signatures" :key="sig.id" :value="sig.id">
            {{ sig.name }}{{ sig.is_default ? ' (기본)' : '' }}
          </option>
        </select>
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
    <div class="flex items-center justify-between px-4 py-2.5 border-t shrink-0">
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
  </div>
</template>

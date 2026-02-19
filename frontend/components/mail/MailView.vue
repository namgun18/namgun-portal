<script setup lang="ts">
let DOMPurify: any = null
if (import.meta.client) {
  import('dompurify').then(m => { DOMPurify = m.default })
}

const {
  selectedMessage,
  loadingMessage,
  clearSelectedMessage,
  toggleStar,
  deleteMessage,
  openCompose,
  downloadAttachment,
  mailboxes,
} = useMail()

function formatDate(dateStr: string | null): string {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatAddr(addr: any): string {
  if (addr.name) return `${addr.name} <${addr.email}>`
  return addr.email
}

function formatAddrs(addrs: any[]): string {
  return addrs.map(formatAddr).join(', ')
}

function formatSize(bytes: number): string {
  if (!bytes) return ''
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0) + ' ' + units[i]
}

function getInitial(msg: any): string {
  if (!msg.from_ || msg.from_.length === 0) return '?'
  const name = msg.from_[0].name || msg.from_[0].email
  return name.charAt(0).toUpperCase()
}

const sanitizedHtml = computed(() => {
  if (!selectedMessage.value?.html_body) return ''
  if (!DOMPurify) return selectedMessage.value.html_body
  return DOMPurify.sanitize(selectedMessage.value.html_body, {
    ALLOW_TAGS: [
      'a', 'b', 'i', 'u', 'em', 'strong', 'p', 'br', 'div', 'span',
      'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'table', 'thead', 'tbody', 'tr', 'td', 'th',
      'blockquote', 'pre', 'code', 'hr', 'img', 'sub', 'sup',
    ],
    ALLOW_ATTR: ['href', 'src', 'alt', 'style', 'class', 'target', 'width', 'height'],
    ADD_ATTR: ['target'],
  })
})

function handleDelete() {
  if (!selectedMessage.value) return
  if (!confirm('이 메일을 삭제하시겠습니까?')) return
  deleteMessage(selectedMessage.value.id)
}

function handleReply() {
  openCompose('reply', selectedMessage.value)
}

function handleReplyAll() {
  openCompose('replyAll', selectedMessage.value)
}

function handleForward() {
  openCompose('forward', selectedMessage.value)
}
</script>

<template>
  <!-- Desktop: right panel -->
  <div
    class="hidden md:flex flex-col border-l bg-background overflow-hidden"
    :class="selectedMessage ? 'flex-1' : 'w-0'"
  >
    <template v-if="loadingMessage">
      <div class="flex-1 p-6 space-y-4">
        <div class="h-8 w-2/3 bg-muted/50 rounded animate-pulse" />
        <div class="h-4 w-1/2 bg-muted/50 rounded animate-pulse" />
        <div class="h-64 bg-muted/50 rounded animate-pulse mt-4" />
      </div>
    </template>

    <template v-else-if="selectedMessage">
      <!-- Header -->
      <div class="flex items-center gap-2 px-4 py-2 border-b shrink-0">
        <button
          @click="clearSelectedMessage"
          class="h-8 w-8 flex items-center justify-center rounded-md hover:bg-accent transition-colors"
          title="닫기"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
        <div class="flex-1" />
        <!-- Action buttons -->
        <button @click="handleReply" class="h-8 w-8 flex items-center justify-center rounded-md hover:bg-accent transition-colors" title="답장">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
            <polyline points="9 17 4 12 9 7" /><path d="M20 18v-2a4 4 0 0 0-4-4H4" />
          </svg>
        </button>
        <button @click="handleReplyAll" class="h-8 w-8 flex items-center justify-center rounded-md hover:bg-accent transition-colors" title="전체 답장">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
            <polyline points="7 17 2 12 7 7" /><polyline points="12 17 7 12 12 7" /><path d="M22 18v-2a4 4 0 0 0-4-4H7" />
          </svg>
        </button>
        <button @click="handleForward" class="h-8 w-8 flex items-center justify-center rounded-md hover:bg-accent transition-colors" title="전달">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
            <polyline points="15 17 20 12 15 7" /><path d="M4 18v-2a4 4 0 0 1 4-4h12" />
          </svg>
        </button>
        <button
          @click="() => selectedMessage && toggleStar(selectedMessage.id)"
          class="h-8 w-8 flex items-center justify-center rounded-md hover:bg-accent transition-colors"
          title="별표"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
            :fill="selectedMessage.is_flagged ? 'currentColor' : 'none'"
            stroke="currentColor" stroke-width="2"
            class="h-4 w-4"
            :class="selectedMessage.is_flagged ? 'text-yellow-500' : 'text-muted-foreground'"
          >
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
          </svg>
        </button>
        <button
          @click="handleDelete"
          class="h-8 w-8 flex items-center justify-center rounded-md hover:bg-destructive/10 text-destructive transition-colors"
          title="삭제"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
            <polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
        </button>
      </div>

      <!-- Body scroll area -->
      <div class="flex-1 overflow-auto">
        <!-- Subject + sender -->
        <div class="px-6 pt-5 pb-4">
          <h2 class="text-lg font-semibold mb-4">{{ selectedMessage.subject || '(제목 없음)' }}</h2>
          <div class="flex items-start gap-3">
            <!-- Avatar -->
            <div class="h-10 w-10 rounded-full bg-primary/10 text-primary flex items-center justify-center shrink-0 text-sm font-semibold">
              {{ getInitial(selectedMessage) }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-baseline gap-2">
                <span class="text-sm font-medium">
                  {{ selectedMessage.from_?.[0]?.name || selectedMessage.from_?.[0]?.email || '(발신자 없음)' }}
                </span>
                <span class="text-xs text-muted-foreground truncate">
                  &lt;{{ selectedMessage.from_?.[0]?.email }}&gt;
                </span>
              </div>
              <div class="text-xs text-muted-foreground mt-0.5">
                받는사람: {{ formatAddrs(selectedMessage.to) }}
              </div>
              <div v-if="selectedMessage.cc.length > 0" class="text-xs text-muted-foreground">
                참조: {{ formatAddrs(selectedMessage.cc) }}
              </div>
              <div class="text-xs text-muted-foreground mt-0.5">
                {{ formatDate(selectedMessage.received_at) }}
              </div>
            </div>
          </div>
        </div>

        <!-- Divider -->
        <div class="mx-6 border-t" />

        <!-- Body content -->
        <div class="px-6 py-4">
          <div
            v-if="sanitizedHtml"
            class="prose prose-sm dark:prose-invert max-w-none break-words [&_img]:max-w-full [&_a]:text-primary"
            v-html="sanitizedHtml"
          />
          <pre
            v-else-if="selectedMessage.text_body"
            class="text-sm whitespace-pre-wrap font-sans text-foreground"
          >{{ selectedMessage.text_body }}</pre>
          <p v-else class="text-sm text-muted-foreground italic">본문 없음</p>
        </div>

        <!-- Attachments -->
        <div v-if="selectedMessage.attachments.length > 0" class="px-6 pb-4">
          <div class="border rounded-lg p-3">
            <h4 class="text-xs font-medium text-muted-foreground mb-2">
              첨부파일 ({{ selectedMessage.attachments.length }})
            </h4>
            <div class="space-y-1.5">
              <button
                v-for="att in selectedMessage.attachments"
                :key="att.blob_id"
                @click="downloadAttachment(att.blob_id, att.name || 'attachment')"
                class="w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-accent transition-colors text-left"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 shrink-0 text-muted-foreground">
                  <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48" />
                </svg>
                <span class="truncate">{{ att.name || 'attachment' }}</span>
                <span class="text-xs text-muted-foreground shrink-0 ml-auto">{{ formatSize(att.size) }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- No selection -->
    <template v-else>
      <!-- Empty - takes no width due to w-0 class -->
    </template>
  </div>

  <!-- Mobile: full screen overlay -->
  <Teleport to="body">
    <div v-if="selectedMessage" class="md:hidden fixed inset-0 z-50 bg-background flex flex-col">
      <!-- Mobile header -->
      <div class="flex items-center gap-2 px-3 py-2 border-b shrink-0">
        <button
          @click="clearSelectedMessage"
          class="h-8 w-8 flex items-center justify-center rounded-md hover:bg-accent"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
        <div class="flex-1" />
        <button @click="handleReply" class="h-8 w-8 flex items-center justify-center rounded-md hover:bg-accent" title="답장">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
            <polyline points="9 17 4 12 9 7" /><path d="M20 18v-2a4 4 0 0 0-4-4H4" />
          </svg>
        </button>
        <button @click="handleForward" class="h-8 w-8 flex items-center justify-center rounded-md hover:bg-accent" title="전달">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
            <polyline points="15 17 20 12 15 7" /><path d="M4 18v-2a4 4 0 0 1 4-4h12" />
          </svg>
        </button>
        <button @click="handleDelete" class="h-8 w-8 flex items-center justify-center rounded-md hover:bg-destructive/10 text-destructive" title="삭제">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
            <polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
        </button>
      </div>

      <!-- Mobile body -->
      <div class="flex-1 overflow-auto">
        <div class="px-4 pt-4 pb-3">
          <h2 class="text-base font-semibold mb-3">{{ selectedMessage.subject || '(제목 없음)' }}</h2>
          <div class="flex items-start gap-3">
            <div class="h-9 w-9 rounded-full bg-primary/10 text-primary flex items-center justify-center shrink-0 text-sm font-semibold">
              {{ getInitial(selectedMessage) }}
            </div>
            <div class="flex-1 min-w-0">
              <span class="text-sm font-medium">
                {{ selectedMessage.from_?.[0]?.name || selectedMessage.from_?.[0]?.email }}
              </span>
              <div class="text-xs text-muted-foreground">
                받는사람: {{ formatAddrs(selectedMessage.to) }}
              </div>
              <div class="text-xs text-muted-foreground">
                {{ formatDate(selectedMessage.received_at) }}
              </div>
            </div>
          </div>
        </div>
        <div class="mx-4 border-t" />
        <div class="px-4 py-3">
          <div
            v-if="sanitizedHtml"
            class="prose prose-sm dark:prose-invert max-w-none break-words [&_img]:max-w-full"
            v-html="sanitizedHtml"
          />
          <pre
            v-else-if="selectedMessage.text_body"
            class="text-sm whitespace-pre-wrap font-sans"
          >{{ selectedMessage.text_body }}</pre>
        </div>
        <div v-if="selectedMessage.attachments.length > 0" class="px-4 pb-4">
          <div class="border rounded-lg p-3">
            <h4 class="text-xs font-medium text-muted-foreground mb-2">첨부파일</h4>
            <div class="space-y-1.5">
              <button
                v-for="att in selectedMessage.attachments"
                :key="att.blob_id"
                @click="downloadAttachment(att.blob_id, att.name || 'attachment')"
                class="w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-accent text-left"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4 shrink-0 text-muted-foreground">
                  <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48" />
                </svg>
                <span class="truncate">{{ att.name || 'attachment' }}</span>
                <span class="text-xs text-muted-foreground shrink-0 ml-auto">{{ formatSize(att.size) }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

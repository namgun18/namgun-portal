export interface EmailAddress {
  name: string | null
  email: string
}

export interface Mailbox {
  id: string
  name: string
  role: string | null
  unread_count: number
  total_count: number
  sort_order: number
}

export interface MessageSummary {
  id: string
  thread_id: string | null
  mailbox_ids: string[]
  from_: EmailAddress[]
  to: EmailAddress[]
  subject: string | null
  preview: string | null
  received_at: string | null
  is_unread: boolean
  is_flagged: boolean
  has_attachment: boolean
}

export interface Attachment {
  blob_id: string
  name: string | null
  type: string | null
  size: number
}

export interface MessageDetail {
  id: string
  thread_id: string | null
  mailbox_ids: string[]
  from_: EmailAddress[]
  to: EmailAddress[]
  cc: EmailAddress[]
  bcc: EmailAddress[]
  reply_to: EmailAddress[]
  subject: string | null
  text_body: string | null
  html_body: string | null
  preview: string | null
  received_at: string | null
  is_unread: boolean
  is_flagged: boolean
  attachments: Attachment[]
}

export interface UploadedAttachment {
  blobId: string
  type: string
  name: string
  size: number
}

export type ComposeMode = 'new' | 'reply' | 'replyAll' | 'forward'

export interface ComposeDefaults {
  to: EmailAddress[]
  cc: EmailAddress[]
  subject: string
  body: string
  in_reply_to: string | null
  references: string[]
}

// Module-level singleton state
const mailboxes = ref<Mailbox[]>([])
const selectedMailboxId = ref<string | null>(null)
const messages = ref<MessageSummary[]>([])
const selectedMessage = ref<MessageDetail | null>(null)
const currentPage = ref(0)
const totalMessages = ref(0)
const limit = ref(50)
const loadingMailboxes = ref(false)
const loadingMessages = ref(false)
const loadingMessage = ref(false)
const showCompose = ref(false)
const composeMode = ref<ComposeMode>('new')
const composeDefaults = ref<ComposeDefaults | null>(null)
const sending = ref(false)
const searchQuery = ref('')
const selectedIds = ref<Set<string>>(new Set())

export function useMail() {
  // ─── Computed ───

  const totalPages = computed(() => Math.ceil(totalMessages.value / limit.value))
  const hasNextPage = computed(() => currentPage.value < totalPages.value - 1)
  const hasPrevPage = computed(() => currentPage.value > 0)

  const totalUnread = computed(() =>
    mailboxes.value
      .filter(m => m.role === 'inbox')
      .reduce((sum, m) => sum + m.unread_count, 0)
  )

  const selectedMailbox = computed(() =>
    mailboxes.value.find(m => m.id === selectedMailboxId.value) || null
  )

  // ─── Actions ───

  async function fetchMailboxes() {
    loadingMailboxes.value = true
    try {
      const data = await $fetch<{ mailboxes: Mailbox[] }>('/api/mail/mailboxes')
      mailboxes.value = data.mailboxes
      // Auto-select inbox if nothing selected
      if (!selectedMailboxId.value) {
        const inbox = data.mailboxes.find(m => m.role === 'inbox')
        if (inbox) {
          selectedMailboxId.value = inbox.id
        } else if (data.mailboxes.length > 0) {
          selectedMailboxId.value = data.mailboxes[0].id
        }
      }
    } catch (e: any) {
      console.error('fetchMailboxes error:', e)
    } finally {
      loadingMailboxes.value = false
    }
  }

  async function selectMailbox(id: string) {
    selectedMailboxId.value = id
    selectedMessage.value = null
    selectedIds.value = new Set()
    currentPage.value = 0
    searchQuery.value = ''
    await fetchMessages()
  }

  async function fetchMessages() {
    if (!selectedMailboxId.value) return
    loadingMessages.value = true
    try {
      const params: Record<string, any> = {
        mailbox_id: selectedMailboxId.value,
        page: currentPage.value,
        limit: limit.value,
      }
      if (searchQuery.value.trim()) {
        params.q = searchQuery.value.trim()
      }
      const data = await $fetch<{
        messages: MessageSummary[]
        total: number
        page: number
        limit: number
      }>('/api/mail/messages', { params })
      messages.value = data.messages
      totalMessages.value = data.total
    } catch (e: any) {
      console.error('fetchMessages error:', e)
      messages.value = []
    } finally {
      loadingMessages.value = false
    }
  }

  function setSearchQuery(q: string) {
    searchQuery.value = q
    currentPage.value = 0
    fetchMessages()
  }

  async function openMessage(id: string) {
    loadingMessage.value = true
    try {
      selectedMessage.value = await $fetch<MessageDetail>(`/api/mail/messages/${id}`)
      // Update unread status in list
      const msg = messages.value.find(m => m.id === id)
      if (msg && msg.is_unread) {
        msg.is_unread = false
        // Update mailbox unread count
        const mb = mailboxes.value.find(m => m.id === selectedMailboxId.value)
        if (mb && mb.unread_count > 0) mb.unread_count--
      }
    } catch (e: any) {
      console.error('openMessage error:', e)
    } finally {
      loadingMessage.value = false
    }
  }

  async function toggleRead(id: string) {
    const msg = messages.value.find(m => m.id === id)
    if (!msg) return
    const newUnread = !msg.is_unread
    try {
      await $fetch(`/api/mail/messages/${id}`, {
        method: 'PATCH',
        body: { is_unread: newUnread },
      })
      msg.is_unread = newUnread
      const mb = mailboxes.value.find(m => m.id === selectedMailboxId.value)
      if (mb) mb.unread_count += newUnread ? 1 : -1
    } catch (e: any) {
      console.error('toggleRead error:', e)
    }
  }

  async function toggleStar(id: string) {
    const msg = messages.value.find(m => m.id === id)
    if (!msg) return
    const newFlagged = !msg.is_flagged
    try {
      await $fetch(`/api/mail/messages/${id}`, {
        method: 'PATCH',
        body: { is_flagged: newFlagged },
      })
      msg.is_flagged = newFlagged
      if (selectedMessage.value?.id === id) {
        selectedMessage.value.is_flagged = newFlagged
      }
    } catch (e: any) {
      console.error('toggleStar error:', e)
    }
  }

  async function deleteMessage(id: string) {
    try {
      await $fetch(`/api/mail/messages/${id}`, { method: 'DELETE' })
      messages.value = messages.value.filter(m => m.id !== id)
      if (selectedMessage.value?.id === id) {
        selectedMessage.value = null
      }
      // Refresh mailboxes for count update
      await fetchMailboxes()
    } catch (e: any) {
      console.error('deleteMessage error:', e)
    }
  }

  async function moveMessage(id: string, mailboxId: string) {
    try {
      await $fetch(`/api/mail/messages/${id}`, {
        method: 'PATCH',
        body: { mailbox_ids: [mailboxId] },
      })
      messages.value = messages.value.filter(m => m.id !== id)
      if (selectedMessage.value?.id === id) {
        selectedMessage.value = null
      }
      await fetchMailboxes()
    } catch (e: any) {
      console.error('moveMessage error:', e)
    }
  }

  async function uploadAttachment(file: File): Promise<UploadedAttachment> {
    const formData = new FormData()
    formData.append('file', file)
    return await $fetch<UploadedAttachment>('/api/mail/upload', {
      method: 'POST',
      body: formData,
    })
  }

  async function sendMessage(data: {
    to: EmailAddress[]
    cc: EmailAddress[]
    bcc: EmailAddress[]
    subject: string
    text_body: string
    html_body?: string | null
    in_reply_to?: string | null
    references?: string[]
    attachments?: UploadedAttachment[]
  }) {
    sending.value = true
    try {
      await $fetch('/api/mail/send', {
        method: 'POST',
        body: data,
      })
      showCompose.value = false
      composeDefaults.value = null
      // Refresh if in sent folder
      await fetchMessages()
      await fetchMailboxes()
    } catch (e: any) {
      console.error('sendMessage error:', e)
      throw e
    } finally {
      sending.value = false
    }
  }

  function toggleSelect(id: string) {
    const s = new Set(selectedIds.value)
    if (s.has(id)) s.delete(id)
    else s.add(id)
    selectedIds.value = s
  }

  function selectAll() {
    selectedIds.value = new Set(messages.value.map(m => m.id))
  }

  function deselectAll() {
    selectedIds.value = new Set()
  }

  async function bulkAction(action: string, mailboxId?: string) {
    const ids = Array.from(selectedIds.value)
    if (ids.length === 0) return
    try {
      await $fetch('/api/mail/bulk', {
        method: 'POST',
        body: { message_ids: ids, action, mailbox_id: mailboxId || null },
      })
      selectedIds.value = new Set()
      await Promise.all([fetchMessages(), fetchMailboxes()])
    } catch (e: any) {
      console.error('bulkAction error:', e)
    }
  }

  function openCompose(mode: ComposeMode = 'new', msg?: MessageDetail | null) {
    composeMode.value = mode
    if (mode === 'new' || !msg) {
      composeDefaults.value = { to: [], cc: [], subject: '', body: '', in_reply_to: null, references: [] }
    } else if (mode === 'reply') {
      const replyTo = msg.reply_to.length > 0 ? msg.reply_to : msg.from_
      composeDefaults.value = {
        to: replyTo,
        cc: [],
        subject: msg.subject?.startsWith('Re:') ? msg.subject : `Re: ${msg.subject || ''}`,
        body: _buildQuoteBody(msg),
        in_reply_to: msg.id,
        references: [],
      }
    } else if (mode === 'replyAll') {
      const replyTo = msg.reply_to.length > 0 ? msg.reply_to : msg.from_
      composeDefaults.value = {
        to: replyTo,
        cc: [...msg.to, ...msg.cc],
        subject: msg.subject?.startsWith('Re:') ? msg.subject : `Re: ${msg.subject || ''}`,
        body: _buildQuoteBody(msg),
        in_reply_to: msg.id,
        references: [],
      }
    } else if (mode === 'forward') {
      composeDefaults.value = {
        to: [],
        cc: [],
        subject: msg.subject?.startsWith('Fwd:') ? msg.subject : `Fwd: ${msg.subject || ''}`,
        body: _buildForwardBody(msg),
        in_reply_to: null,
        references: [],
      }
    }
    showCompose.value = true
  }

  function _buildQuoteBody(msg: MessageDetail): string {
    const from = msg.from_.map(a => a.name || a.email).join(', ')
    const date = msg.received_at ? new Date(msg.received_at).toLocaleString('ko-KR') : ''
    const body = msg.text_body || ''
    return `\n\n${date}, ${from}:\n> ${body.split('\n').join('\n> ')}`
  }

  function _buildForwardBody(msg: MessageDetail): string {
    const from = msg.from_.map(a => `${a.name || ''} <${a.email}>`).join(', ')
    const to = msg.to.map(a => `${a.name || ''} <${a.email}>`).join(', ')
    const date = msg.received_at ? new Date(msg.received_at).toLocaleString('ko-KR') : ''
    const body = msg.text_body || ''
    return `\n\n---------- Forwarded message ----------\nFrom: ${from}\nDate: ${date}\nSubject: ${msg.subject || ''}\nTo: ${to}\n\n${body}`
  }

  function clearSelectedMessage() {
    selectedMessage.value = null
  }

  async function nextPage() {
    if (hasNextPage.value) {
      currentPage.value++
      await fetchMessages()
    }
  }

  async function prevPage() {
    if (hasPrevPage.value) {
      currentPage.value--
      await fetchMessages()
    }
  }

  function downloadAttachment(blobId: string, name: string) {
    const url = `/api/mail/blob/${encodeURIComponent(blobId)}?name=${encodeURIComponent(name)}`
    window.open(url, '_blank')
  }

  async function refresh() {
    await Promise.all([fetchMailboxes(), fetchMessages()])
  }

  return {
    // State (readonly)
    mailboxes: readonly(mailboxes),
    selectedMailboxId: readonly(selectedMailboxId),
    messages: readonly(messages),
    selectedMessage: readonly(selectedMessage),
    currentPage: readonly(currentPage),
    totalMessages: readonly(totalMessages),
    limit: readonly(limit),
    loadingMailboxes: readonly(loadingMailboxes),
    loadingMessages: readonly(loadingMessages),
    loadingMessage: readonly(loadingMessage),
    showCompose,
    composeMode: readonly(composeMode),
    composeDefaults: readonly(composeDefaults),
    sending: readonly(sending),
    searchQuery,
    selectedIds,
    // Computed
    totalPages,
    hasNextPage,
    hasPrevPage,
    totalUnread,
    selectedMailbox,
    // Actions
    fetchMailboxes,
    selectMailbox,
    fetchMessages,
    openMessage,
    toggleRead,
    toggleStar,
    deleteMessage,
    moveMessage,
    sendMessage,
    uploadAttachment,
    toggleSelect,
    selectAll,
    deselectAll,
    bulkAction,
    openCompose,
    clearSelectedMessage,
    nextPage,
    prevPage,
    setSearchQuery,
    downloadAttachment,
    refresh,
  }
}

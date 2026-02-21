export interface Signature {
  id: string
  name: string
  html_content: string
  is_default: boolean
  created_at: string
}

const signatures = ref<Signature[]>([])
const loading = ref(false)

export function useMailSignature() {
  async function fetchSignatures() {
    loading.value = true
    try {
      signatures.value = await $fetch<Signature[]>('/api/mail/signatures')
    } catch (e: any) {
      console.error('fetchSignatures error:', e)
    } finally {
      loading.value = false
    }
  }

  async function getDefaultSignature(): Promise<Signature | null> {
    try {
      return await $fetch<Signature | null>('/api/mail/signatures/default')
    } catch {
      return null
    }
  }

  async function createSignature(data: {
    name: string
    html_content: string
    is_default?: boolean
  }): Promise<Signature> {
    const sig = await $fetch<Signature>('/api/mail/signatures', {
      method: 'POST',
      body: data,
    })
    await fetchSignatures()
    return sig
  }

  async function updateSignature(
    id: string,
    data: { name?: string; html_content?: string; is_default?: boolean }
  ): Promise<Signature> {
    const sig = await $fetch<Signature>(`/api/mail/signatures/${id}`, {
      method: 'PATCH',
      body: data,
    })
    await fetchSignatures()
    return sig
  }

  async function deleteSignature(id: string) {
    await $fetch(`/api/mail/signatures/${id}`, { method: 'DELETE' })
    await fetchSignatures()
  }

  return {
    signatures: readonly(signatures),
    loading: readonly(loading),
    fetchSignatures,
    getDefaultSignature,
    createSignature,
    updateSignature,
    deleteSignature,
  }
}

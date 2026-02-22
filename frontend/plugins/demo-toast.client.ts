/**
 * Demo mode toast plugin.
 * Shows a toast notification when write operations are attempted in demo mode.
 * Uses ofetch interceptors (via $fetch.create) to preserve $fetch.raw/.create/.native.
 */
export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig()
  if (!config.public.demoMode) return

  // Simple toast implementation
  let toastEl: HTMLDivElement | null = null
  let toastTimer: ReturnType<typeof setTimeout> | null = null

  function showDemoToast() {
    if (toastEl) {
      if (toastTimer) clearTimeout(toastTimer)
    } else {
      toastEl = document.createElement('div')
      toastEl.innerHTML = `
        <div style="
          position: fixed; bottom: 24px; right: 24px; z-index: 9999;
          background: #1e293b; color: #f8fafc; padding: 12px 20px;
          border-radius: 8px; font-size: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
          display: flex; align-items: center; gap: 8px;
          animation: demoSlideIn 0.3s ease;
        ">
          <span style="font-size: 18px;">&#x1F512;</span>
          <span>데모 모드에서는 변경할 수 없습니다</span>
        </div>
        <style>
          @keyframes demoSlideIn { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        </style>
      `
      document.body.appendChild(toastEl)
    }

    toastTimer = setTimeout(() => {
      if (toastEl) {
        toastEl.remove()
        toastEl = null
      }
    }, 3000)
  }

  // Use $fetch.create() to preserve all ofetch properties (.raw, .create, .native)
  const original = globalThis.$fetch
  globalThis.$fetch = original.create({
    onResponseError({ response }) {
      if (response.status === 403) {
        const detail = (response._data as any)?.detail
        if (typeof detail === 'string' && detail.includes('데모')) {
          showDemoToast()
        }
      }
    },
  }) as typeof original
})

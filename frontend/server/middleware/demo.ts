/**
 * Demo mode Nitro server middleware.
 * Intercepts /api/* requests when NUXT_PUBLIC_DEMO_MODE=true.
 * - GET: returns mock data
 * - POST/PATCH/DELETE: returns 403 "데모 모드입니다"
 */
import { getMockResponse } from '~/demo/mockData'

export default defineEventHandler((event) => {
  const config = useRuntimeConfig()
  if (!config.public.demoMode) return

  const url = getRequestURL(event)
  const path = url.pathname
  if (!path.startsWith('/api/')) return

  const method = event.method.toUpperCase()

  // Write operations → 403
  if (method !== 'GET') {
    setResponseStatus(event, 403)
    return { detail: '데모 모드에서는 변경할 수 없습니다.' }
  }

  // Read operations → mock data (pass query params for path-aware routes)
  const query: Record<string, string> = {}
  for (const [k, v] of url.searchParams.entries()) {
    query[k] = v
  }
  const mock = getMockResponse(method, path, query)
  if (mock === '__DEMO_BLOCK__') {
    setResponseStatus(event, 403)
    return { detail: '데모 모드에서는 파일 다운로드/미리보기를 사용할 수 없습니다.' }
  }
  if (mock !== null && mock !== undefined) {
    return mock
  }

  // Fallback: empty success
  return {}
})

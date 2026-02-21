/**
 * Relative time formatting (e.g., "3분 전", "2시간 전")
 */
export function timeAgo(dateStr: string): string {
  const now = Date.now()
  const past = new Date(dateStr).getTime()
  if (isNaN(past)) return ''

  const diff = Math.floor((now - past) / 1000)
  if (diff < 60) return '방금 전'
  if (diff < 3600) return `${Math.floor(diff / 60)}분 전`
  if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`
  if (diff < 2592000) return `${Math.floor(diff / 86400)}일 전`
  if (diff < 31536000) return `${Math.floor(diff / 2592000)}개월 전`
  return `${Math.floor(diff / 31536000)}년 전`
}

/**
 * Human-readable file size (e.g., "1.5 GB")
 */
export function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  const val = bytes / Math.pow(1024, i)
  return `${val < 10 ? val.toFixed(1) : Math.round(val)} ${units[i]}`
}

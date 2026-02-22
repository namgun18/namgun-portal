export interface CalendarInfo {
  id: string
  name: string
  color: string | null
  is_visible: boolean
  sort_order: number
}

export interface CalendarEvent {
  id: string
  calendar_id: string
  title: string
  description: string | null
  location: string | null
  start: string
  end: string
  all_day: boolean
  color: string | null
  status: string | null
  created: string | null
  updated: string | null
}

export interface CalendarShareInfo {
  email: string
  can_write: boolean
}

export type ViewMode = 'month' | 'week' | 'day'

// Module-level singleton state
const calendars = ref<CalendarInfo[]>([])
const events = ref<CalendarEvent[]>([])
const viewMode = ref<ViewMode>('month')
const selectedDate = ref(new Date())
const selectedEvent = ref<CalendarEvent | null>(null)
const loadingCalendars = ref(false)
const loadingEvents = ref(false)
const showEventModal = ref(false)
const editingEvent = ref<CalendarEvent | null>(null)
const showShareModal = ref(false)
const sharingCalendar = ref<CalendarInfo | null>(null)

// Default calendar colors
const CALENDAR_COLORS = [
  '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
  '#ec4899', '#06b6d4', '#f97316',
]

export function useCalendar() {
  // ─── Computed ───

  const visibleCalendarIds = computed(() =>
    new Set(calendars.value.filter(c => c.is_visible).map(c => c.id))
  )

  const visibleEvents = computed(() =>
    events.value.filter(e => visibleCalendarIds.value.has(e.calendar_id))
  )

  const currentMonth = computed(() => selectedDate.value.getMonth())
  const currentYear = computed(() => selectedDate.value.getFullYear())

  // ─── Actions ───

  async function fetchCalendars() {
    loadingCalendars.value = true
    try {
      const data = await $fetch<{ calendars: CalendarInfo[] }>('/api/calendar/calendars')
      calendars.value = data.calendars.map((c, i) => ({
        ...c,
        color: c.color || CALENDAR_COLORS[i % CALENDAR_COLORS.length],
      }))
    } catch (e: any) {
      console.error('fetchCalendars error:', e)
    } finally {
      loadingCalendars.value = false
    }
  }

  async function fetchEvents() {
    loadingEvents.value = true
    try {
      // Fetch a wide range around the selected date
      const d = selectedDate.value
      const start = new Date(d.getFullYear(), d.getMonth() - 1, 1)
      const end = new Date(d.getFullYear(), d.getMonth() + 2, 0)

      const data = await $fetch<{ events: CalendarEvent[] }>('/api/calendar/events', {
        params: {
          start: start.toISOString(),
          end: end.toISOString(),
        },
      })
      // Attach calendar color
      const colorMap = new Map(calendars.value.map(c => [c.id, c.color]))
      events.value = data.events.map(e => ({
        ...e,
        color: e.color || colorMap.get(e.calendar_id) || '#3b82f6',
      }))
    } catch (e: any) {
      console.error('fetchEvents error:', e)
    } finally {
      loadingEvents.value = false
    }
  }

  async function createCalendar(name: string, color?: string) {
    try {
      await $fetch('/api/calendar/calendars', {
        method: 'POST',
        body: { name, color },
      })
      await fetchCalendars()
    } catch (e: any) {
      console.error('createCalendar error:', e)
      throw e
    }
  }

  async function updateCalendar(id: string, updates: Partial<CalendarInfo>) {
    try {
      await $fetch(`/api/calendar/calendars/${id}`, {
        method: 'PATCH',
        body: updates,
      })
      await fetchCalendars()
    } catch (e: any) {
      console.error('updateCalendar error:', e)
    }
  }

  async function deleteCalendar(id: string) {
    try {
      await $fetch(`/api/calendar/calendars/${id}`, { method: 'DELETE' })
      await fetchCalendars()
      await fetchEvents()
    } catch (e: any) {
      console.error('deleteCalendar error:', e)
    }
  }

  async function createEvent(data: {
    calendar_id: string
    title: string
    description?: string
    location?: string
    start: string
    end: string
    all_day?: boolean
  }) {
    try {
      await $fetch('/api/calendar/events', {
        method: 'POST',
        body: data,
      })
      await fetchEvents()
    } catch (e: any) {
      console.error('createEvent error:', e)
      throw e
    }
  }

  async function updateEvent(id: string, data: Record<string, any>) {
    try {
      await $fetch(`/api/calendar/events/${id}`, {
        method: 'PATCH',
        body: data,
      })
      await fetchEvents()
    } catch (e: any) {
      console.error('updateEvent error:', e)
      throw e
    }
  }

  async function deleteEvent(id: string) {
    try {
      await $fetch(`/api/calendar/events/${id}`, { method: 'DELETE' })
      events.value = events.value.filter(e => e.id !== id)
    } catch (e: any) {
      console.error('deleteEvent error:', e)
    }
  }

  function toggleCalendarVisibility(id: string) {
    const cal = calendars.value.find(c => c.id === id)
    if (cal) cal.is_visible = !cal.is_visible
  }

  function soloCalendar(id: string) {
    const allVisible = calendars.value.every(c => c.id === id ? c.is_visible : !c.is_visible)
    if (allVisible) {
      // Already solo — restore all to visible
      calendars.value.forEach(c => c.is_visible = true)
    } else {
      // Solo mode — hide everything except the clicked one
      calendars.value.forEach(c => c.is_visible = c.id === id)
    }
  }

  function setViewMode(mode: ViewMode) {
    viewMode.value = mode
  }

  function goToToday() {
    selectedDate.value = new Date()
  }

  function navigatePrev() {
    const d = new Date(selectedDate.value)
    if (viewMode.value === 'month') d.setMonth(d.getMonth() - 1)
    else if (viewMode.value === 'week') d.setDate(d.getDate() - 7)
    else d.setDate(d.getDate() - 1)
    selectedDate.value = d
  }

  function navigateNext() {
    const d = new Date(selectedDate.value)
    if (viewMode.value === 'month') d.setMonth(d.getMonth() + 1)
    else if (viewMode.value === 'week') d.setDate(d.getDate() + 7)
    else d.setDate(d.getDate() + 1)
    selectedDate.value = d
  }

  function selectDate(date: Date) {
    selectedDate.value = date
  }

  async function fetchCalendarShares(calendarId: string): Promise<CalendarShareInfo[]> {
    try {
      const data = await $fetch<CalendarShareInfo[]>(`/api/calendar/calendars/${calendarId}/shares`)
      return data
    } catch (e: any) {
      console.error('fetchCalendarShares error:', e)
      return []
    }
  }

  async function setCalendarShares(calendarId: string, shares: CalendarShareInfo[]) {
    try {
      await $fetch(`/api/calendar/calendars/${calendarId}/shares`, {
        method: 'POST',
        body: { shares },
      })
    } catch (e: any) {
      console.error('setCalendarShares error:', e)
      throw e
    }
  }

  async function removeCalendarShare(calendarId: string, email: string) {
    try {
      await $fetch(`/api/calendar/calendars/${calendarId}/shares/${encodeURIComponent(email)}`, {
        method: 'DELETE',
      })
    } catch (e: any) {
      console.error('removeCalendarShare error:', e)
      throw e
    }
  }

  function openShareModal(cal: CalendarInfo) {
    sharingCalendar.value = cal
    showShareModal.value = true
  }

  function closeShareModal() {
    showShareModal.value = false
    sharingCalendar.value = null
  }

  function openCreateModal(date?: Date) {
    editingEvent.value = null
    if (date) selectedDate.value = date
    showEventModal.value = true
  }

  function openEditModal(event: CalendarEvent) {
    editingEvent.value = event
    showEventModal.value = true
  }

  function closeModal() {
    showEventModal.value = false
    editingEvent.value = null
  }

  return {
    // State
    calendars: readonly(calendars),
    events: readonly(events),
    viewMode,
    selectedDate,
    selectedEvent,
    loadingCalendars: readonly(loadingCalendars),
    loadingEvents: readonly(loadingEvents),
    showEventModal,
    editingEvent: readonly(editingEvent),
    showShareModal,
    sharingCalendar: readonly(sharingCalendar),
    // Computed
    visibleEvents,
    currentMonth,
    currentYear,
    // Actions
    fetchCalendars,
    fetchEvents,
    createCalendar,
    updateCalendar,
    deleteCalendar,
    createEvent,
    updateEvent,
    deleteEvent,
    toggleCalendarVisibility,
    soloCalendar,
    setViewMode,
    goToToday,
    navigatePrev,
    navigateNext,
    selectDate,
    openCreateModal,
    openEditModal,
    closeModal,
    fetchCalendarShares,
    setCalendarShares,
    removeCalendarShare,
    openShareModal,
    closeShareModal,
    CALENDAR_COLORS,
  }
}

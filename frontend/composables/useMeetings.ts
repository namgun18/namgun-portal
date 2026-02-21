export interface Meeting {
  meetingID: string
  meetingName: string
  running: boolean
  participantCount: number
  moderatorCount: number
  createTime: string
  hasBeenForciblyEnded: boolean
}

export interface Attendee {
  fullName: string
  role: string
  hasJoinedVoice: boolean
  hasVideo: boolean
}

export interface MeetingDetail extends Meeting {
  attendees: Attendee[]
  startTime: string
  moderatorPW: string
  attendeePW: string
}

export interface CreateMeetingRequest {
  name: string
  meetingID?: string | null
  record?: boolean
  duration?: number
  welcome?: string | null
  muteOnStart?: boolean
  maxParticipants?: number
}

export interface Recording {
  recordID: string
  meetingID: string
  name: string
  state: string
  startTime: string
  endTime: string
  playbackUrl: string
  size: number
}

// Module-level singleton state
const meetings = ref<Meeting[]>([])
const selectedMeeting = ref<MeetingDetail | null>(null)
const recordings = ref<Recording[]>([])
const loadingMeetings = ref(false)
const loadingDetail = ref(false)
const loadingRecordings = ref(false)
const showCreateModal = ref(false)

export function useMeetings() {
  async function fetchMeetings() {
    loadingMeetings.value = true
    try {
      meetings.value = await $fetch<Meeting[]>('/api/meetings/')
    } catch (e: any) {
      console.error('fetchMeetings error:', e)
      meetings.value = []
    } finally {
      loadingMeetings.value = false
    }
  }

  async function fetchMeetingDetail(meetingId: string) {
    loadingDetail.value = true
    try {
      selectedMeeting.value = await $fetch<MeetingDetail>(`/api/meetings/${meetingId}`)
    } catch (e: any) {
      console.error('fetchMeetingDetail error:', e)
      selectedMeeting.value = null
    } finally {
      loadingDetail.value = false
    }
  }

  async function createMeeting(data: CreateMeetingRequest) {
    const result = await $fetch<Meeting>('/api/meetings/', {
      method: 'POST',
      body: data,
    })
    showCreateModal.value = false
    await fetchMeetings()
    return result
  }

  async function joinMeeting(meetingId: string) {
    const resp = await $fetch<{ joinUrl: string }>(`/api/meetings/${meetingId}/join`, {
      method: 'POST',
    })
    window.open(resp.joinUrl, '_blank')
  }

  async function endMeeting(meetingId: string) {
    await $fetch(`/api/meetings/${meetingId}/end`, { method: 'POST' })
    selectedMeeting.value = null
    await fetchMeetings()
  }

  async function fetchRecordings(meetingId?: string) {
    loadingRecordings.value = true
    try {
      const params: Record<string, string> = {}
      if (meetingId) params.meeting_id = meetingId
      recordings.value = await $fetch<Recording[]>('/api/meetings/recordings', { params })
    } catch (e: any) {
      console.error('fetchRecordings error:', e)
      recordings.value = []
    } finally {
      loadingRecordings.value = false
    }
  }

  async function deleteRecording(recordId: string) {
    await $fetch(`/api/meetings/recordings/${recordId}`, { method: 'DELETE' })
    await fetchRecordings()
  }

  function clearSelectedMeeting() {
    selectedMeeting.value = null
  }

  return {
    // State
    meetings: readonly(meetings),
    selectedMeeting: readonly(selectedMeeting),
    recordings: readonly(recordings),
    loadingMeetings: readonly(loadingMeetings),
    loadingDetail: readonly(loadingDetail),
    loadingRecordings: readonly(loadingRecordings),
    showCreateModal,
    // Actions
    fetchMeetings,
    fetchMeetingDetail,
    createMeeting,
    joinMeeting,
    endMeeting,
    fetchRecordings,
    deleteRecording,
    clearSelectedMeeting,
  }
}

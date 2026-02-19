<script setup lang="ts">
const emit = defineEmits<{
  close: []
}>()

const { createMeeting } = useMeetings()

const form = reactive({
  name: '',
  record: false,
  duration: 0,
  welcome: '',
  muteOnStart: false,
  maxParticipants: 0,
})

const creating = ref(false)
const error = ref('')

async function handleSubmit() {
  if (!form.name.trim()) {
    error.value = '회의 이름을 입력하세요.'
    return
  }
  creating.value = true
  error.value = ''
  try {
    await createMeeting({
      name: form.name.trim(),
      record: form.record,
      duration: form.duration || 0,
      welcome: form.welcome || null,
      muteOnStart: form.muteOnStart,
      maxParticipants: form.maxParticipants || 0,
    })
    emit('close')
  } catch (e: any) {
    error.value = e?.data?.detail || '회의 생성에 실패했습니다.'
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/50" @click="emit('close')" />

      <!-- Modal -->
      <div class="relative bg-background border rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold">새 회의 만들기</h2>
          <button
            @click="emit('close')"
            class="inline-flex items-center justify-center h-8 w-8 rounded-md hover:bg-accent transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <!-- Name -->
          <div>
            <label class="block text-sm font-medium mb-1">회의 이름 *</label>
            <input
              v-model="form.name"
              type="text"
              placeholder="예: 주간 회의"
              class="w-full px-3 py-2 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
              autofocus
            />
          </div>

          <!-- Welcome message -->
          <div>
            <label class="block text-sm font-medium mb-1">환영 메시지</label>
            <input
              v-model="form.welcome"
              type="text"
              placeholder="(선택사항)"
              class="w-full px-3 py-2 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <!-- Duration -->
            <div>
              <label class="block text-sm font-medium mb-1">제한 시간 (분)</label>
              <input
                v-model.number="form.duration"
                type="number"
                min="0"
                placeholder="0 = 무제한"
                class="w-full px-3 py-2 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>

            <!-- Max participants -->
            <div>
              <label class="block text-sm font-medium mb-1">최대 참가자</label>
              <input
                v-model.number="form.maxParticipants"
                type="number"
                min="0"
                placeholder="0 = 무제한"
                class="w-full px-3 py-2 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
          </div>

          <!-- Toggles -->
          <div class="flex items-center gap-6">
            <label class="flex items-center gap-2 text-sm cursor-pointer">
              <input v-model="form.record" type="checkbox" class="rounded" />
              녹화
            </label>
            <label class="flex items-center gap-2 text-sm cursor-pointer">
              <input v-model="form.muteOnStart" type="checkbox" class="rounded" />
              시작 시 음소거
            </label>
          </div>

          <!-- Error -->
          <p v-if="error" class="text-sm text-destructive">{{ error }}</p>

          <!-- Submit -->
          <div class="flex justify-end gap-2 pt-2">
            <button
              type="button"
              @click="emit('close')"
              class="px-4 py-2 text-sm font-medium rounded-md border hover:bg-accent transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              :disabled="creating"
              class="px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {{ creating ? '생성 중...' : '회의 생성' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

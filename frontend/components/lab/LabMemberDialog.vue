<script setup lang="ts">
const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const { members, selectedEnv, fetchMembers, inviteMember, removeMember } = useLab()
const { user } = useAuth()

const username = ref('')
const inviting = ref(false)
const error = ref('')

async function handleInvite() {
  if (!username.value.trim()) return
  inviting.value = true
  error.value = ''
  try {
    await inviteMember(username.value.trim())
    username.value = ''
  } catch (e: any) {
    error.value = e?.data?.detail || '초대 실패'
  } finally {
    inviting.value = false
  }
}

async function handleRemove(userId: string) {
  if (!confirm('이 멤버를 제거하시겠습니까?')) return
  try {
    await removeMember(userId)
  } catch (e: any) {
    alert(e?.data?.detail || '제거 실패')
  }
}

watch(() => props.open, (v) => {
  if (v) fetchMembers()
})
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="absolute inset-0 bg-black/50" @click="emit('close')" />
      <div class="relative bg-background rounded-lg shadow-xl border w-full max-w-md mx-4 max-h-[80vh] flex flex-col">
        <!-- Header -->
        <div class="flex items-center justify-between p-4 border-b">
          <h3 class="text-lg font-semibold">멤버 관리</h3>
          <button @click="emit('close')" class="p-1 rounded-md hover:bg-accent transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-5 h-5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        <!-- Invite form -->
        <div v-if="selectedEnv?.role === 'owner'" class="p-4 border-b">
          <form @submit.prevent="handleInvite" class="flex gap-2">
            <input
              v-model="username"
              type="text"
              placeholder="사용자명 입력"
              class="flex-1 px-3 py-2 text-sm rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <button
              type="submit"
              :disabled="inviting || !username.trim()"
              class="px-3 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {{ inviting ? '...' : '초대' }}
            </button>
          </form>
          <p v-if="error" class="mt-1 text-xs text-destructive">{{ error }}</p>
        </div>

        <!-- Member list -->
        <div class="flex-1 overflow-y-auto p-4 space-y-2">
          <div
            v-for="m in members"
            :key="m.id"
            class="flex items-center justify-between py-2 px-3 rounded-md bg-accent/30"
          >
            <div>
              <div class="text-sm font-medium">{{ m.display_name || m.username }}</div>
              <div class="text-xs text-muted-foreground">
                @{{ m.username }} · {{ m.role === 'owner' ? '소유자' : '멤버' }}
              </div>
            </div>
            <button
              v-if="m.role === 'member' && selectedEnv?.role === 'owner'"
              @click="handleRemove(m.user_id)"
              class="p-1 rounded-md hover:bg-destructive/20 text-destructive transition-colors"
              title="멤버 제거"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          <div v-if="members.length === 0" class="text-center text-sm text-muted-foreground py-4">
            아직 멤버가 없습니다
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

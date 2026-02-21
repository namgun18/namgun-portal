<script setup lang="ts">
const emit = defineEmits<{ (e: 'select'): void }>()

const {
  environments, selectedEnv, loading,
  fetchEnvironments, createEnvironment, selectEnvironment,
  startEnvironment, stopEnvironment, deleteEnvironment,
} = useLab()

const showCreate = ref(false)
const newName = ref('')
const creating = ref(false)
const actionLoading = ref(false)

async function handleCreate() {
  if (!newName.value.trim()) return
  creating.value = true
  try {
    await createEnvironment(newName.value.trim())
    newName.value = ''
    showCreate.value = false
    emit('select')
  } catch (e: any) {
    alert(e?.data?.detail || '생성 실패')
  } finally {
    creating.value = false
  }
}

async function handleSelect(env: any) {
  await selectEnvironment(env)
  emit('select')
}

async function handleStart() {
  actionLoading.value = true
  try { await startEnvironment() } catch (e: any) { alert(e?.data?.detail || '시작 실패') }
  finally { actionLoading.value = false }
}

async function handleStop() {
  actionLoading.value = true
  try { await stopEnvironment() } catch (e: any) { alert(e?.data?.detail || '중지 실패') }
  finally { actionLoading.value = false }
}

async function handleDelete() {
  if (!confirm('환경과 모든 데이터가 삭제됩니다. 계속하시겠습니까?')) return
  actionLoading.value = true
  try { await deleteEnvironment() } catch (e: any) { alert(e?.data?.detail || '삭제 실패') }
  finally { actionLoading.value = false }
}

const statusColor: Record<string, string> = {
  running: 'bg-green-500',
  stopped: 'bg-gray-400',
  starting: 'bg-yellow-500',
  error: 'bg-red-500',
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="p-3 border-b">
      <h2 class="text-sm font-semibold text-muted-foreground uppercase tracking-wider">AWS Lab</h2>
    </div>

    <!-- Environment list -->
    <div class="flex-1 overflow-y-auto p-2 space-y-1">
      <div v-if="loading" class="p-4 text-center text-sm text-muted-foreground">
        불러오는 중...
      </div>
      <button
        v-for="env in environments"
        :key="env.id"
        @click="handleSelect(env)"
        class="w-full text-left px-3 py-2.5 rounded-md text-sm transition-colors"
        :class="selectedEnv?.id === env.id ? 'bg-accent text-accent-foreground' : 'hover:bg-accent/50 text-foreground'"
      >
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full shrink-0" :class="statusColor[env.status] || 'bg-gray-400'" />
          <span class="truncate font-medium">{{ env.name }}</span>
        </div>
        <div class="mt-0.5 text-xs text-muted-foreground pl-4">
          {{ env.role === 'owner' ? '내 환경' : '공유받음' }}
        </div>
      </button>
      <div v-if="!loading && environments.length === 0" class="p-4 text-center text-sm text-muted-foreground">
        환경이 없습니다
      </div>
    </div>

    <!-- Actions for selected env -->
    <div v-if="selectedEnv" class="p-2 border-t space-y-1">
      <div class="flex gap-1">
        <button
          v-if="selectedEnv.status !== 'running'"
          @click="handleStart"
          :disabled="actionLoading"
          class="flex-1 inline-flex items-center justify-center gap-1 px-2 py-1.5 text-xs font-medium rounded-md bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-3 h-3"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          시작
        </button>
        <button
          v-if="selectedEnv.status === 'running'"
          @click="handleStop"
          :disabled="actionLoading"
          class="flex-1 inline-flex items-center justify-center gap-1 px-2 py-1.5 text-xs font-medium rounded-md bg-yellow-600 text-white hover:bg-yellow-700 disabled:opacity-50 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-3 h-3"><rect x="6" y="6" width="12" height="12"/></svg>
          중지
        </button>
        <button
          v-if="selectedEnv.role === 'owner'"
          @click="handleDelete"
          :disabled="actionLoading"
          class="inline-flex items-center justify-center px-2 py-1.5 text-xs font-medium rounded-md border border-destructive text-destructive hover:bg-destructive hover:text-destructive-foreground disabled:opacity-50 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-3 h-3"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
        </button>
      </div>
    </div>

    <!-- Create button -->
    <div class="p-2 border-t">
      <div v-if="!showCreate">
        <button
          @click="showCreate = true"
          class="w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md border border-dashed hover:bg-accent/50 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          새 환경
        </button>
      </div>
      <form v-else @submit.prevent="handleCreate" class="space-y-2">
        <input
          v-model="newName"
          type="text"
          placeholder="환경 이름 (예: 내 첫 AWS 랩)"
          class="w-full px-3 py-2 text-sm rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-ring"
          autofocus
        />
        <div class="flex gap-1">
          <button
            type="submit"
            :disabled="creating || !newName.trim()"
            class="flex-1 px-3 py-1.5 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {{ creating ? '생성 중...' : '생성' }}
          </button>
          <button
            type="button"
            @click="showCreate = false; newName = ''"
            class="px-3 py-1.5 text-sm font-medium rounded-md border hover:bg-accent transition-colors"
          >
            취소
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

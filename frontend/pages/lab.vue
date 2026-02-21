<script setup lang="ts">
import LabSidebar from '~/components/lab/LabSidebar.vue'
import LabTopology from '~/components/lab/LabTopology.vue'
import LabTerraform from '~/components/lab/LabTerraform.vue'
import LabResourcePanel from '~/components/lab/LabResourcePanel.vue'
import LabMemberDialog from '~/components/lab/LabMemberDialog.vue'

definePageMeta({ layout: 'default' })

const { fetchEnvironments, selectedEnv } = useLab()

const showMobileSidebar = ref(false)
const showMembers = ref(false)
const activePanel = ref<'terraform' | 'resources'>('terraform')

onMounted(async () => {
  await fetchEnvironments()
})
</script>

<template>
  <div class="flex h-[calc(100vh-3.5rem)] overflow-hidden relative">
    <!-- Mobile sidebar overlay -->
    <div
      v-if="showMobileSidebar"
      class="md:hidden fixed inset-0 z-30 bg-black/40"
      @click="showMobileSidebar = false"
    />

    <!-- Sidebar -->
    <div
      class="shrink-0 h-full z-30 transition-transform duration-200
        fixed md:relative
        w-64 md:w-56
        bg-background md:bg-transparent
        shadow-xl md:shadow-none
        border-r"
      :class="showMobileSidebar ? 'translate-x-0' : '-translate-x-full md:translate-x-0'"
    >
      <LabSidebar @select="showMobileSidebar = false" />
    </div>

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Command bar -->
      <div class="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-4 py-2 border-b bg-background">
        <!-- Mobile sidebar toggle -->
        <button
          @click="showMobileSidebar = !showMobileSidebar"
          class="md:hidden inline-flex items-center justify-center h-8 w-8 rounded-md hover:bg-accent transition-colors shrink-0"
          title="환경 목록"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
            <line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>

        <div v-if="selectedEnv" class="flex items-center gap-2 min-w-0">
          <span
            class="w-2 h-2 rounded-full shrink-0"
            :class="selectedEnv.status === 'running' ? 'bg-green-500' : 'bg-gray-400'"
          />
          <span class="text-sm font-medium truncate">{{ selectedEnv.name }}</span>
          <span class="text-xs px-1.5 py-0.5 rounded-full border" :class="selectedEnv.status === 'running' ? 'border-green-500/40 text-green-400' : 'text-muted-foreground'">
            {{ selectedEnv.status === 'running' ? '실행 중' : selectedEnv.status === 'stopped' ? '중지됨' : selectedEnv.status }}
          </span>
        </div>
        <div v-else class="text-sm text-muted-foreground">환경을 선택하거나 새로 만드세요</div>

        <div class="flex-1" />

        <!-- Panel tabs -->
        <div v-if="selectedEnv" class="flex items-center rounded-md border overflow-hidden">
          <button
            @click="activePanel = 'terraform'"
            class="px-2.5 py-1 text-xs font-medium transition-colors"
            :class="activePanel === 'terraform' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50'"
          >
            Terraform
          </button>
          <button
            @click="activePanel = 'resources'"
            class="px-2.5 py-1 text-xs font-medium transition-colors border-l"
            :class="activePanel === 'resources' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50'"
          >
            리소스
          </button>
        </div>

        <!-- Members button -->
        <button
          v-if="selectedEnv"
          @click="showMembers = true"
          class="inline-flex items-center gap-1 px-2 py-1.5 text-sm font-medium rounded-md border hover:bg-accent transition-colors"
          title="멤버 관리"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          <span class="hidden sm:inline">멤버</span>
        </button>
      </div>

      <!-- Main area -->
      <div v-if="selectedEnv" class="flex-1 flex flex-col min-h-0 overflow-hidden">
        <!-- Topology graph -->
        <div class="h-[250px] sm:h-[300px] shrink-0 p-2 sm:p-3 pb-0">
          <LabTopology />
        </div>

        <!-- Terraform / Resources panel -->
        <div class="flex-1 min-h-0 p-2 sm:p-3 pt-2">
          <LabTerraform v-if="activePanel === 'terraform'" class="h-full" />
          <LabResourcePanel v-else class="h-full overflow-y-auto" />
        </div>
      </div>

      <!-- No env selected -->
      <div v-else class="flex-1 flex items-center justify-center">
        <div class="text-center text-muted-foreground">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-16 h-16 mx-auto mb-4 opacity-30">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>
          </svg>
          <h3 class="text-lg font-medium mb-1">AWS Lab</h3>
          <p class="text-sm">Terraform + LocalStack 기반 AWS IaC 학습 환경</p>
          <p class="text-sm mt-1">왼쪽 사이드바에서 환경을 생성해보세요.</p>
        </div>
      </div>
    </div>

    <!-- Member dialog -->
    <LabMemberDialog :open="showMembers" @close="showMembers = false" />
  </div>
</template>

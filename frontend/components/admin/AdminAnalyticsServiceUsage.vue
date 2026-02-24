<script setup lang="ts">
import { Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js'
import type { ServiceUsage } from '~/composables/useAdminAnalytics'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps<{ data: ServiceUsage[] }>()

const colorMode = useColorMode()

const COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#14b8a6', '#f97316', '#64748b']
const SERVICE_LABELS: Record<string, string> = {
  mail: '메일', calendar: '캘린더', contacts: '연락처', files: '파일',
  meetings: '회의', git: 'Git', lab: 'Lab', dashboard: '대시보드',
  admin: '관리', auth: '인증', services: '서비스',
}

const chartData = computed(() => ({
  labels: props.data.map(d => SERVICE_LABELS[d.service] || d.service),
  datasets: [{
    data: props.data.map(d => d.count),
    backgroundColor: props.data.map((_, i) => COLORS[i % COLORS.length]),
    borderWidth: 0,
  }],
}))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'right' as const,
      labels: {
        color: colorMode.value === 'dark' ? '#a1a1aa' : '#71717a',
        usePointStyle: true,
        pointStyleWidth: 10,
        padding: 12,
      },
    },
  },
}))
</script>

<template>
  <div class="rounded-lg border bg-card p-4">
    <h3 class="text-sm font-medium text-muted-foreground mb-3">서비스 사용량</h3>
    <div class="h-[240px]">
      <Doughnut v-if="data.length" :data="chartData" :options="chartOptions" />
      <div v-else class="flex items-center justify-center h-full text-muted-foreground text-sm">
        데이터 없음
      </div>
    </div>
  </div>
</template>

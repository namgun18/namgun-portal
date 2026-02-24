<script setup lang="ts">
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import type { DailyVisit } from '~/composables/useAdminAnalytics'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const props = defineProps<{ data: DailyVisit[] }>()

const colorMode = useColorMode()

const chartData = computed(() => {
  const labels = props.data.map(d => {
    const dt = new Date(d.date)
    return `${dt.getMonth() + 1}/${dt.getDate()}`
  })
  return {
    labels,
    datasets: [
      {
        label: '전체',
        data: props.data.map(d => d.total),
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        fill: true,
        tension: 0.3,
      },
      {
        label: '인증',
        data: props.data.map(d => d.authenticated),
        borderColor: '#22c55e',
        backgroundColor: 'transparent',
        tension: 0.3,
      },
      {
        label: '비인증',
        data: props.data.map(d => d.unauthenticated),
        borderColor: '#f59e0b',
        backgroundColor: 'transparent',
        tension: 0.3,
      },
    ],
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
      labels: { color: colorMode.value === 'dark' ? '#a1a1aa' : '#71717a', usePointStyle: true, pointStyleWidth: 10 },
    },
  },
  scales: {
    x: { ticks: { color: colorMode.value === 'dark' ? '#a1a1aa' : '#71717a' }, grid: { display: false } },
    y: {
      ticks: { color: colorMode.value === 'dark' ? '#a1a1aa' : '#71717a' },
      grid: { color: colorMode.value === 'dark' ? '#27272a' : '#e4e4e7' },
      beginAtZero: true,
    },
  },
}))
</script>

<template>
  <div class="rounded-lg border bg-card p-4">
    <h3 class="text-sm font-medium text-muted-foreground mb-3">일별 방문 추이</h3>
    <div class="h-[240px]">
      <Line v-if="data.length" :data="chartData" :options="chartOptions" />
      <div v-else class="flex items-center justify-center h-full text-muted-foreground text-sm">
        데이터 없음
      </div>
    </div>
  </div>
</template>

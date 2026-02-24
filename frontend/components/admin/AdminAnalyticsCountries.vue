<script setup lang="ts">
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
} from 'chart.js'
import { countryFlag, type CountryStats } from '~/composables/useAdminAnalytics'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

const props = defineProps<{ data: CountryStats[] }>()

const colorMode = useColorMode()

const chartData = computed(() => ({
  labels: props.data.map(d => `${countryFlag(d.country_code)} ${d.country_name || '알 수 없음'}`),
  datasets: [{
    data: props.data.map(d => d.count),
    backgroundColor: '#6366f1',
    borderRadius: 4,
  }],
}))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y' as const,
  plugins: { legend: { display: false } },
  scales: {
    x: {
      ticks: { color: colorMode.value === 'dark' ? '#a1a1aa' : '#71717a' },
      grid: { color: colorMode.value === 'dark' ? '#27272a' : '#e4e4e7' },
      beginAtZero: true,
    },
    y: {
      ticks: { color: colorMode.value === 'dark' ? '#a1a1aa' : '#71717a' },
      grid: { display: false },
    },
  },
}))
</script>

<template>
  <div class="rounded-lg border bg-card p-4">
    <h3 class="text-sm font-medium text-muted-foreground mb-3">국가별 분포</h3>
    <div class="h-[240px]">
      <Bar v-if="data.length" :data="chartData" :options="chartOptions" />
      <div v-else class="flex items-center justify-center h-full text-muted-foreground text-sm">
        데이터 없음
      </div>
    </div>
  </div>
</template>

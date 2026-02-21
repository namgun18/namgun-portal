<script setup lang="ts">
import { onMounted, onBeforeUnmount, watch, ref } from 'vue'

const { topology, selectedEnv, fetchTopology } = useLab()

const cyContainer = ref<HTMLElement | null>(null)
let cy: any = null
let pollTimer: ReturnType<typeof setInterval> | null = null
const autoRefresh = ref(true)

// Service colors
const serviceColors: Record<string, { bg: string; border: string }> = {
  s3: { bg: '#22c55e', border: '#16a34a' },
  sqs: { bg: '#a855f7', border: '#9333ea' },
  lambda: { bg: '#f97316', border: '#ea580c' },
  dynamodb: { bg: '#3b82f6', border: '#2563eb' },
  sns: { bg: '#ef4444', border: '#dc2626' },
  iam: { bg: '#6b7280', border: '#4b5563' },
}

const serviceLabels: Record<string, string> = {
  s3: 'S3',
  sqs: 'SQS',
  lambda: 'Lambda',
  dynamodb: 'DynamoDB',
  sns: 'SNS',
  iam: 'IAM',
}

async function initCytoscape() {
  if (!cyContainer.value) return

  const cytoscape = (await import('cytoscape')).default
  const cytoscapeDagre = (await import('cytoscape-dagre')).default

  cytoscape.use(cytoscapeDagre)

  cy = cytoscape({
    container: cyContainer.value,
    style: [
      {
        selector: 'node',
        style: {
          'label': 'data(label)',
          'text-valign': 'bottom',
          'text-margin-y': 6,
          'font-size': 11,
          'font-weight': 600,
          'color': '#d1d5db',
          'background-color': 'data(bgColor)',
          'border-color': 'data(borderColor)',
          'border-width': 2,
          'width': 48,
          'height': 48,
          'text-wrap': 'ellipsis',
          'text-max-width': 80,
        },
      },
      {
        selector: 'node:selected',
        style: {
          'border-width': 3,
          'border-color': '#818cf8',
          'overlay-color': '#818cf8',
          'overlay-opacity': 0.15,
        },
      },
      {
        selector: 'edge',
        style: {
          'width': 2,
          'line-color': '#6b7280',
          'target-arrow-color': '#6b7280',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'label': 'data(label)',
          'font-size': 9,
          'color': '#9ca3af',
          'text-background-color': '#1f2937',
          'text-background-opacity': 0.8,
          'text-background-padding': '2px',
        },
      },
    ],
    layout: { name: 'grid' },
    minZoom: 0.3,
    maxZoom: 3,
  })
}

function renderGraph() {
  if (!cy) return

  cy.elements().remove()

  if (topology.value.nodes.length === 0) return

  // Add nodes
  for (const node of topology.value.nodes) {
    const svc = node.service || 'iam'
    const colors = serviceColors[svc] || serviceColors.iam
    cy.add({
      group: 'nodes',
      data: {
        id: node.id,
        label: `[${serviceLabels[svc] || svc}]\n${node.label}`,
        bgColor: colors.bg,
        borderColor: colors.border,
        service: svc,
      },
    })
  }

  // Add edges
  for (const edge of topology.value.edges) {
    // Only add edge if both source and target exist
    if (cy.getElementById(edge.source).length && cy.getElementById(edge.target).length) {
      cy.add({
        group: 'edges',
        data: {
          source: edge.source,
          target: edge.target,
          label: edge.label || '',
        },
      })
    }
  }

  // Apply dagre layout
  cy.layout({
    name: 'dagre',
    rankDir: 'TB',
    nodeSep: 60,
    rankSep: 80,
    padding: 30,
  }).run()

  cy.fit(undefined, 40)
}

function handleFit() {
  if (cy) cy.fit(undefined, 40)
}

function startPolling() {
  stopPolling()
  if (autoRefresh.value) {
    pollTimer = setInterval(() => {
      if (selectedEnv.value?.status === 'running') {
        fetchTopology()
      }
    }, 10000)
  }
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

watch(autoRefresh, (v) => {
  if (v) startPolling()
  else stopPolling()
})

watch(() => topology.value, () => {
  renderGraph()
}, { deep: true })

onMounted(async () => {
  await initCytoscape()
  renderGraph()
  startPolling()
})

onBeforeUnmount(() => {
  stopPolling()
  if (cy) { cy.destroy(); cy = null }
})
</script>

<template>
  <div class="flex flex-col h-full border rounded-lg bg-card overflow-hidden">
    <!-- Toolbar -->
    <div class="flex items-center gap-2 px-3 py-2 border-b bg-background/80">
      <span class="text-xs font-semibold text-muted-foreground uppercase tracking-wider">토폴로지</span>
      <div class="flex-1" />
      <label class="flex items-center gap-1 text-xs text-muted-foreground cursor-pointer">
        <input v-model="autoRefresh" type="checkbox" class="rounded" />
        자동 새로고침
      </label>
      <button
        @click="fetchTopology"
        class="inline-flex items-center justify-center p-1.5 rounded-md hover:bg-accent transition-colors"
        title="새로고침"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-3.5 h-3.5"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
      </button>
      <button
        @click="handleFit"
        class="inline-flex items-center justify-center p-1.5 rounded-md hover:bg-accent transition-colors"
        title="화면 맞춤"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-3.5 h-3.5"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>
      </button>
    </div>

    <!-- Graph -->
    <div class="flex-1 relative min-h-[200px]">
      <div ref="cyContainer" class="absolute inset-0" />
      <!-- Empty state -->
      <div
        v-if="topology.nodes.length === 0 && selectedEnv?.status === 'running'"
        class="absolute inset-0 flex items-center justify-center"
      >
        <div class="text-center text-muted-foreground">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-12 h-12 mx-auto mb-2 opacity-40"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          <p class="text-sm">아직 AWS 리소스가 없습니다</p>
          <p class="text-xs mt-1">아래 패널에서 리소스를 생성해보세요</p>
        </div>
      </div>
      <div
        v-if="selectedEnv?.status !== 'running'"
        class="absolute inset-0 flex items-center justify-center"
      >
        <div class="text-center text-muted-foreground">
          <p class="text-sm">환경을 시작하면 토폴로지가 표시됩니다</p>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div v-if="topology.nodes.length > 0" class="flex items-center gap-3 px-3 py-1.5 border-t text-xs text-muted-foreground overflow-x-auto">
      <span v-for="(colors, svc) in serviceColors" :key="svc" class="flex items-center gap-1 shrink-0">
        <span class="w-2.5 h-2.5 rounded-full" :style="{ backgroundColor: colors.bg }" />
        {{ serviceLabels[svc] || svc }}
      </span>
    </div>
  </div>
</template>

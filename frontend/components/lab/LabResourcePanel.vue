<script setup lang="ts">
const {
  selectedEnv, resourceLoading, fetchAllResources, fetchTopology,
  s3Buckets, sqsQueues, lambdaFunctions, dynamoTables, snsTopics,
  createBucket, deleteBucket, listObjects, uploadObject, deleteObject,
  createQueue, deleteQueue, sendMessage, receiveMessages,
  createFunction, deleteFunction, invokeFunction,
  createTable, deleteTable, scanTable, putItem,
  createTopic, deleteTopic, publishMessage, subscribeTopic,
} = useLab()

const activeTab = ref('s3')
const tabs = [
  { id: 's3', label: 'S3' },
  { id: 'sqs', label: 'SQS' },
  { id: 'lambda', label: 'Lambda' },
  { id: 'dynamodb', label: 'DynamoDB' },
  { id: 'sns', label: 'SNS' },
]

const tabColors: Record<string, string> = {
  s3: 'bg-green-500/20 text-green-400 border-green-500/40',
  sqs: 'bg-purple-500/20 text-purple-400 border-purple-500/40',
  lambda: 'bg-orange-500/20 text-orange-400 border-orange-500/40',
  dynamodb: 'bg-blue-500/20 text-blue-400 border-blue-500/40',
  sns: 'bg-red-500/20 text-red-400 border-red-500/40',
}

// ─── S3 state ───
const newBucket = ref('')
const selectedBucket = ref<string | null>(null)
const objects = ref<any[]>([])
const objectsLoading = ref(false)

async function handleCreateBucket() {
  if (!newBucket.value.trim()) return
  try { await createBucket(newBucket.value.trim()); newBucket.value = '' } catch (e: any) { alert(e?.data?.detail || 'S3 버킷 생성 실패') }
}
async function handleDeleteBucket(name: string) {
  if (!confirm(`"${name}" 버킷을 삭제하시겠습니까?`)) return
  try { await deleteBucket(name); if (selectedBucket.value === name) selectedBucket.value = null } catch (e: any) { alert(e?.data?.detail || '삭제 실패') }
}
async function handleSelectBucket(name: string) {
  selectedBucket.value = name
  objectsLoading.value = true
  try { objects.value = await listObjects(name) || [] } catch { objects.value = [] }
  finally { objectsLoading.value = false }
}
async function handleUpload(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (!files?.length || !selectedBucket.value) return
  for (const f of files) {
    try { await uploadObject(selectedBucket.value, f) } catch { /* skip */ }
  }
  await handleSelectBucket(selectedBucket.value)
  await fetchTopology()
}
async function handleDeleteObject(key: string) {
  if (!selectedBucket.value) return
  try { await deleteObject(selectedBucket.value, key) } catch { /* skip */ }
  await handleSelectBucket(selectedBucket.value)
}

// ─── SQS state ───
const newQueue = ref('')
const sqsMsgBody = ref('')
const sqsMsgTarget = ref('')
const receivedMsgs = ref<any[]>([])

async function handleCreateQueue() {
  if (!newQueue.value.trim()) return
  try { await createQueue(newQueue.value.trim()); newQueue.value = '' } catch (e: any) { alert(e?.data?.detail || 'SQS 큐 생성 실패') }
}
async function handleDeleteQueue(url: string) {
  if (!confirm('이 큐를 삭제하시겠습니까?')) return
  try { await deleteQueue(url) } catch (e: any) { alert(e?.data?.detail || '삭제 실패') }
}
async function handleSendMessage() {
  if (!sqsMsgBody.value.trim() || !sqsMsgTarget.value) return
  try { await sendMessage(sqsMsgTarget.value, sqsMsgBody.value); sqsMsgBody.value = '' } catch (e: any) { alert(e?.data?.detail || '메시지 발송 실패') }
  await fetchAllResources()
}
async function handleReceive(name: string) {
  try { receivedMsgs.value = await receiveMessages(name) || [] } catch { receivedMsgs.value = [] }
}

// ─── Lambda state ───
const lambdaName = ref('')
const lambdaCode = ref('def lambda_handler(event, context):\n    return {"statusCode": 200, "body": "Hello from Lambda!"}')
const lambdaPayload = ref('{}')
const lambdaResult = ref<any>(null)
const lambdaRunning = ref(false)

async function handleCreateLambda() {
  if (!lambdaName.value.trim()) return
  try { await createFunction(lambdaName.value.trim(), lambdaCode.value); lambdaName.value = '' } catch (e: any) { alert(e?.data?.detail || 'Lambda 함수 생성 실패') }
}
async function handleDeleteLambda(name: string) {
  if (!confirm(`"${name}" 함수를 삭제하시겠습니까?`)) return
  try { await deleteFunction(name) } catch (e: any) { alert(e?.data?.detail || '삭제 실패') }
}
async function handleInvoke(name: string) {
  lambdaRunning.value = true
  try {
    let payload = {}
    try { payload = JSON.parse(lambdaPayload.value) } catch { /* empty */ }
    lambdaResult.value = await invokeFunction(name, payload)
  } catch (e: any) { lambdaResult.value = { error: e?.data?.detail || '실행 실패' } }
  finally { lambdaRunning.value = false }
}

// ─── DynamoDB state ───
const dynamoName = ref('')
const dynamoPK = ref('id')
const dynamoPKType = ref('S')
const dynamoSK = ref('')
const dynamoSKType = ref('S')
const dynamoSelectedTable = ref<string | null>(null)
const dynamoItems = ref<any[]>([])
const dynamoNewItem = ref('{}')
const dynamoItemsLoading = ref(false)

async function handleCreateDynamo() {
  if (!dynamoName.value.trim() || !dynamoPK.value.trim()) return
  try {
    await createTable(dynamoName.value.trim(), dynamoPK.value.trim(), dynamoPKType.value, dynamoSK.value.trim() || undefined, dynamoSKType.value)
    dynamoName.value = ''
  } catch (e: any) { alert(e?.data?.detail || 'DynamoDB 테이블 생성 실패') }
}
async function handleDeleteDynamo(name: string) {
  if (!confirm(`"${name}" 테이블을 삭제하시겠습니까?`)) return
  try { await deleteTable(name); if (dynamoSelectedTable.value === name) dynamoSelectedTable.value = null } catch (e: any) { alert(e?.data?.detail || '삭제 실패') }
}
async function handleScanDynamo(table: string) {
  dynamoSelectedTable.value = table
  dynamoItemsLoading.value = true
  try { dynamoItems.value = await scanTable(table) || [] } catch { dynamoItems.value = [] }
  finally { dynamoItemsLoading.value = false }
}
async function handlePutItem() {
  if (!dynamoSelectedTable.value) return
  try {
    const item = JSON.parse(dynamoNewItem.value)
    await putItem(dynamoSelectedTable.value, item)
    dynamoNewItem.value = '{}'
    await handleScanDynamo(dynamoSelectedTable.value)
  } catch (e: any) { alert(e?.data?.detail || '아이템 추가 실패') }
}

// ─── SNS state ───
const newTopic = ref('')
const snsMsg = ref('')
const snsMsgTarget = ref('')
const snsSubProtocol = ref('sqs')
const snsSubEndpoint = ref('')
const snsSubTarget = ref('')

async function handleCreateTopic() {
  if (!newTopic.value.trim()) return
  try { await createTopic(newTopic.value.trim()); newTopic.value = '' } catch (e: any) { alert(e?.data?.detail || 'SNS 토픽 생성 실패') }
}
async function handleDeleteTopic(arn: string) {
  if (!confirm('이 토픽을 삭제하시겠습니까?')) return
  try { await deleteTopic(arn) } catch (e: any) { alert(e?.data?.detail || '삭제 실패') }
}
async function handlePublish() {
  if (!snsMsg.value.trim() || !snsMsgTarget.value) return
  try { await publishMessage(snsMsgTarget.value, snsMsg.value); snsMsg.value = '' } catch (e: any) { alert(e?.data?.detail || '발행 실패') }
}
async function handleSubscribe() {
  if (!snsSubTarget.value || !snsSubEndpoint.value.trim()) return
  try {
    await subscribeTopic(snsSubTarget.value, snsSubProtocol.value, snsSubEndpoint.value.trim())
    snsSubEndpoint.value = ''
    await fetchAllResources()
    await fetchTopology()
  } catch (e: any) { alert(e?.data?.detail || '구독 실패') }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / 1048576).toFixed(1)}MB`
}
</script>

<template>
  <div class="border rounded-lg bg-card overflow-hidden flex flex-col">
    <!-- Tab bar -->
    <div class="flex items-center gap-1 px-2 py-1.5 border-b bg-background/80 overflow-x-auto">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="activeTab = tab.id"
        class="px-3 py-1 text-xs font-semibold rounded-md border transition-colors shrink-0"
        :class="activeTab === tab.id ? tabColors[tab.id] : 'text-muted-foreground border-transparent hover:bg-accent/50'"
      >
        {{ tab.label }}
      </button>
      <div class="flex-1" />
      <button
        @click="fetchAllResources(); fetchTopology()"
        class="p-1.5 rounded-md hover:bg-accent transition-colors"
        title="새로고침"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-3.5 h-3.5"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
      </button>
    </div>

    <!-- Loading -->
    <div v-if="resourceLoading" class="p-4 text-center text-sm text-muted-foreground">불러오는 중...</div>

    <!-- Not running -->
    <div v-else-if="selectedEnv?.status !== 'running'" class="p-8 text-center text-sm text-muted-foreground">
      환경을 시작하면 리소스를 관리할 수 있습니다
    </div>

    <!-- Content -->
    <div v-else class="flex-1 overflow-y-auto p-3 space-y-3">

      <!-- ═══ S3 ═══ -->
      <template v-if="activeTab === 's3'">
        <form @submit.prevent="handleCreateBucket" class="flex gap-2">
          <input v-model="newBucket" placeholder="버킷 이름" class="flex-1 px-3 py-1.5 text-sm rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-ring" />
          <button type="submit" :disabled="!newBucket.trim()" class="px-3 py-1.5 text-sm font-medium rounded-md bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition-colors">생성</button>
        </form>
        <div v-if="s3Buckets.length === 0" class="text-sm text-muted-foreground text-center py-4">S3 버킷이 없습니다</div>
        <div v-for="b in s3Buckets" :key="b.name" class="border rounded-md">
          <div class="flex items-center justify-between px-3 py-2 cursor-pointer hover:bg-accent/30 transition-colors" @click="handleSelectBucket(b.name)">
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-green-500" />
              <span class="text-sm font-medium">{{ b.name }}</span>
            </div>
            <button @click.stop="handleDeleteBucket(b.name)" class="p-1 rounded hover:bg-destructive/20 text-destructive transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-3.5 h-3.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
          <!-- Objects -->
          <div v-if="selectedBucket === b.name" class="border-t px-3 py-2 space-y-2">
            <div v-if="objectsLoading" class="text-xs text-muted-foreground">불러오는 중...</div>
            <div v-else-if="objects.length === 0" class="text-xs text-muted-foreground">오브젝트 없음</div>
            <div v-for="obj in objects" :key="obj.key" class="flex items-center justify-between text-sm">
              <span class="truncate">{{ obj.key }}</span>
              <div class="flex items-center gap-2 shrink-0">
                <span class="text-xs text-muted-foreground">{{ formatSize(obj.size) }}</span>
                <button @click="handleDeleteObject(obj.key)" class="text-destructive hover:text-destructive/80">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-3.5 h-3.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
              </div>
            </div>
            <label class="inline-flex items-center gap-1.5 px-2 py-1 text-xs font-medium rounded-md border border-dashed cursor-pointer hover:bg-accent/50 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-3.5 h-3.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
              파일 업로드
              <input type="file" class="hidden" multiple @change="handleUpload" />
            </label>
          </div>
        </div>
      </template>

      <!-- ═══ SQS ═══ -->
      <template v-if="activeTab === 'sqs'">
        <form @submit.prevent="handleCreateQueue" class="flex gap-2">
          <input v-model="newQueue" placeholder="큐 이름" class="flex-1 px-3 py-1.5 text-sm rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-ring" />
          <button type="submit" :disabled="!newQueue.trim()" class="px-3 py-1.5 text-sm font-medium rounded-md bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50 transition-colors">생성</button>
        </form>
        <div v-if="sqsQueues.length === 0" class="text-sm text-muted-foreground text-center py-4">SQS 큐가 없습니다</div>
        <div v-for="q in sqsQueues" :key="q.url" class="border rounded-md px-3 py-2 space-y-2">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-purple-500" />
              <span class="text-sm font-medium">{{ q.name }}</span>
              <span class="text-xs text-muted-foreground">{{ q.messages }}건</span>
            </div>
            <button @click="handleDeleteQueue(q.url)" class="p-1 rounded hover:bg-destructive/20 text-destructive transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-3.5 h-3.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
          <!-- Send -->
          <div class="flex gap-1">
            <input v-model="sqsMsgBody" placeholder="메시지 내용" class="flex-1 px-2 py-1 text-xs rounded border bg-background focus:outline-none focus:ring-1 focus:ring-ring" />
            <button @click="sqsMsgTarget = q.name; handleSendMessage()" :disabled="!sqsMsgBody.trim()" class="px-2 py-1 text-xs rounded bg-purple-600 text-white disabled:opacity-50">발송</button>
            <button @click="handleReceive(q.name)" class="px-2 py-1 text-xs rounded border hover:bg-accent/50">수신</button>
          </div>
          <!-- Received -->
          <div v-if="receivedMsgs.length > 0 && sqsMsgTarget === q.name" class="space-y-1">
            <div v-for="m in receivedMsgs" :key="m.message_id" class="text-xs bg-accent/20 rounded px-2 py-1 font-mono break-all">{{ m.body }}</div>
          </div>
        </div>
      </template>

      <!-- ═══ Lambda ═══ -->
      <template v-if="activeTab === 'lambda'">
        <div class="space-y-2 border rounded-md p-3">
          <input v-model="lambdaName" placeholder="함수 이름" class="w-full px-3 py-1.5 text-sm rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-ring" />
          <textarea
            v-model="lambdaCode"
            rows="6"
            class="w-full px-3 py-2 text-xs font-mono rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-ring resize-y"
            placeholder="Python 코드를 입력하세요..."
          />
          <button @click="handleCreateLambda" :disabled="!lambdaName.trim()" class="px-3 py-1.5 text-sm font-medium rounded-md bg-orange-600 text-white hover:bg-orange-700 disabled:opacity-50 transition-colors">함수 생성</button>
        </div>
        <div v-if="lambdaFunctions.length === 0" class="text-sm text-muted-foreground text-center py-4">Lambda 함수가 없습니다</div>
        <div v-for="fn in lambdaFunctions" :key="fn.name" class="border rounded-md px-3 py-2 space-y-2">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-orange-500" />
              <span class="text-sm font-medium">{{ fn.name }}</span>
              <span class="text-xs text-muted-foreground">{{ fn.runtime }}</span>
            </div>
            <button @click="handleDeleteLambda(fn.name)" class="p-1 rounded hover:bg-destructive/20 text-destructive transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-3.5 h-3.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
          <div class="flex gap-1">
            <input v-model="lambdaPayload" placeholder='{"key": "value"}' class="flex-1 px-2 py-1 text-xs font-mono rounded border bg-background focus:outline-none focus:ring-1 focus:ring-ring" />
            <button @click="handleInvoke(fn.name)" :disabled="lambdaRunning" class="px-2 py-1 text-xs rounded bg-orange-600 text-white disabled:opacity-50">
              {{ lambdaRunning ? '실행 중...' : '실행' }}
            </button>
          </div>
          <div v-if="lambdaResult" class="text-xs bg-accent/20 rounded px-2 py-1 font-mono break-all whitespace-pre-wrap">{{ JSON.stringify(lambdaResult, null, 2) }}</div>
        </div>
      </template>

      <!-- ═══ DynamoDB ═══ -->
      <template v-if="activeTab === 'dynamodb'">
        <div class="space-y-2 border rounded-md p-3">
          <input v-model="dynamoName" placeholder="테이블 이름" class="w-full px-3 py-1.5 text-sm rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-ring" />
          <div class="flex gap-2">
            <input v-model="dynamoPK" placeholder="파티션 키" class="flex-1 px-2 py-1 text-sm rounded border bg-background" />
            <select v-model="dynamoPKType" class="px-2 py-1 text-sm rounded border bg-background">
              <option value="S">String</option>
              <option value="N">Number</option>
            </select>
          </div>
          <div class="flex gap-2">
            <input v-model="dynamoSK" placeholder="정렬 키 (선택)" class="flex-1 px-2 py-1 text-sm rounded border bg-background" />
            <select v-model="dynamoSKType" class="px-2 py-1 text-sm rounded border bg-background">
              <option value="S">String</option>
              <option value="N">Number</option>
            </select>
          </div>
          <button @click="handleCreateDynamo" :disabled="!dynamoName.trim() || !dynamoPK.trim()" class="px-3 py-1.5 text-sm font-medium rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors">테이블 생성</button>
        </div>
        <div v-if="dynamoTables.length === 0" class="text-sm text-muted-foreground text-center py-4">DynamoDB 테이블이 없습니다</div>
        <div v-for="t in dynamoTables" :key="t.name" class="border rounded-md">
          <div class="flex items-center justify-between px-3 py-2 cursor-pointer hover:bg-accent/30 transition-colors" @click="handleScanDynamo(t.name)">
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-blue-500" />
              <span class="text-sm font-medium">{{ t.name }}</span>
              <span class="text-xs text-muted-foreground">{{ t.item_count }}건</span>
            </div>
            <button @click.stop="handleDeleteDynamo(t.name)" class="p-1 rounded hover:bg-destructive/20 text-destructive transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-3.5 h-3.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
          <div v-if="dynamoSelectedTable === t.name" class="border-t px-3 py-2 space-y-2">
            <div v-if="dynamoItemsLoading" class="text-xs text-muted-foreground">불러오는 중...</div>
            <div v-else-if="dynamoItems.length === 0" class="text-xs text-muted-foreground">아이템 없음</div>
            <div v-for="(item, idx) in dynamoItems" :key="idx" class="text-xs bg-accent/20 rounded px-2 py-1 font-mono break-all">{{ JSON.stringify(item) }}</div>
            <div class="flex gap-1">
              <input v-model="dynamoNewItem" placeholder='{"id":"1","name":"test"}' class="flex-1 px-2 py-1 text-xs font-mono rounded border bg-background focus:outline-none focus:ring-1 focus:ring-ring" />
              <button @click="handlePutItem" class="px-2 py-1 text-xs rounded bg-blue-600 text-white">추가</button>
            </div>
          </div>
        </div>
      </template>

      <!-- ═══ SNS ═══ -->
      <template v-if="activeTab === 'sns'">
        <form @submit.prevent="handleCreateTopic" class="flex gap-2">
          <input v-model="newTopic" placeholder="토픽 이름" class="flex-1 px-3 py-1.5 text-sm rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-ring" />
          <button type="submit" :disabled="!newTopic.trim()" class="px-3 py-1.5 text-sm font-medium rounded-md bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-colors">생성</button>
        </form>
        <div v-if="snsTopics.length === 0" class="text-sm text-muted-foreground text-center py-4">SNS 토픽이 없습니다</div>
        <div v-for="t in snsTopics" :key="t.arn" class="border rounded-md px-3 py-2 space-y-2">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-red-500" />
              <span class="text-sm font-medium">{{ t.name }}</span>
              <span class="text-xs text-muted-foreground">구독 {{ t.subscriptions }}개</span>
            </div>
            <button @click="handleDeleteTopic(t.arn)" class="p-1 rounded hover:bg-destructive/20 text-destructive transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-3.5 h-3.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
          <!-- Publish -->
          <div class="flex gap-1">
            <input v-model="snsMsg" placeholder="메시지" class="flex-1 px-2 py-1 text-xs rounded border bg-background" />
            <button @click="snsMsgTarget = t.name; handlePublish()" :disabled="!snsMsg.trim()" class="px-2 py-1 text-xs rounded bg-red-600 text-white disabled:opacity-50">발행</button>
          </div>
          <!-- Subscribe -->
          <div class="flex gap-1 items-center">
            <select v-model="snsSubProtocol" class="px-1 py-1 text-xs rounded border bg-background">
              <option value="sqs">SQS</option>
              <option value="lambda">Lambda</option>
              <option value="http">HTTP</option>
              <option value="email">Email</option>
            </select>
            <input v-model="snsSubEndpoint" placeholder="엔드포인트 ARN/URL" class="flex-1 px-2 py-1 text-xs rounded border bg-background" />
            <button @click="snsSubTarget = t.name; handleSubscribe()" :disabled="!snsSubEndpoint.trim()" class="px-2 py-1 text-xs rounded border hover:bg-accent/50 disabled:opacity-50">구독</button>
          </div>
        </div>
      </template>

    </div>
  </div>
</template>

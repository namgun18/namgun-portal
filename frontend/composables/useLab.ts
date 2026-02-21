interface LabEnvironment {
  id: string
  owner_id: string
  name: string
  container_name: string
  status: string
  created_at: string
  role: string
}

interface LabMember {
  id: string
  user_id: string
  username: string
  display_name: string | null
  role: string
  invited_at: string
}

interface TopologyNode {
  id: string
  label: string
  service: string
  details?: Record<string, any>
}

interface TopologyEdge {
  source: string
  target: string
  label?: string
}

interface Topology {
  nodes: TopologyNode[]
  edges: TopologyEdge[]
}

export const useLab = () => {
  const environments = useState<LabEnvironment[]>('lab-envs', () => [])
  const selectedEnv = useState<LabEnvironment | null>('lab-selected', () => null)
  const topology = useState<Topology>('lab-topology', () => ({ nodes: [], edges: [] }))
  const members = useState<LabMember[]>('lab-members', () => [])
  const loading = useState<boolean>('lab-loading', () => false)
  const resourceLoading = useState<boolean>('lab-res-loading', () => false)

  // Resources per service
  const s3Buckets = useState<any[]>('lab-s3', () => [])
  const sqsQueues = useState<any[]>('lab-sqs', () => [])
  const lambdaFunctions = useState<any[]>('lab-lambda', () => [])
  const dynamoTables = useState<any[]>('lab-dynamo', () => [])
  const snsTopics = useState<any[]>('lab-sns', () => [])

  // ─── Environments ───

  const fetchEnvironments = async () => {
    loading.value = true
    try {
      environments.value = await $fetch<LabEnvironment[]>('/api/lab/environments', { credentials: 'include' })
    } catch {
      environments.value = []
    } finally {
      loading.value = false
    }
  }

  const createEnvironment = async (name: string) => {
    const env = await $fetch<LabEnvironment>('/api/lab/environments', {
      method: 'POST',
      body: { name },
      credentials: 'include',
    })
    environments.value = [env, ...environments.value]
    selectedEnv.value = env
    return env
  }

  const selectEnvironment = async (env: LabEnvironment) => {
    selectedEnv.value = env
    // Refresh status
    try {
      const fresh = await $fetch<LabEnvironment>(`/api/lab/environments/${env.id}`, { credentials: 'include' })
      selectedEnv.value = fresh
      // Update in list
      const idx = environments.value.findIndex(e => e.id === env.id)
      if (idx >= 0) environments.value[idx] = fresh
    } catch { /* keep stale */ }

    if (env.status === 'running') {
      await Promise.all([fetchTopology(), fetchAllResources(), fetchMembers()])
    } else {
      topology.value = { nodes: [], edges: [] }
      clearResources()
    }
  }

  const startEnvironment = async () => {
    if (!selectedEnv.value) return
    await $fetch(`/api/lab/environments/${selectedEnv.value.id}/start`, { method: 'POST', credentials: 'include' })
    selectedEnv.value = { ...selectedEnv.value, status: 'running' }
    const idx = environments.value.findIndex(e => e.id === selectedEnv.value!.id)
    if (idx >= 0) environments.value[idx] = selectedEnv.value
    await Promise.all([fetchTopology(), fetchAllResources()])
  }

  const stopEnvironment = async () => {
    if (!selectedEnv.value) return
    await $fetch(`/api/lab/environments/${selectedEnv.value.id}/stop`, { method: 'POST', credentials: 'include' })
    selectedEnv.value = { ...selectedEnv.value, status: 'stopped' }
    const idx = environments.value.findIndex(e => e.id === selectedEnv.value!.id)
    if (idx >= 0) environments.value[idx] = selectedEnv.value
    topology.value = { nodes: [], edges: [] }
    clearResources()
  }

  const deleteEnvironment = async () => {
    if (!selectedEnv.value) return
    await $fetch(`/api/lab/environments/${selectedEnv.value.id}`, { method: 'DELETE', credentials: 'include' })
    environments.value = environments.value.filter(e => e.id !== selectedEnv.value!.id)
    selectedEnv.value = environments.value[0] ?? null
    if (selectedEnv.value) await selectEnvironment(selectedEnv.value)
  }

  // ─── Members ───

  const fetchMembers = async () => {
    if (!selectedEnv.value) return
    try {
      members.value = await $fetch<LabMember[]>(`/api/lab/environments/${selectedEnv.value.id}/members`, { credentials: 'include' })
    } catch {
      members.value = []
    }
  }

  const inviteMember = async (username: string) => {
    if (!selectedEnv.value) return
    const m = await $fetch<LabMember>(`/api/lab/environments/${selectedEnv.value.id}/members`, {
      method: 'POST',
      body: { username },
      credentials: 'include',
    })
    members.value = [...members.value, m]
    return m
  }

  const removeMember = async (userId: string) => {
    if (!selectedEnv.value) return
    await $fetch(`/api/lab/environments/${selectedEnv.value.id}/members/${userId}`, {
      method: 'DELETE',
      credentials: 'include',
    })
    members.value = members.value.filter(m => m.user_id !== userId)
  }

  // ─── Topology ───

  const fetchTopology = async () => {
    if (!selectedEnv.value || selectedEnv.value.status !== 'running') return
    try {
      topology.value = await $fetch<Topology>(`/api/lab/environments/${selectedEnv.value.id}/topology`, { credentials: 'include' })
    } catch {
      topology.value = { nodes: [], edges: [] }
    }
  }

  // ─── Resources ───

  const clearResources = () => {
    s3Buckets.value = []
    sqsQueues.value = []
    lambdaFunctions.value = []
    dynamoTables.value = []
    snsTopics.value = []
  }

  const fetchAllResources = async () => {
    if (!selectedEnv.value || selectedEnv.value.status !== 'running') return
    resourceLoading.value = true
    const id = selectedEnv.value.id
    try {
      const [s3, sqs, lambda_, dynamo, sns] = await Promise.all([
        $fetch<any[]>(`/api/lab/environments/${id}/resources/s3`, { credentials: 'include' }).catch(() => []),
        $fetch<any[]>(`/api/lab/environments/${id}/resources/sqs`, { credentials: 'include' }).catch(() => []),
        $fetch<any[]>(`/api/lab/environments/${id}/resources/lambda`, { credentials: 'include' }).catch(() => []),
        $fetch<any[]>(`/api/lab/environments/${id}/resources/dynamodb`, { credentials: 'include' }).catch(() => []),
        $fetch<any[]>(`/api/lab/environments/${id}/resources/sns`, { credentials: 'include' }).catch(() => []),
      ])
      s3Buckets.value = s3
      sqsQueues.value = sqs
      lambdaFunctions.value = lambda_
      dynamoTables.value = dynamo
      snsTopics.value = sns
    } finally {
      resourceLoading.value = false
    }
  }

  // ─── S3 ───

  const createBucket = async (name: string) => {
    if (!selectedEnv.value) return
    await $fetch(`/api/lab/environments/${selectedEnv.value.id}/resources/s3`, {
      method: 'POST', body: { name }, credentials: 'include',
    })
    await fetchAllResources()
    await fetchTopology()
  }

  const deleteBucket = async (name: string) => {
    if (!selectedEnv.value) return
    await $fetch(`/api/lab/environments/${selectedEnv.value.id}/resources/s3/${name}`, {
      method: 'DELETE', credentials: 'include',
    })
    await fetchAllResources()
    await fetchTopology()
  }

  const listObjects = async (bucket: string) => {
    if (!selectedEnv.value) return []
    return await $fetch<any[]>(`/api/lab/environments/${selectedEnv.value.id}/s3/${bucket}/objects`, { credentials: 'include' })
  }

  const uploadObject = async (bucket: string, file: File) => {
    if (!selectedEnv.value) return
    const form = new FormData()
    form.append('file', file)
    await $fetch(`/api/lab/environments/${selectedEnv.value.id}/s3/${bucket}/upload`, {
      method: 'POST', body: form, credentials: 'include',
    })
  }

  const deleteObject = async (bucket: string, key: string) => {
    if (!selectedEnv.value) return
    await $fetch(`/api/lab/environments/${selectedEnv.value.id}/s3/${bucket}/${key}`, {
      method: 'DELETE', credentials: 'include',
    })
  }

  // ─── SQS ───

  const createQueue = async (name: string) => {
    if (!selectedEnv.value) return
    await $fetch(`/api/lab/environments/${selectedEnv.value.id}/resources/sqs`, {
      method: 'POST', body: { name }, credentials: 'include',
    })
    await fetchAllResources()
    await fetchTopology()
  }

  const deleteQueue = async (url: string) => {
    if (!selectedEnv.value) return
    await $fetch(`/api/lab/environments/${selectedEnv.value.id}/resources/sqs/${encodeURIComponent(url)}`, {
      method: 'DELETE', credentials: 'include',
    })
    await fetchAllResources()
    await fetchTopology()
  }

  const sendMessage = async (queueName: string, body: string) => {
    if (!selectedEnv.value) return
    return await $fetch(`/api/lab/environments/${selectedEnv.value.id}/sqs/${queueName}/send`, {
      method: 'POST', body: { body }, credentials: 'include',
    })
  }

  const receiveMessages = async (queueName: string) => {
    if (!selectedEnv.value) return []
    return await $fetch<any[]>(`/api/lab/environments/${selectedEnv.value.id}/sqs/${queueName}/receive`, { credentials: 'include' })
  }

  // ─── Lambda ───

  const createFunction = async (name: string, code: string, runtime: string = 'python3.12') => {
    if (!selectedEnv.value) return
    await $fetch(`/api/lab/environments/${selectedEnv.value.id}/lambda`, {
      method: 'POST', body: { name, code, runtime }, credentials: 'include',
    })
    await fetchAllResources()
    await fetchTopology()
  }

  const deleteFunction = async (name: string) => {
    if (!selectedEnv.value) return
    await $fetch(`/api/lab/environments/${selectedEnv.value.id}/resources/lambda/${name}`, {
      method: 'DELETE', credentials: 'include',
    })
    await fetchAllResources()
    await fetchTopology()
  }

  const invokeFunction = async (name: string, payload: Record<string, any> = {}) => {
    if (!selectedEnv.value) return null
    return await $fetch<{ status_code: number; payload: any }>(`/api/lab/environments/${selectedEnv.value.id}/lambda/${name}/invoke`, {
      method: 'POST', body: { payload }, credentials: 'include',
    })
  }

  // ─── DynamoDB ───

  const createTable = async (name: string, partitionKey: string, pkType: string = 'S', sortKey?: string, skType?: string) => {
    if (!selectedEnv.value) return
    await $fetch(`/api/lab/environments/${selectedEnv.value.id}/dynamodb`, {
      method: 'POST',
      body: { name, partition_key: partitionKey, partition_key_type: pkType, sort_key: sortKey, sort_key_type: skType },
      credentials: 'include',
    })
    await fetchAllResources()
    await fetchTopology()
  }

  const deleteTable = async (name: string) => {
    if (!selectedEnv.value) return
    await $fetch(`/api/lab/environments/${selectedEnv.value.id}/resources/dynamodb/${name}`, {
      method: 'DELETE', credentials: 'include',
    })
    await fetchAllResources()
    await fetchTopology()
  }

  const scanTable = async (table: string) => {
    if (!selectedEnv.value) return []
    return await $fetch<any[]>(`/api/lab/environments/${selectedEnv.value.id}/dynamodb/${table}/items`, { credentials: 'include' })
  }

  const putItem = async (table: string, item: Record<string, any>) => {
    if (!selectedEnv.value) return
    await $fetch(`/api/lab/environments/${selectedEnv.value.id}/dynamodb/${table}/items`, {
      method: 'POST', body: { item }, credentials: 'include',
    })
  }

  // ─── SNS ───

  const createTopic = async (name: string) => {
    if (!selectedEnv.value) return
    await $fetch(`/api/lab/environments/${selectedEnv.value.id}/resources/sns`, {
      method: 'POST', body: { name }, credentials: 'include',
    })
    await fetchAllResources()
    await fetchTopology()
  }

  const deleteTopic = async (arn: string) => {
    if (!selectedEnv.value) return
    await $fetch(`/api/lab/environments/${selectedEnv.value.id}/resources/sns/${encodeURIComponent(arn)}`, {
      method: 'DELETE', credentials: 'include',
    })
    await fetchAllResources()
    await fetchTopology()
  }

  const publishMessage = async (topicName: string, message: string) => {
    if (!selectedEnv.value) return
    return await $fetch(`/api/lab/environments/${selectedEnv.value.id}/sns/${topicName}/publish`, {
      method: 'POST', body: { message }, credentials: 'include',
    })
  }

  const subscribeTopic = async (topicName: string, protocol: string, endpoint: string) => {
    if (!selectedEnv.value) return
    return await $fetch(`/api/lab/environments/${selectedEnv.value.id}/sns/${topicName}/subscribe`, {
      method: 'POST', body: { protocol, endpoint }, credentials: 'include',
    })
  }

  // ─── Terraform ───

  const tfFiles = useState<Record<string, string>>('lab-tf-files', () => ({}))
  const tfOutput = useState<string>('lab-tf-output', () => '')
  const tfRunning = useState<boolean>('lab-tf-running', () => false)
  const tfTemplates = useState<{ id: string; label: string }[]>('lab-tf-templates', () => [])

  const fetchTfFiles = async () => {
    if (!selectedEnv.value) return
    try {
      tfFiles.value = await $fetch<Record<string, string>>(`/api/lab/environments/${selectedEnv.value.id}/terraform/files`, { credentials: 'include' })
    } catch {
      tfFiles.value = {}
    }
  }

  const saveTfFiles = async (files: Record<string, string>) => {
    if (!selectedEnv.value) return
    await $fetch(`/api/lab/environments/${selectedEnv.value.id}/terraform/files`, {
      method: 'PUT', body: { files }, credentials: 'include',
    })
    tfFiles.value = { ...tfFiles.value, ...files }
  }

  const deleteTfFile = async (filename: string) => {
    if (!selectedEnv.value) return
    await $fetch(`/api/lab/environments/${selectedEnv.value.id}/terraform/files/${filename}`, {
      method: 'DELETE', credentials: 'include',
    })
    const copy = { ...tfFiles.value }
    delete copy[filename]
    tfFiles.value = copy
  }

  const runTfCommand = async (command: 'init' | 'plan' | 'apply' | 'destroy') => {
    if (!selectedEnv.value) return null
    tfRunning.value = true
    tfOutput.value = `$ terraform ${command}\n실행 중...\n`
    try {
      const result = await $fetch<{ exit_code: number; stdout: string; stderr: string }>(
        `/api/lab/environments/${selectedEnv.value.id}/terraform/${command}`,
        { method: 'POST', credentials: 'include' },
      )
      tfOutput.value = `$ terraform ${command}\n${result.stdout}\n${result.stderr}`
      if (command === 'apply' || command === 'destroy') {
        await Promise.all([fetchTopology(), fetchAllResources()])
      }
      return result
    } catch (e: any) {
      tfOutput.value = `$ terraform ${command}\nError: ${e?.data?.detail || e?.message || '실행 실패'}`
      return null
    } finally {
      tfRunning.value = false
    }
  }

  const fetchTfTemplates = async () => {
    try {
      tfTemplates.value = await $fetch<{ id: string; label: string }[]>('/api/lab/terraform/templates', { credentials: 'include' })
    } catch {
      tfTemplates.value = []
    }
  }

  const loadTfTemplate = async (templateId: string) => {
    try {
      const data = await $fetch<{ code: string }>(`/api/lab/terraform/templates/${templateId}`, { credentials: 'include' })
      return data.code
    } catch {
      return null
    }
  }

  const deployFromFiles = async (files: Record<string, string>) => {
    if (!selectedEnv.value) return null
    tfRunning.value = true
    tfOutput.value = '$ terraform deploy (CI/CD)\n실행 중...\n'
    try {
      const result = await $fetch<{ stage: string; exit_code: number; stdout: string; stderr: string }>(
        `/api/lab/environments/${selectedEnv.value.id}/terraform/deploy`,
        { method: 'POST', body: { files }, credentials: 'include' },
      )
      tfOutput.value = `$ terraform deploy [${result.stage}]\n${result.stdout}\n${result.stderr}`
      await Promise.all([fetchTopology(), fetchAllResources()])
      return result
    } catch (e: any) {
      tfOutput.value = `$ terraform deploy\nError: ${e?.data?.detail || '배포 실패'}`
      return null
    } finally {
      tfRunning.value = false
    }
  }

  return {
    // State
    environments, selectedEnv, topology, members, loading, resourceLoading,
    s3Buckets, sqsQueues, lambdaFunctions, dynamoTables, snsTopics,
    // Environment
    fetchEnvironments, createEnvironment, selectEnvironment,
    startEnvironment, stopEnvironment, deleteEnvironment,
    // Members
    fetchMembers, inviteMember, removeMember,
    // Topology
    fetchTopology,
    // Resources
    fetchAllResources,
    // S3
    createBucket, deleteBucket, listObjects, uploadObject, deleteObject,
    // SQS
    createQueue, deleteQueue, sendMessage, receiveMessages,
    // Lambda
    createFunction, deleteFunction, invokeFunction,
    // DynamoDB
    createTable, deleteTable, scanTable, putItem,
    // SNS
    createTopic, deleteTopic, publishMessage, subscribeTopic,
    // Terraform
    tfFiles, tfOutput, tfRunning, tfTemplates,
    fetchTfFiles, saveTfFiles, deleteTfFile, runTfCommand,
    fetchTfTemplates, loadTfTemplate, deployFromFiles,
  }
}

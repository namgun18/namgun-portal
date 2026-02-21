export type GitView =
  | 'repo-list'
  | 'repo-detail'
  | 'file-view'
  | 'issue-list'
  | 'issue-detail'
  | 'pull-list'
  | 'pull-detail'
  | 'commit-list'

export interface RepoOwner {
  login: string
  avatar_url: string
}

export interface RepoSummary {
  id: number
  name: string
  full_name: string
  description: string
  owner: RepoOwner
  html_url: string
  default_branch: string
  stars_count: number
  forks_count: number
  open_issues_count: number
  updated_at: string
  language: string
  private: boolean
}

export interface RepoDetail extends RepoSummary {
  readme: string | null
  size: number
  created_at: string
}

export interface ContentEntry {
  name: string
  path: string
  type: 'file' | 'dir' | 'symlink' | 'submodule'
  size: number
  sha: string
}

export interface FileContent {
  name: string
  path: string
  size: number
  sha: string
  content: string | null
  too_large: boolean
}

export interface Branch {
  name: string
  commit_sha: string
  commit_message: string
}

export interface CommitEntry {
  sha: string
  message: string
  author: { name: string; email: string; date: string } | null
  committer: { name: string; email: string; date: string } | null
  html_url: string
}

export interface IssueUser {
  login: string
  avatar_url: string
}

export interface Label {
  id: number
  name: string
  color: string
}

export interface Issue {
  number: number
  title: string
  body: string
  state: string
  user: IssueUser | null
  labels: Label[]
  comments: number
  created_at: string
  updated_at: string
}

export interface IssueComment {
  id: number
  body: string
  user: IssueUser | null
  created_at: string
  updated_at: string
}

export interface PullRequest {
  number: number
  title: string
  body: string
  state: string
  user: IssueUser | null
  labels: Label[]
  head_branch: string
  base_branch: string
  mergeable: boolean | null
  merged: boolean
  comments: number
  created_at: string
  updated_at: string
}

// GitHub-style language colors
export const LANG_COLORS: Record<string, string> = {
  Python: '#3572A5', JavaScript: '#f1e05a', TypeScript: '#3178c6',
  Vue: '#41b883', Go: '#00ADD8', Rust: '#dea584', Java: '#b07219',
  'C++': '#f34b7d', C: '#555555', 'C#': '#178600', Ruby: '#701516',
  PHP: '#4F5D95', Swift: '#F05138', Kotlin: '#A97BFF', Dart: '#00B4AB',
  Shell: '#89e051', Bash: '#89e051', HTML: '#e34c26', CSS: '#563d7c',
  SCSS: '#c6538c', Lua: '#000080', Perl: '#0298c3', R: '#198CE7',
  Scala: '#c22d40', Haskell: '#5e5086', Elixir: '#6e4a7e',
  Dockerfile: '#384d54', Makefile: '#427819', Nix: '#7e7eff',
}

// Module-level singleton state
const currentView = ref<GitView>('repo-list')
const repos = ref<RepoSummary[]>([])
const reposTotal = ref(0)
const selectedRepo = ref<RepoDetail | null>(null)
const contents = ref<ContentEntry[]>([])
const fileContent = ref<FileContent | null>(null)
const branches = ref<Branch[]>([])
const currentBranch = ref('')
const currentPath = ref('')
const commits = ref<CommitEntry[]>([])
const latestCommit = ref<CommitEntry | null>(null)
const commitCount = ref(0)
const issues = ref<Issue[]>([])
const selectedIssue = ref<Issue | null>(null)
const issueComments = ref<IssueComment[]>([])
const pulls = ref<PullRequest[]>([])
const selectedPull = ref<PullRequest | null>(null)
const searchQuery = ref('')
const loading = ref(false)
const repoTab = ref<'code' | 'issues' | 'pulls' | 'commits'>('code')
const issueState = ref<'open' | 'closed'>('open')
const pullState = ref<'open' | 'closed'>('open')
const cloneUrl = ref('')

// Navigation history for back button
const navHistory = ref<GitView[]>([])

export function useGit() {
  function pushView(view: GitView) {
    navHistory.value.push(currentView.value)
    currentView.value = view
  }

  function goBack() {
    const prev = navHistory.value.pop()
    if (prev) {
      currentView.value = prev
    } else {
      currentView.value = 'repo-list'
    }
  }

  function resetToRepoList() {
    navHistory.value = []
    currentView.value = 'repo-list'
    selectedRepo.value = null
    fileContent.value = null
    selectedIssue.value = null
    selectedPull.value = null
    currentPath.value = ''
    repoTab.value = 'code'
  }

  // ─── Repos ───

  async function fetchRepos(page = 1) {
    loading.value = true
    try {
      const data = await $fetch<{ repos: RepoSummary[]; total: number }>('/api/git/repos', {
        params: { query: searchQuery.value, page, limit: 20, sort: 'updated' },
      })
      repos.value = data.repos
      reposTotal.value = data.total
    } catch (e: any) {
      console.error('fetchRepos error:', e)
      repos.value = []
      reposTotal.value = 0
    } finally {
      loading.value = false
    }
  }

  async function selectRepo(owner: string, repo: string) {
    loading.value = true
    try {
      selectedRepo.value = await $fetch<RepoDetail>(`/api/git/repos/${owner}/${repo}`)
      currentBranch.value = selectedRepo.value.default_branch
      currentPath.value = ''
      repoTab.value = 'code'
      cloneUrl.value = `https://git.namgun.or.kr/${owner}/${repo}.git`
      pushView('repo-detail')
      // Fetch contents, branches, and latest commit in parallel
      const [, , commitData] = await Promise.all([
        fetchContents(),
        fetchBranches(),
        $fetch<CommitEntry[]>(`/api/git/repos/${owner}/${repo}/commits`, {
          params: { sha: selectedRepo.value.default_branch, page: 1 },
        }).catch(() => [] as CommitEntry[]),
      ])
      latestCommit.value = commitData[0] || null
      commitCount.value = commitData.length >= 30 ? 30 : commitData.length // Approximate
    } catch (e: any) {
      console.error('selectRepo error:', e)
    } finally {
      loading.value = false
    }
  }

  // ─── Contents ───

  async function fetchContents(path = '') {
    if (!selectedRepo.value) return
    const { owner, name } = selectedRepo.value
    loading.value = true
    try {
      currentPath.value = path
      const params: Record<string, string> = {}
      if (path) params.path = path
      if (currentBranch.value) params.ref = currentBranch.value
      contents.value = await $fetch<ContentEntry[]>(
        `/api/git/repos/${owner.login}/${name}/contents`,
        { params },
      )
      // Sort: dirs first, then files
      contents.value.sort((a, b) => {
        if (a.type === 'dir' && b.type !== 'dir') return -1
        if (a.type !== 'dir' && b.type === 'dir') return 1
        return a.name.localeCompare(b.name)
      })
    } catch (e: any) {
      console.error('fetchContents error:', e)
      contents.value = []
    } finally {
      loading.value = false
    }
  }

  async function openFile(path: string) {
    if (!selectedRepo.value) return
    const { owner, name } = selectedRepo.value
    loading.value = true
    try {
      const params: Record<string, string> = { path }
      if (currentBranch.value) params.ref = currentBranch.value
      fileContent.value = await $fetch<FileContent>(
        `/api/git/repos/${owner.login}/${name}/file`,
        { params },
      )
      currentPath.value = path
      pushView('file-view')
    } catch (e: any) {
      console.error('openFile error:', e)
    } finally {
      loading.value = false
    }
  }

  function navigateToDir(path: string) {
    fetchContents(path)
  }

  // ─── Branches ───

  async function fetchBranches() {
    if (!selectedRepo.value) return
    const { owner, name } = selectedRepo.value
    try {
      branches.value = await $fetch<Branch[]>(
        `/api/git/repos/${owner.login}/${name}/branches`,
      )
    } catch (e: any) {
      console.error('fetchBranches error:', e)
      branches.value = []
    }
  }

  async function switchBranch(branch: string) {
    currentBranch.value = branch
    currentPath.value = ''
    if (currentView.value === 'file-view') {
      currentView.value = 'repo-detail'
      navHistory.value = navHistory.value.filter((v) => v !== 'file-view')
    }
    await fetchContents()
  }

  // ─── Commits ───

  async function fetchCommits(page = 1) {
    if (!selectedRepo.value) return
    const { owner, name } = selectedRepo.value
    loading.value = true
    try {
      commits.value = await $fetch<CommitEntry[]>(
        `/api/git/repos/${owner.login}/${name}/commits`,
        { params: { sha: currentBranch.value || undefined, page } },
      )
    } catch (e: any) {
      console.error('fetchCommits error:', e)
      commits.value = []
    } finally {
      loading.value = false
    }
  }

  // ─── Issues ───

  async function fetchIssues(page = 1) {
    if (!selectedRepo.value) return
    const { owner, name } = selectedRepo.value
    loading.value = true
    try {
      issues.value = await $fetch<Issue[]>(
        `/api/git/repos/${owner.login}/${name}/issues`,
        { params: { state: issueState.value, page } },
      )
    } catch (e: any) {
      console.error('fetchIssues error:', e)
      issues.value = []
    } finally {
      loading.value = false
    }
  }

  async function selectIssue(index: number) {
    if (!selectedRepo.value) return
    const { owner, name } = selectedRepo.value
    loading.value = true
    try {
      selectedIssue.value = await $fetch<Issue>(
        `/api/git/repos/${owner.login}/${name}/issues/${index}`,
      )
      issueComments.value = await $fetch<IssueComment[]>(
        `/api/git/repos/${owner.login}/${name}/issues/${index}/comments`,
      )
      pushView('issue-detail')
    } catch (e: any) {
      console.error('selectIssue error:', e)
    } finally {
      loading.value = false
    }
  }

  async function createIssue(title: string, body: string) {
    if (!selectedRepo.value) return
    const { owner, name } = selectedRepo.value
    await $fetch(`/api/git/repos/${owner.login}/${name}/issues`, {
      method: 'POST',
      body: { title, body },
    })
    await fetchIssues()
  }

  async function addIssueComment(index: number, body: string) {
    if (!selectedRepo.value) return
    const { owner, name } = selectedRepo.value
    const comment = await $fetch<IssueComment>(
      `/api/git/repos/${owner.login}/${name}/issues/${index}/comments`,
      { method: 'POST', body: { body } },
    )
    issueComments.value = [...issueComments.value, comment]
  }

  // ─── Pull Requests ───

  async function fetchPulls(page = 1) {
    if (!selectedRepo.value) return
    const { owner, name } = selectedRepo.value
    loading.value = true
    try {
      pulls.value = await $fetch<PullRequest[]>(
        `/api/git/repos/${owner.login}/${name}/pulls`,
        { params: { state: pullState.value, page } },
      )
    } catch (e: any) {
      console.error('fetchPulls error:', e)
      pulls.value = []
    } finally {
      loading.value = false
    }
  }

  async function selectPull(index: number) {
    if (!selectedRepo.value) return
    const { owner, name } = selectedRepo.value
    loading.value = true
    try {
      selectedPull.value = await $fetch<PullRequest>(
        `/api/git/repos/${owner.login}/${name}/pulls/${index}`,
      )
      pushView('pull-detail')
    } catch (e: any) {
      console.error('selectPull error:', e)
    } finally {
      loading.value = false
    }
  }

  // ─── Tab switching ───

  async function switchTab(tab: 'code' | 'issues' | 'pulls' | 'commits') {
    repoTab.value = tab
    if (tab === 'code') {
      currentView.value = 'repo-detail'
      navHistory.value = ['repo-list']
      await fetchContents(currentPath.value)
    } else if (tab === 'issues') {
      currentView.value = 'issue-list'
      navHistory.value = ['repo-list', 'repo-detail']
      await fetchIssues()
    } else if (tab === 'pulls') {
      currentView.value = 'pull-list'
      navHistory.value = ['repo-list', 'repo-detail']
      await fetchPulls()
    } else if (tab === 'commits') {
      currentView.value = 'commit-list'
      navHistory.value = ['repo-list', 'repo-detail']
      await fetchCommits()
    }
  }

  return {
    // State
    currentView: readonly(currentView),
    repos: readonly(repos),
    reposTotal: readonly(reposTotal),
    selectedRepo: readonly(selectedRepo),
    contents: readonly(contents),
    fileContent: readonly(fileContent),
    branches: readonly(branches),
    currentBranch: readonly(currentBranch),
    currentPath: readonly(currentPath),
    commits: readonly(commits),
    latestCommit: readonly(latestCommit),
    commitCount: readonly(commitCount),
    cloneUrl: readonly(cloneUrl),
    issues: readonly(issues),
    selectedIssue: readonly(selectedIssue),
    issueComments: readonly(issueComments),
    pulls: readonly(pulls),
    selectedPull: readonly(selectedPull),
    loading: readonly(loading),
    repoTab,
    searchQuery,
    issueState,
    pullState,
    // Actions
    fetchRepos,
    selectRepo,
    fetchContents,
    openFile,
    navigateToDir,
    fetchBranches,
    switchBranch,
    fetchCommits,
    fetchIssues,
    selectIssue,
    createIssue,
    addIssueComment,
    fetchPulls,
    selectPull,
    switchTab,
    goBack,
    resetToRepoList,
  }
}

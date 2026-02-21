<script setup lang="ts">
import GitCommandBar from '~/components/git/GitCommandBar.vue'
import GitRepoList from '~/components/git/GitRepoList.vue'
import GitRepoDetail from '~/components/git/GitRepoDetail.vue'
import GitFileViewer from '~/components/git/GitFileViewer.vue'
import GitCommitList from '~/components/git/GitCommitList.vue'
import GitIssueList from '~/components/git/GitIssueList.vue'
import GitIssueDetail from '~/components/git/GitIssueDetail.vue'
import GitCreateIssueModal from '~/components/git/GitCreateIssueModal.vue'
import GitPullList from '~/components/git/GitPullList.vue'
import GitPullDetail from '~/components/git/GitPullDetail.vue'

definePageMeta({ layout: 'default' })

const {
  currentView,
  fetchRepos,
  resetToRepoList,
} = useGit()

const showCreateIssue = ref(false)

onMounted(async () => {
  resetToRepoList()
  await fetchRepos()
})
</script>

<template>
  <div class="flex h-[calc(100vh-3.5rem)] overflow-hidden">
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Command bar -->
      <GitCommandBar />

      <!-- Content -->
      <GitRepoList v-if="currentView === 'repo-list'" />
      <GitRepoDetail v-else-if="currentView === 'repo-detail'" />
      <GitFileViewer v-else-if="currentView === 'file-view'" />
      <GitCommitList v-else-if="currentView === 'commit-list'" />
      <GitIssueList v-else-if="currentView === 'issue-list'" @create-issue="showCreateIssue = true" />
      <GitIssueDetail v-else-if="currentView === 'issue-detail'" />
      <GitPullList v-else-if="currentView === 'pull-list'" />
      <GitPullDetail v-else-if="currentView === 'pull-detail'" />
    </div>

    <!-- Create issue modal -->
    <GitCreateIssueModal
      v-if="showCreateIssue"
      @close="showCreateIssue = false"
    />
  </div>
</template>

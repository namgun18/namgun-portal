"""Pydantic models for Git API responses."""

from pydantic import BaseModel


class RepoOwner(BaseModel):
    login: str
    avatar_url: str = ""


class RepoSummary(BaseModel):
    id: int
    name: str
    full_name: str
    description: str = ""
    owner: RepoOwner
    html_url: str
    default_branch: str = "main"
    stars_count: int = 0
    forks_count: int = 0
    open_issues_count: int = 0
    updated_at: str = ""
    language: str = ""
    private: bool = False


class RepoListResponse(BaseModel):
    repos: list[RepoSummary]
    total: int


class RepoDetail(RepoSummary):
    readme: str | None = None
    size: int = 0
    created_at: str = ""


class ContentEntry(BaseModel):
    name: str
    path: str
    type: str  # "file" | "dir" | "symlink" | "submodule"
    size: int = 0
    sha: str = ""


class FileContent(BaseModel):
    name: str
    path: str
    size: int = 0
    sha: str = ""
    content: str | None = None
    too_large: bool = False
    encoding: str = ""


class Branch(BaseModel):
    name: str
    commit_sha: str = ""
    commit_message: str = ""


class CommitUser(BaseModel):
    name: str = ""
    email: str = ""
    date: str = ""


class Commit(BaseModel):
    sha: str
    message: str = ""
    author: CommitUser | None = None
    committer: CommitUser | None = None
    html_url: str = ""


class IssueUser(BaseModel):
    login: str
    avatar_url: str = ""


class Label(BaseModel):
    id: int
    name: str
    color: str = ""


class Issue(BaseModel):
    number: int
    title: str
    body: str = ""
    state: str = "open"
    user: IssueUser | None = None
    labels: list[Label] = []
    comments: int = 0
    created_at: str = ""
    updated_at: str = ""


class IssueComment(BaseModel):
    id: int
    body: str = ""
    user: IssueUser | None = None
    created_at: str = ""
    updated_at: str = ""


class CreateIssueRequest(BaseModel):
    title: str
    body: str = ""


class CreateCommentRequest(BaseModel):
    body: str


class RecentCommit(BaseModel):
    repo_full_name: str
    repo_name: str
    sha: str
    message: str = ""
    author_name: str = ""
    author_date: str = ""


class PullRequest(BaseModel):
    number: int
    title: str
    body: str = ""
    state: str = "open"
    user: IssueUser | None = None
    labels: list[Label] = []
    head_branch: str = ""
    base_branch: str = ""
    mergeable: bool | None = None
    merged: bool = False
    comments: int = 0
    created_at: str = ""
    updated_at: str = ""

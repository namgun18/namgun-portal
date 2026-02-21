"""Git (Gitea) API router."""

import asyncio
import time

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.deps import get_current_user
from app.db.models import User
from app.git import gitea
from app.git.schemas import (
    Branch,
    Commit,
    CommitUser,
    ContentEntry,
    CreateCommentRequest,
    CreateIssueRequest,
    FileContent,
    Issue,
    IssueComment,
    IssueUser,
    Label,
    PullRequest,
    RecentCommit,
    RepoDetail,
    RepoListResponse,
    RepoOwner,
    RepoSummary,
)

router = APIRouter(prefix="/api/git", tags=["git"])


def _map_repo_summary(r: dict) -> RepoSummary:
    owner = r.get("owner", {})
    return RepoSummary(
        id=r.get("id", 0),
        name=r.get("name", ""),
        full_name=r.get("full_name", ""),
        description=r.get("description") or "",
        owner=RepoOwner(
            login=owner.get("login", ""),
            avatar_url=owner.get("avatar_url", ""),
        ),
        html_url=r.get("html_url", ""),
        default_branch=r.get("default_branch", "main"),
        stars_count=r.get("stars_count", 0),
        forks_count=r.get("forks_count", 0),
        open_issues_count=r.get("open_issues_count", 0),
        updated_at=r.get("updated_at", ""),
        language=r.get("language") or "",
        private=r.get("private", False),
    )


def _map_issue_user(u: dict | None) -> IssueUser | None:
    if not u:
        return None
    return IssueUser(login=u.get("login", ""), avatar_url=u.get("avatar_url", ""))


def _map_labels(labels: list[dict] | None) -> list[Label]:
    if not labels:
        return []
    return [
        Label(id=l.get("id", 0), name=l.get("name", ""), color=l.get("color", ""))
        for l in labels
    ]


# ─── Recent Commits (cross-repo, cached) ───

_recent_commits_cache: list[RecentCommit] = []
_recent_commits_ts: float = 0
_RECENT_COMMITS_TTL = 120  # seconds


async def _refresh_recent_commits() -> list[RecentCommit]:
    """Fetch recent commits from top 5 repos in parallel."""
    try:
        repos, _ = await gitea.search_repos("", 1, 5, "updated")
    except Exception:
        return []

    async def _fetch(r: dict) -> list[RecentCommit]:
        owner = r.get("owner", {}).get("login", "")
        name = r.get("name", "")
        full_name = r.get("full_name", "")
        if not owner or not name:
            return []
        try:
            commits = await gitea.get_commits(owner, name, page=1)
            out = []
            for c in commits[:3]:
                cd = c.get("commit", {})
                ad = cd.get("author", {})
                out.append(RecentCommit(
                    repo_full_name=full_name, repo_name=name,
                    sha=c.get("sha", ""), message=cd.get("message", ""),
                    author_name=ad.get("name", ""), author_date=ad.get("date", ""),
                ))
            return out
        except Exception:
            return []

    results = await asyncio.gather(*[_fetch(r) for r in repos])
    all_commits = [c for batch in results for c in batch]
    all_commits.sort(key=lambda c: c.author_date, reverse=True)
    return all_commits[:20]


@router.get("/recent-commits", response_model=list[RecentCommit])
async def recent_commits(
    limit: int = Query(5, ge=1, le=20),
    user: User = Depends(get_current_user),
):
    global _recent_commits_cache, _recent_commits_ts
    now = time.monotonic()
    if now - _recent_commits_ts > _RECENT_COMMITS_TTL or not _recent_commits_cache:
        _recent_commits_cache = await _refresh_recent_commits()
        _recent_commits_ts = now
    return _recent_commits_cache[:limit]


# ─── Repositories ───


@router.get("/repos", response_model=RepoListResponse)
async def list_repos(
    query: str = "",
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    sort: str = "updated",
    user: User = Depends(get_current_user),
):
    repos, total = await gitea.search_repos(query, page, limit, sort)
    return RepoListResponse(
        repos=[_map_repo_summary(r) for r in repos],
        total=total,
    )


@router.get("/repos/{owner}/{repo}", response_model=RepoDetail)
async def get_repo(
    owner: str,
    repo: str,
    user: User = Depends(get_current_user),
):
    try:
        data = await gitea.get_repo(owner, repo)
    except Exception:
        raise HTTPException(status_code=404, detail="Repository not found")
    readme = await gitea.get_readme(owner, repo)
    o = data.get("owner", {})
    return RepoDetail(
        id=data.get("id", 0),
        name=data.get("name", ""),
        full_name=data.get("full_name", ""),
        description=data.get("description") or "",
        owner=RepoOwner(
            login=o.get("login", ""),
            avatar_url=o.get("avatar_url", ""),
        ),
        html_url=data.get("html_url", ""),
        default_branch=data.get("default_branch", "main"),
        stars_count=data.get("stars_count", 0),
        forks_count=data.get("forks_count", 0),
        open_issues_count=data.get("open_issues_count", 0),
        updated_at=data.get("updated_at", ""),
        language=data.get("language") or "",
        private=data.get("private", False),
        readme=readme,
        size=data.get("size", 0),
        created_at=data.get("created_at", ""),
    )


# ─── Contents ───


@router.get("/repos/{owner}/{repo}/contents", response_model=list[ContentEntry])
async def list_contents(
    owner: str,
    repo: str,
    path: str = "",
    ref: str | None = None,
    user: User = Depends(get_current_user),
):
    items = await gitea.get_contents(owner, repo, path, ref)
    return [
        ContentEntry(
            name=i.get("name", ""),
            path=i.get("path", ""),
            type=i.get("type", "file"),
            size=i.get("size", 0),
            sha=i.get("sha", ""),
        )
        for i in items
    ]


@router.get("/repos/{owner}/{repo}/file", response_model=FileContent)
async def get_file(
    owner: str,
    repo: str,
    path: str,
    ref: str | None = None,
    user: User = Depends(get_current_user),
):
    data = await gitea.get_file(owner, repo, path, ref)
    if not data:
        raise HTTPException(status_code=404, detail="File not found")
    return FileContent(
        name=data.get("name", ""),
        path=data.get("path", ""),
        size=data.get("size", 0),
        sha=data.get("sha", ""),
        content=data.get("decoded_content"),
        too_large=data.get("too_large", False),
        encoding=data.get("encoding", ""),
    )


# ─── Branches ───


@router.get("/repos/{owner}/{repo}/branches", response_model=list[Branch])
async def list_branches(
    owner: str,
    repo: str,
    user: User = Depends(get_current_user),
):
    branches = await gitea.get_branches(owner, repo)
    return [
        Branch(
            name=b.get("name", ""),
            commit_sha=b.get("commit", {}).get("id", ""),
            commit_message=b.get("commit", {}).get("message", ""),
        )
        for b in branches
    ]


# ─── Commits ───


@router.get("/repos/{owner}/{repo}/commits", response_model=list[Commit])
async def list_commits(
    owner: str,
    repo: str,
    sha: str | None = None,
    page: int = Query(1, ge=1),
    user: User = Depends(get_current_user),
):
    commits = await gitea.get_commits(owner, repo, sha, page)
    result = []
    for c in commits:
        commit_data = c.get("commit", {})
        author_data = commit_data.get("author", {})
        committer_data = commit_data.get("committer", {})
        result.append(
            Commit(
                sha=c.get("sha", ""),
                message=commit_data.get("message", ""),
                author=CommitUser(
                    name=author_data.get("name", ""),
                    email=author_data.get("email", ""),
                    date=author_data.get("date", ""),
                ),
                committer=CommitUser(
                    name=committer_data.get("name", ""),
                    email=committer_data.get("email", ""),
                    date=committer_data.get("date", ""),
                ),
                html_url=c.get("html_url", ""),
            )
        )
    return result


# ─── Issues ───


@router.get("/repos/{owner}/{repo}/issues", response_model=list[Issue])
async def list_issues(
    owner: str,
    repo: str,
    state: str = "open",
    page: int = Query(1, ge=1),
    user: User = Depends(get_current_user),
):
    issues = await gitea.get_issues(owner, repo, state, page)
    return [
        Issue(
            number=i.get("number", 0),
            title=i.get("title", ""),
            body=i.get("body") or "",
            state=i.get("state", "open"),
            user=_map_issue_user(i.get("user")),
            labels=_map_labels(i.get("labels")),
            comments=i.get("comments", 0),
            created_at=i.get("created_at", ""),
            updated_at=i.get("updated_at", ""),
        )
        for i in issues
    ]


@router.post("/repos/{owner}/{repo}/issues", response_model=Issue)
async def create_issue(
    owner: str,
    repo: str,
    body: CreateIssueRequest,
    user: User = Depends(get_current_user),
):
    data = await gitea.create_issue(owner, repo, body.title, body.body)
    return Issue(
        number=data.get("number", 0),
        title=data.get("title", ""),
        body=data.get("body") or "",
        state=data.get("state", "open"),
        user=_map_issue_user(data.get("user")),
        labels=_map_labels(data.get("labels")),
        comments=data.get("comments", 0),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
    )


@router.get("/repos/{owner}/{repo}/issues/{index}", response_model=Issue)
async def get_issue(
    owner: str,
    repo: str,
    index: int,
    user: User = Depends(get_current_user),
):
    try:
        data = await gitea.get_issue(owner, repo, index)
    except Exception:
        raise HTTPException(status_code=404, detail="Issue not found")
    return Issue(
        number=data.get("number", 0),
        title=data.get("title", ""),
        body=data.get("body") or "",
        state=data.get("state", "open"),
        user=_map_issue_user(data.get("user")),
        labels=_map_labels(data.get("labels")),
        comments=data.get("comments", 0),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
    )


@router.get(
    "/repos/{owner}/{repo}/issues/{index}/comments",
    response_model=list[IssueComment],
)
async def list_issue_comments(
    owner: str,
    repo: str,
    index: int,
    user: User = Depends(get_current_user),
):
    comments = await gitea.get_issue_comments(owner, repo, index)
    return [
        IssueComment(
            id=c.get("id", 0),
            body=c.get("body") or "",
            user=_map_issue_user(c.get("user")),
            created_at=c.get("created_at", ""),
            updated_at=c.get("updated_at", ""),
        )
        for c in comments
    ]


@router.post(
    "/repos/{owner}/{repo}/issues/{index}/comments",
    response_model=IssueComment,
)
async def add_issue_comment(
    owner: str,
    repo: str,
    index: int,
    body: CreateCommentRequest,
    user: User = Depends(get_current_user),
):
    data = await gitea.create_issue_comment(owner, repo, index, body.body)
    return IssueComment(
        id=data.get("id", 0),
        body=data.get("body") or "",
        user=_map_issue_user(data.get("user")),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
    )


# ─── Pull Requests ───


@router.get("/repos/{owner}/{repo}/pulls", response_model=list[PullRequest])
async def list_pulls(
    owner: str,
    repo: str,
    state: str = "open",
    page: int = Query(1, ge=1),
    user: User = Depends(get_current_user),
):
    pulls = await gitea.get_pulls(owner, repo, state, page)
    return [
        PullRequest(
            number=p.get("number", 0),
            title=p.get("title", ""),
            body=p.get("body") or "",
            state=p.get("state", "open"),
            user=_map_issue_user(p.get("user")),
            labels=_map_labels(p.get("labels")),
            head_branch=p.get("head", {}).get("label", ""),
            base_branch=p.get("base", {}).get("label", ""),
            mergeable=p.get("mergeable"),
            merged=p.get("merged", False),
            comments=p.get("comments", 0),
            created_at=p.get("created_at", ""),
            updated_at=p.get("updated_at", ""),
        )
        for p in pulls
    ]


@router.get("/repos/{owner}/{repo}/pulls/{index}", response_model=PullRequest)
async def get_pull(
    owner: str,
    repo: str,
    index: int,
    user: User = Depends(get_current_user),
):
    try:
        data = await gitea.get_pull(owner, repo, index)
    except Exception:
        raise HTTPException(status_code=404, detail="Pull request not found")
    return PullRequest(
        number=data.get("number", 0),
        title=data.get("title", ""),
        body=data.get("body") or "",
        state=data.get("state", "open"),
        user=_map_issue_user(data.get("user")),
        labels=_map_labels(data.get("labels")),
        head_branch=data.get("head", {}).get("label", ""),
        base_branch=data.get("base", {}).get("label", ""),
        mergeable=data.get("mergeable"),
        merged=data.get("merged", False),
        comments=data.get("comments", 0),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
    )

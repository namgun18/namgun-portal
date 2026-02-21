"""Gitea API client with httpx singleton."""

import base64

import httpx

from app.config import get_settings

settings = get_settings()

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=f"{settings.gitea_url}/api/v1",
            headers={"Authorization": f"token {settings.gitea_token}"},
            timeout=15.0,
        )
    return _client


async def _get(path: str, params: dict | None = None) -> dict | list:
    client = _get_client()
    resp = await client.get(path, params=params)
    resp.raise_for_status()
    return resp.json()


async def _post(path: str, json: dict | None = None) -> dict:
    client = _get_client()
    resp = await client.post(path, json=json)
    resp.raise_for_status()
    return resp.json()


# ─── Repositories ───


async def search_repos(
    query: str = "",
    page: int = 1,
    limit: int = 20,
    sort: str = "updated",
) -> tuple[list[dict], int]:
    """Search repositories. Returns (repos, total_count)."""
    params: dict = {"page": page, "limit": limit, "sort": sort}
    if query:
        params["q"] = query
    client = _get_client()
    resp = await client.get("/repos/search", params=params)
    resp.raise_for_status()
    total = int(resp.headers.get("x-total-count", 0))
    return resp.json().get("data", []), total


async def get_repo(owner: str, repo: str) -> dict:
    return await _get(f"/repos/{owner}/{repo}")


async def get_readme(owner: str, repo: str, ref: str | None = None) -> str | None:
    """Get decoded README content via raw endpoint."""
    client = _get_client()
    params = {}
    if ref:
        params["ref"] = ref
    for name in ("README.md", "readme.md", "README", "README.txt"):
        try:
            resp = await client.get(
                f"/repos/{owner}/{repo}/raw/{name}", params=params
            )
            if resp.status_code == 200:
                return resp.text
        except httpx.HTTPError:
            continue
    return None


# ─── Contents ───


async def get_contents(
    owner: str, repo: str, path: str = "", ref: str | None = None
) -> list[dict]:
    """Get directory listing."""
    params = {}
    if ref:
        params["ref"] = ref
    try:
        data = await _get(f"/repos/{owner}/{repo}/contents/{path}", params)
        if isinstance(data, list):
            return data
        return [data]
    except httpx.HTTPStatusError:
        return []


async def get_file(
    owner: str, repo: str, path: str, ref: str | None = None
) -> dict | None:
    """Get file content, decoded from base64."""
    params = {}
    if ref:
        params["ref"] = ref
    try:
        data = await _get(f"/repos/{owner}/{repo}/contents/{path}", params)
        if isinstance(data, list):
            return None
        content = data.get("content", "")
        size = data.get("size", 0)
        if content and size <= 1_048_576:  # 1MB
            data["decoded_content"] = base64.b64decode(content).decode(
                "utf-8", errors="replace"
            )
        elif size > 1_048_576:
            data["decoded_content"] = None
            data["too_large"] = True
        data.pop("content", None)
        return data
    except httpx.HTTPStatusError:
        return None


# ─── Branches ───


async def get_branches(owner: str, repo: str) -> list[dict]:
    return await _get(f"/repos/{owner}/{repo}/branches")


# ─── Commits ───


async def get_commits(
    owner: str, repo: str, sha: str | None = None, page: int = 1
) -> list[dict]:
    params: dict = {"page": page, "limit": 30}
    if sha:
        params["sha"] = sha
    return await _get(f"/repos/{owner}/{repo}/commits", params)


# ─── Issues ───


async def get_issues(
    owner: str, repo: str, state: str = "open", page: int = 1
) -> list[dict]:
    params = {"state": state, "page": page, "limit": 20, "type": "issues"}
    return await _get(f"/repos/{owner}/{repo}/issues", params)


async def get_issue(owner: str, repo: str, index: int) -> dict:
    return await _get(f"/repos/{owner}/{repo}/issues/{index}")


async def create_issue(owner: str, repo: str, title: str, body: str = "") -> dict:
    return await _post(
        f"/repos/{owner}/{repo}/issues", json={"title": title, "body": body}
    )


async def get_issue_comments(owner: str, repo: str, index: int) -> list[dict]:
    return await _get(f"/repos/{owner}/{repo}/issues/{index}/comments")


async def create_issue_comment(
    owner: str, repo: str, index: int, body: str
) -> dict:
    return await _post(
        f"/repos/{owner}/{repo}/issues/{index}/comments", json={"body": body}
    )


# ─── Pull Requests ───


async def get_pulls(
    owner: str, repo: str, state: str = "open", page: int = 1
) -> list[dict]:
    params = {"state": state, "page": page, "limit": 20}
    return await _get(f"/repos/{owner}/{repo}/pulls", params)


async def get_pull(owner: str, repo: str, index: int) -> dict:
    return await _get(f"/repos/{owner}/{repo}/pulls/{index}")

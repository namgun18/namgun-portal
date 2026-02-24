"""Analytics response schemas."""

from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    total_visits: int
    unique_ips: int
    authenticated_visits: int
    unauthenticated_visits: int
    avg_response_time_ms: int


class DailyVisit(BaseModel):
    date: str
    total: int
    authenticated: int
    unauthenticated: int


class TopPage(BaseModel):
    path: str
    count: int


class CountryStats(BaseModel):
    country_code: str | None
    country_name: str | None
    count: int


class ServiceUsage(BaseModel):
    service: str
    count: int


class ActiveUser(BaseModel):
    user_id: str
    username: str
    display_name: str | None
    path: str
    ip_address: str
    country_code: str | None
    last_seen: str


class RecentLogin(BaseModel):
    user_id: str
    username: str
    display_name: str | None
    ip_address: str
    country_code: str | None
    country_name: str | None
    login_at: str


class AccessLogEntry(BaseModel):
    id: str
    ip_address: str
    method: str
    path: str
    status_code: int
    response_time_ms: int
    browser: str | None
    os: str | None
    device: str | None
    country_code: str | None
    country_name: str | None
    user_id: str | None
    username: str | None
    service: str | None
    created_at: str


class AccessLogPage(BaseModel):
    logs: list[AccessLogEntry]
    total: int
    page: int
    limit: int


class GitActivityItem(BaseModel):
    repo_name: str
    repo_full_name: str
    event_type: str  # push, issue, pull_request
    title: str
    user: str
    created_at: str


class GitStats(BaseModel):
    total_repos: int
    total_users: int
    total_issues: int
    total_pulls: int

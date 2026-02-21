"""Pydantic schemas for lab API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


# ── Environment ──

class EnvironmentCreate(BaseModel):
    name: str


class EnvironmentOut(BaseModel):
    id: str
    owner_id: str
    name: str
    container_name: str
    status: str
    created_at: datetime
    role: str = "owner"

    class Config:
        from_attributes = True


# ── Members ──

class MemberInvite(BaseModel):
    username: str


class MemberOut(BaseModel):
    id: str
    user_id: str
    username: str
    display_name: str | None
    role: str
    invited_at: datetime


# ── Resources ──

class ResourceCreate(BaseModel):
    name: str
    config: dict[str, Any] = {}


class ResourceOut(BaseModel):
    id: str
    name: str
    service: str
    details: dict[str, Any] = {}


# ── Topology ──

class TopologyNode(BaseModel):
    id: str
    label: str
    service: str
    details: dict[str, Any] = {}


class TopologyEdge(BaseModel):
    source: str
    target: str
    label: str = ""


class TopologyOut(BaseModel):
    nodes: list[TopologyNode]
    edges: list[TopologyEdge]


# ── S3 ──

class S3ObjectOut(BaseModel):
    key: str
    size: int = 0
    last_modified: str = ""


# ── SQS ──

class SqsSend(BaseModel):
    body: str


class SqsMessageOut(BaseModel):
    message_id: str
    receipt_handle: str
    body: str


# ── Lambda ──

class LambdaCreate(BaseModel):
    name: str
    code: str
    runtime: str = "python3.12"


class LambdaInvoke(BaseModel):
    payload: dict[str, Any] = {}


class LambdaResult(BaseModel):
    status_code: int
    payload: Any


# ── DynamoDB ──

class DynamoTableCreate(BaseModel):
    name: str
    partition_key: str
    partition_key_type: str = "S"
    sort_key: str | None = None
    sort_key_type: str = "S"


class DynamoItemPut(BaseModel):
    item: dict[str, Any]


# ── SNS ──

class SnsPublish(BaseModel):
    message: str


class SnsSubscribe(BaseModel):
    protocol: str  # "sqs", "email", "http", etc.
    endpoint: str


# ── Terraform ──

class TerraformFiles(BaseModel):
    files: dict[str, str]


class TerraformResult(BaseModel):
    exit_code: int
    stdout: str
    stderr: str


class TerraformTemplate(BaseModel):
    id: str
    label: str

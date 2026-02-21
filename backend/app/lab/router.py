"""Lab environment API router."""

from __future__ import annotations

import asyncio
from functools import partial

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db.models import LabEnvironment, LabMember, User
from app.db.session import get_db
from app.lab import aws_client as aws
from app.lab import docker_manager as dm
from app.lab import terraform_manager as tf
from app.lab.schemas import (
    DynamoItemPut,
    DynamoTableCreate,
    EnvironmentCreate,
    EnvironmentOut,
    LambdaCreate,
    LambdaInvoke,
    LambdaResult,
    MemberInvite,
    MemberOut,
    ResourceCreate,
    S3ObjectOut,
    SnsPublish,
    SnsSubscribe,
    SqsMessageOut,
    SqsSend,
    TerraformFiles,
    TerraformResult,
    TerraformTemplate,
    TopologyOut,
)

router = APIRouter(prefix="/api/lab", tags=["lab"])

MAX_ENVS_PER_USER = 5


def _run(fn, *args, **kwargs):
    """Run a sync function in the default executor."""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, partial(fn, *args, **kwargs))


async def _get_env_with_access(
    env_id: str, user: User, db: AsyncSession, require_owner: bool = False,
) -> LabEnvironment:
    """Fetch environment and verify user has access."""
    env = await db.get(LabEnvironment, env_id)
    if not env:
        raise HTTPException(status_code=404, detail="환경을 찾을 수 없습니다")

    if env.owner_id == user.id:
        return env

    if require_owner:
        raise HTTPException(status_code=403, detail="소유자만 수행할 수 있습니다")

    # Check membership
    stmt = select(LabMember).where(
        LabMember.environment_id == env_id,
        LabMember.user_id == user.id,
    )
    member = (await db.execute(stmt)).scalar_one_or_none()
    if not member and not user.is_admin:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    return env


def _env_to_out(env: LabEnvironment, role: str = "owner") -> EnvironmentOut:
    return EnvironmentOut(
        id=env.id,
        owner_id=env.owner_id,
        name=env.name,
        container_name=env.container_name,
        status=env.status,
        created_at=env.created_at,
        role=role,
    )


# ─── Environment CRUD ───

@router.get("/environments", response_model=list[EnvironmentOut])
async def list_environments(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Owned
    stmt = select(LabEnvironment).where(LabEnvironment.owner_id == user.id).order_by(LabEnvironment.created_at.desc())
    owned = list((await db.execute(stmt)).scalars().all())

    # Shared (member)
    stmt = (
        select(LabEnvironment)
        .join(LabMember, LabMember.environment_id == LabEnvironment.id)
        .where(LabMember.user_id == user.id, LabMember.role == "member")
        .order_by(LabEnvironment.created_at.desc())
    )
    shared = list((await db.execute(stmt)).scalars().all())

    result = [_env_to_out(e, "owner") for e in owned]
    result += [_env_to_out(e, "member") for e in shared]
    return result


@router.post("/environments", response_model=EnvironmentOut, status_code=201)
async def create_environment(
    body: EnvironmentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check limit
    if not user.is_admin:
        stmt = select(LabEnvironment).where(LabEnvironment.owner_id == user.id)
        count = len((await db.execute(stmt)).scalars().all())
        if count >= MAX_ENVS_PER_USER:
            raise HTTPException(status_code=400, detail=f"환경은 최대 {MAX_ENVS_PER_USER}개까지 생성 가능합니다")

    env = LabEnvironment(owner_id=user.id, name=body.name, container_name="tmp")
    db.add(env)
    await db.flush()

    # Create container
    env.container_name = f"lab-{env.id[:8]}"
    try:
        info = await _run(dm.create_container, env.id)
        env.container_id = info["container_id"]
        env.status = "running"
    except Exception as e:
        env.status = "error"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"컨테이너 생성 실패: {e}")

    # Add owner as member
    member = LabMember(environment_id=env.id, user_id=user.id, role="owner")
    db.add(member)
    await db.commit()
    await db.refresh(env)
    return _env_to_out(env)


@router.get("/environments/{env_id}", response_model=EnvironmentOut)
async def get_environment(
    env_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    # Sync status from Docker
    actual = await _run(dm.get_status, env.container_name)
    if actual == "running":
        env.status = "running"
    elif actual == "removed":
        env.status = "stopped"
    elif actual in ("exited", "created"):
        env.status = "stopped"
    else:
        env.status = actual
    await db.commit()

    role = "owner" if env.owner_id == user.id else "member"
    return _env_to_out(env, role)


@router.post("/environments/{env_id}/start")
async def start_environment(
    env_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)

    actual = await _run(dm.get_status, env.container_name)
    if actual == "running":
        env.status = "running"
        await db.commit()
        return {"status": "running"}

    if actual == "removed":
        # Re-create — clear stale terraform state
        tf.clear_state(env_id)
        try:
            info = await _run(dm.create_container, env.id)
            env.container_id = info["container_id"]
            env.status = "running"
        except Exception as e:
            env.status = "error"
            await db.commit()
            raise HTTPException(status_code=500, detail=str(e))
    else:
        try:
            await _run(dm.start_container, env.container_name)
            env.status = "running"
        except Exception as e:
            env.status = "error"
            await db.commit()
            raise HTTPException(status_code=500, detail=str(e))

    await db.commit()
    return {"status": "running"}


@router.post("/environments/{env_id}/stop")
async def stop_environment(
    env_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    await _run(dm.stop_container, env.container_name)
    env.status = "stopped"
    await db.commit()
    return {"status": "stopped"}


@router.delete("/environments/{env_id}", status_code=204)
async def delete_environment(
    env_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db, require_owner=True)
    await _run(dm.remove_container, env.container_name)
    tf.destroy_workspace(env_id)

    # Delete members + env
    stmt = select(LabMember).where(LabMember.environment_id == env_id)
    members = (await db.execute(stmt)).scalars().all()
    for m in members:
        await db.delete(m)
    await db.delete(env)
    await db.commit()


# ─── Members ───

@router.get("/environments/{env_id}/members", response_model=list[MemberOut])
async def list_members(
    env_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_env_with_access(env_id, user, db)
    stmt = select(LabMember, User).join(User, LabMember.user_id == User.id).where(LabMember.environment_id == env_id)
    rows = (await db.execute(stmt)).all()
    return [
        MemberOut(
            id=m.id, user_id=m.user_id, username=u.username,
            display_name=u.display_name, role=m.role, invited_at=m.invited_at,
        )
        for m, u in rows
    ]


@router.post("/environments/{env_id}/members", response_model=MemberOut, status_code=201)
async def invite_member(
    env_id: str,
    body: MemberInvite,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db, require_owner=True)

    # Find user
    stmt = select(User).where(User.username == body.username)
    target = (await db.execute(stmt)).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    if target.id == env.owner_id:
        raise HTTPException(status_code=400, detail="소유자는 이미 멤버입니다")

    # Check existing
    stmt = select(LabMember).where(LabMember.environment_id == env_id, LabMember.user_id == target.id)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="이미 멤버입니다")

    member = LabMember(environment_id=env_id, user_id=target.id, role="member")
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return MemberOut(
        id=member.id, user_id=target.id, username=target.username,
        display_name=target.display_name, role="member", invited_at=member.invited_at,
    )


@router.delete("/environments/{env_id}/members/{user_id}", status_code=204)
async def remove_member(
    env_id: str,
    user_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_env_with_access(env_id, user, db, require_owner=True)
    stmt = select(LabMember).where(
        LabMember.environment_id == env_id,
        LabMember.user_id == user_id,
        LabMember.role == "member",
    )
    member = (await db.execute(stmt)).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="멤버를 찾을 수 없습니다")
    await db.delete(member)
    await db.commit()


# ─── Topology ───

@router.get("/environments/{env_id}/topology", response_model=TopologyOut)
async def get_topology(
    env_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        return TopologyOut(nodes=[], edges=[])
    data = await _run(aws.discover_topology, env.container_name)
    return TopologyOut(**data)


# ─── Generic resources list ───

@router.get("/environments/{env_id}/resources/{service}")
async def list_resources(
    env_id: str,
    service: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")

    cn = env.container_name
    handlers = {
        "s3": aws.s3_list_buckets,
        "sqs": aws.sqs_list_queues,
        "lambda": aws.lambda_list_functions,
        "dynamodb": aws.dynamodb_list_tables,
        "sns": aws.sns_list_topics,
        "iam-users": aws.iam_list_users,
        "iam-roles": aws.iam_list_roles,
        "iam-policies": aws.iam_list_policies,
    }
    handler = handlers.get(service)
    if not handler:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 서비스: {service}")

    return await _run(handler, cn)


@router.post("/environments/{env_id}/resources/{service}")
async def create_resource(
    env_id: str,
    service: str,
    body: ResourceCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")

    cn = env.container_name
    if service == "s3":
        return await _run(aws.s3_create_bucket, cn, body.name)
    elif service == "sqs":
        return await _run(aws.sqs_create_queue, cn, body.name)
    elif service == "sns":
        return await _run(aws.sns_create_topic, cn, body.name)
    else:
        raise HTTPException(status_code=400, detail=f"이 서비스의 일반 생성은 지원하지 않습니다: {service}")


@router.delete("/environments/{env_id}/resources/{service}/{resource_id:path}")
async def delete_resource(
    env_id: str,
    service: str,
    resource_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")

    cn = env.container_name
    if service == "s3":
        await _run(aws.s3_delete_bucket, cn, resource_id)
    elif service == "sqs":
        await _run(aws.sqs_delete_queue, cn, resource_id)
    elif service == "lambda":
        await _run(aws.lambda_delete_function, cn, resource_id)
    elif service == "dynamodb":
        await _run(aws.dynamodb_delete_table, cn, resource_id)
    elif service == "sns":
        await _run(aws.sns_delete_topic, cn, resource_id)
    else:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 서비스: {service}")
    return {"ok": True}


# ─── S3 specifics ───

@router.get("/environments/{env_id}/s3/{bucket}/objects", response_model=list[S3ObjectOut])
async def list_objects(
    env_id: str,
    bucket: str,
    prefix: str = "",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")
    return await _run(aws.s3_list_objects, env.container_name, bucket, prefix)


@router.post("/environments/{env_id}/s3/{bucket}/upload")
async def upload_object(
    env_id: str,
    bucket: str,
    file: UploadFile = File(...),
    key: str = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")
    object_key = key or file.filename or "unnamed"
    body = await file.read()
    content_type = file.content_type or "application/octet-stream"
    return await _run(aws.s3_upload_object, env.container_name, bucket, object_key, body, content_type)


@router.delete("/environments/{env_id}/s3/{bucket}/{key:path}")
async def delete_object(
    env_id: str,
    bucket: str,
    key: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")
    await _run(aws.s3_delete_object, env.container_name, bucket, key)
    return {"ok": True}


# ─── Lambda specifics ───

@router.post("/environments/{env_id}/lambda", status_code=201)
async def create_lambda(
    env_id: str,
    body: LambdaCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")
    return await _run(aws.lambda_create_function, env.container_name, body.name, body.runtime, body.code)


@router.post("/environments/{env_id}/lambda/{name}/invoke", response_model=LambdaResult)
async def invoke_lambda(
    env_id: str,
    name: str,
    body: LambdaInvoke,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")
    return await _run(aws.lambda_invoke, env.container_name, name, body.payload)


@router.get("/environments/{env_id}/lambda/{name}/code")
async def get_lambda_code(
    env_id: str,
    name: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")
    code = await _run(aws.lambda_get_code, env.container_name, name)
    return {"code": code}


# ─── SQS specifics ───

@router.post("/environments/{env_id}/sqs/{queue_name}/send")
async def send_sqs_message(
    env_id: str,
    queue_name: str,
    body: SqsSend,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")
    # Resolve queue URL
    queues = await _run(aws.sqs_list_queues, env.container_name)
    queue_url = None
    for q in queues:
        if q["name"] == queue_name:
            queue_url = q["url"]
            break
    if not queue_url:
        raise HTTPException(status_code=404, detail="큐를 찾을 수 없습니다")
    return await _run(aws.sqs_send_message, env.container_name, queue_url, body.body)


@router.get("/environments/{env_id}/sqs/{queue_name}/receive", response_model=list[SqsMessageOut])
async def receive_sqs_messages(
    env_id: str,
    queue_name: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")
    queues = await _run(aws.sqs_list_queues, env.container_name)
    queue_url = None
    for q in queues:
        if q["name"] == queue_name:
            queue_url = q["url"]
            break
    if not queue_url:
        raise HTTPException(status_code=404, detail="큐를 찾을 수 없습니다")
    return await _run(aws.sqs_receive_messages, env.container_name, queue_url)


# ─── DynamoDB specifics ───

@router.post("/environments/{env_id}/dynamodb", status_code=201)
async def create_dynamo_table(
    env_id: str,
    body: DynamoTableCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")
    return await _run(
        aws.dynamodb_create_table, env.container_name,
        body.name, body.partition_key, body.partition_key_type,
        body.sort_key, body.sort_key_type,
    )


@router.get("/environments/{env_id}/dynamodb/{table}/items")
async def scan_dynamo_table(
    env_id: str,
    table: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")
    return await _run(aws.dynamodb_scan, env.container_name, table)


@router.post("/environments/{env_id}/dynamodb/{table}/items")
async def put_dynamo_item(
    env_id: str,
    table: str,
    body: DynamoItemPut,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")
    return await _run(aws.dynamodb_put_item, env.container_name, table, body.item)


# ─── SNS specifics ───

@router.post("/environments/{env_id}/sns/{topic_name}/publish")
async def publish_sns(
    env_id: str,
    topic_name: str,
    body: SnsPublish,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")
    topics = await _run(aws.sns_list_topics, env.container_name)
    topic_arn = None
    for t in topics:
        if t["name"] == topic_name:
            topic_arn = t["arn"]
            break
    if not topic_arn:
        raise HTTPException(status_code=404, detail="토픽을 찾을 수 없습니다")
    return await _run(aws.sns_publish, env.container_name, topic_arn, body.message)


@router.post("/environments/{env_id}/sns/{topic_name}/subscribe")
async def subscribe_sns(
    env_id: str,
    topic_name: str,
    body: SnsSubscribe,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")
    topics = await _run(aws.sns_list_topics, env.container_name)
    topic_arn = None
    for t in topics:
        if t["name"] == topic_name:
            topic_arn = t["arn"]
            break
    if not topic_arn:
        raise HTTPException(status_code=404, detail="토픽을 찾을 수 없습니다")
    return await _run(aws.sns_subscribe, env.container_name, topic_arn, body.protocol, body.endpoint)


@router.get("/environments/{env_id}/sns/{topic_name}/subscriptions")
async def list_sns_subscriptions(
    env_id: str,
    topic_name: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")
    topics = await _run(aws.sns_list_topics, env.container_name)
    topic_arn = None
    for t in topics:
        if t["name"] == topic_name:
            topic_arn = t["arn"]
            break
    if not topic_arn:
        raise HTTPException(status_code=404, detail="토픽을 찾을 수 없습니다")
    return await _run(aws.sns_list_subscriptions, env.container_name, topic_arn)


# ─── Terraform ───

@router.get("/environments/{env_id}/terraform/files")
async def get_tf_files(
    env_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    tf.init_workspace(env_id, env.container_name)
    return tf.get_files(env_id)


@router.put("/environments/{env_id}/terraform/files")
async def save_tf_files(
    env_id: str,
    body: TerraformFiles,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    tf.save_files(env_id, body.files, env.container_name)
    return {"ok": True}


@router.delete("/environments/{env_id}/terraform/files/{filename}")
async def delete_tf_file(
    env_id: str,
    filename: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_env_with_access(env_id, user, db)
    tf.delete_file(env_id, filename)
    return {"ok": True}


@router.post("/environments/{env_id}/terraform/init", response_model=TerraformResult)
async def terraform_init(
    env_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")
    return await tf.tf_init(env_id, env.container_name)


@router.post("/environments/{env_id}/terraform/plan", response_model=TerraformResult)
async def terraform_plan(
    env_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")
    return await tf.tf_plan(env_id, env.container_name)


@router.post("/environments/{env_id}/terraform/apply", response_model=TerraformResult)
async def terraform_apply(
    env_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")
    return await tf.tf_apply(env_id, env.container_name)


@router.post("/environments/{env_id}/terraform/destroy", response_model=TerraformResult)
async def terraform_destroy(
    env_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")
    return await tf.tf_destroy(env_id, env.container_name)


@router.get("/terraform/templates", response_model=list[TerraformTemplate])
async def list_templates(user: User = Depends(get_current_user)):
    return tf.get_templates()


@router.get("/terraform/templates/{template_id}")
async def get_template(template_id: str, user: User = Depends(get_current_user)):
    code = tf.get_template_code(template_id)
    if code is None:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")
    return {"code": code}


# ─── Git CI/CD (push .tf → auto plan/apply) ───

@router.post("/environments/{env_id}/terraform/deploy")
async def terraform_deploy_from_repo(
    env_id: str,
    body: TerraformFiles,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """CI/CD endpoint: receive .tf files, save → init → apply, return result."""
    env = await _get_env_with_access(env_id, user, db)
    if env.status != "running":
        raise HTTPException(status_code=400, detail="환경이 실행 중이 아닙니다")

    # Save files
    tf.save_files(env_id, body.files, env.container_name)

    # Init
    init_result = await tf.tf_init(env_id, env.container_name)
    if init_result["exit_code"] != 0:
        return {"stage": "init", **init_result}

    # Plan
    plan_result = await tf.tf_plan(env_id, env.container_name)
    if plan_result["exit_code"] != 0:
        return {"stage": "plan", **plan_result}

    # Apply
    apply_result = await tf.tf_apply(env_id, env.container_name)
    return {"stage": "apply", **apply_result}

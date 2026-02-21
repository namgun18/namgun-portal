"""boto3 wrapper for LocalStack containers — all calls are sync (run in threadpool)."""

from __future__ import annotations

import base64
import io
import json
import zipfile
from typing import Any

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

_REGION = "us-east-1"
_CREDS = {"aws_access_key_id": "test", "aws_secret_access_key": "test"}
_BOTO_CFG = BotoConfig(retries={"max_attempts": 1}, connect_timeout=5, read_timeout=10)


def _client(container_name: str, service: str):
    endpoint = f"http://{container_name}:4566"
    return boto3.client(
        service,
        endpoint_url=endpoint,
        region_name=_REGION,
        config=_BOTO_CFG,
        **_CREDS,
    )


# ────────────────────── S3 ──────────────────────

def s3_list_buckets(cn: str) -> list[dict]:
    resp = _client(cn, "s3").list_buckets()
    return [{"name": b["Name"], "created": b["CreationDate"].isoformat()} for b in resp.get("Buckets", [])]


def s3_create_bucket(cn: str, name: str) -> dict:
    _client(cn, "s3").create_bucket(Bucket=name)
    return {"name": name}


def s3_delete_bucket(cn: str, name: str) -> None:
    c = _client(cn, "s3")
    # Delete all objects first
    try:
        objs = c.list_objects_v2(Bucket=name).get("Contents", [])
        for obj in objs:
            c.delete_object(Bucket=name, Key=obj["Key"])
    except ClientError:
        pass
    c.delete_bucket(Bucket=name)


def s3_list_objects(cn: str, bucket: str, prefix: str = "") -> list[dict]:
    resp = _client(cn, "s3").list_objects_v2(Bucket=bucket, Prefix=prefix)
    return [
        {
            "key": o["Key"],
            "size": o["Size"],
            "last_modified": o["LastModified"].isoformat(),
        }
        for o in resp.get("Contents", [])
    ]


def s3_upload_object(cn: str, bucket: str, key: str, body: bytes, content_type: str) -> dict:
    _client(cn, "s3").put_object(Bucket=bucket, Key=key, Body=body, ContentType=content_type)
    return {"bucket": bucket, "key": key}


def s3_download_object(cn: str, bucket: str, key: str) -> tuple[bytes, str]:
    resp = _client(cn, "s3").get_object(Bucket=bucket, Key=key)
    return resp["Body"].read(), resp.get("ContentType", "application/octet-stream")


def s3_delete_object(cn: str, bucket: str, key: str) -> None:
    _client(cn, "s3").delete_object(Bucket=bucket, Key=key)


# ────────────────────── SQS ──────────────────────

def sqs_list_queues(cn: str) -> list[dict]:
    c = _client(cn, "sqs")
    urls = c.list_queues().get("QueueUrls", [])
    result = []
    for url in urls:
        attrs = c.get_queue_attributes(QueueUrl=url, AttributeNames=["ApproximateNumberOfMessages"])["Attributes"]
        name = url.rsplit("/", 1)[-1]
        result.append({"name": name, "url": url, "messages": int(attrs.get("ApproximateNumberOfMessages", 0))})
    return result


def sqs_create_queue(cn: str, name: str) -> dict:
    resp = _client(cn, "sqs").create_queue(QueueName=name)
    return {"name": name, "url": resp["QueueUrl"]}


def sqs_delete_queue(cn: str, queue_url: str) -> None:
    _client(cn, "sqs").delete_queue(QueueUrl=queue_url)


def sqs_send_message(cn: str, queue_url: str, body: str) -> dict:
    resp = _client(cn, "sqs").send_message(QueueUrl=queue_url, MessageBody=body)
    return {"message_id": resp["MessageId"]}


def sqs_receive_messages(cn: str, queue_url: str, max_count: int = 10) -> list[dict]:
    resp = _client(cn, "sqs").receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=max_count, WaitTimeSeconds=1,
    )
    return [
        {"message_id": m["MessageId"], "receipt_handle": m["ReceiptHandle"], "body": m["Body"]}
        for m in resp.get("Messages", [])
    ]


def sqs_delete_message(cn: str, queue_url: str, receipt_handle: str) -> None:
    _client(cn, "sqs").delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)


# ────────────────────── Lambda ──────────────────────

def lambda_list_functions(cn: str) -> list[dict]:
    resp = _client(cn, "lambda").list_functions()
    return [
        {
            "name": f["FunctionName"],
            "runtime": f.get("Runtime", ""),
            "last_modified": f.get("LastModified", ""),
        }
        for f in resp.get("Functions", [])
    ]


def _zip_code(code: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("lambda_function.py", code)
    return buf.getvalue()


def lambda_create_function(cn: str, name: str, runtime: str, code: str) -> dict:
    c = _client(cn, "lambda")
    # Ensure lambda execution role exists
    iam = _client(cn, "iam")
    role_arn = f"arn:aws:iam::000000000000:role/lambda-role"
    try:
        iam.create_role(
            RoleName="lambda-role",
            AssumeRolePolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}],
            }),
        )
    except ClientError:
        pass  # Already exists

    resp = c.create_function(
        FunctionName=name,
        Runtime=runtime,
        Role=role_arn,
        Handler="lambda_function.lambda_handler",
        Code={"ZipFile": _zip_code(code)},
        Timeout=30,
        MemorySize=128,
    )
    return {"name": resp["FunctionName"], "runtime": resp.get("Runtime", "")}


def lambda_delete_function(cn: str, name: str) -> None:
    _client(cn, "lambda").delete_function(FunctionName=name)


def lambda_invoke(cn: str, name: str, payload: dict) -> dict:
    resp = _client(cn, "lambda").invoke(
        FunctionName=name,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload).encode(),
    )
    body = resp["Payload"].read().decode()
    try:
        body = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        pass
    return {"status_code": resp["StatusCode"], "payload": body}


def lambda_get_code(cn: str, name: str) -> str:
    """Retrieve the function code (best-effort for LocalStack)."""
    try:
        resp = _client(cn, "lambda").get_function(FunctionName=name)
        # LocalStack stores code inline in some versions
        location = resp.get("Code", {}).get("Location", "")
        if location:
            import urllib.request
            data = urllib.request.urlopen(location).read()
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for fname in zf.namelist():
                    if fname.endswith(".py"):
                        return zf.read(fname).decode()
    except Exception:
        pass
    return ""


# ────────────────────── DynamoDB ──────────────────────

def dynamodb_list_tables(cn: str) -> list[dict]:
    c = _client(cn, "dynamodb")
    names = c.list_tables().get("TableNames", [])
    result = []
    for name in names:
        desc = c.describe_table(TableName=name)["Table"]
        item_count = desc.get("ItemCount", 0)
        key_schema = desc.get("KeySchema", [])
        result.append({"name": name, "item_count": item_count, "key_schema": key_schema})
    return result


def dynamodb_create_table(
    cn: str, name: str, partition_key: str, pk_type: str = "S",
    sort_key: str | None = None, sk_type: str = "S",
) -> dict:
    key_schema = [{"AttributeName": partition_key, "KeyType": "HASH"}]
    attr_defs = [{"AttributeName": partition_key, "AttributeType": pk_type}]
    if sort_key:
        key_schema.append({"AttributeName": sort_key, "KeyType": "RANGE"})
        attr_defs.append({"AttributeName": sort_key, "AttributeType": sk_type})

    _client(cn, "dynamodb").create_table(
        TableName=name,
        KeySchema=key_schema,
        AttributeDefinitions=attr_defs,
        BillingMode="PAY_PER_REQUEST",
    )
    return {"name": name}


def dynamodb_delete_table(cn: str, name: str) -> None:
    _client(cn, "dynamodb").delete_table(TableName=name)


def dynamodb_put_item(cn: str, table: str, item: dict[str, Any]) -> dict:
    # Auto-wrap simple values into DynamoDB format
    dynamo_item = {}
    for k, v in item.items():
        if isinstance(v, str):
            dynamo_item[k] = {"S": v}
        elif isinstance(v, (int, float)):
            dynamo_item[k] = {"N": str(v)}
        elif isinstance(v, bool):
            dynamo_item[k] = {"BOOL": v}
        elif isinstance(v, dict) and any(t in v for t in ("S", "N", "BOOL", "L", "M")):
            dynamo_item[k] = v  # Already DynamoDB format
        else:
            dynamo_item[k] = {"S": str(v)}

    _client(cn, "dynamodb").put_item(TableName=table, Item=dynamo_item)
    return {"table": table}


def dynamodb_scan(cn: str, table: str) -> list[dict]:
    resp = _client(cn, "dynamodb").scan(TableName=table, Limit=100)
    items = []
    for raw in resp.get("Items", []):
        item = {}
        for k, v in raw.items():
            if "S" in v:
                item[k] = v["S"]
            elif "N" in v:
                item[k] = float(v["N"]) if "." in v["N"] else int(v["N"])
            elif "BOOL" in v:
                item[k] = v["BOOL"]
            else:
                item[k] = str(v)
        items.append(item)
    return items


def dynamodb_delete_item(cn: str, table: str, key: dict[str, Any]) -> None:
    dynamo_key = {}
    for k, v in key.items():
        if isinstance(v, str):
            dynamo_key[k] = {"S": v}
        elif isinstance(v, (int, float)):
            dynamo_key[k] = {"N": str(v)}
        else:
            dynamo_key[k] = {"S": str(v)}
    _client(cn, "dynamodb").delete_item(TableName=table, Key=dynamo_key)


# ────────────────────── SNS ──────────────────────

def sns_list_topics(cn: str) -> list[dict]:
    resp = _client(cn, "sns").list_topics()
    topics = []
    for t in resp.get("Topics", []):
        arn = t["TopicArn"]
        name = arn.rsplit(":", 1)[-1]
        # Count subscriptions
        subs = _client(cn, "sns").list_subscriptions_by_topic(TopicArn=arn).get("Subscriptions", [])
        topics.append({"name": name, "arn": arn, "subscriptions": len(subs)})
    return topics


def sns_create_topic(cn: str, name: str) -> dict:
    resp = _client(cn, "sns").create_topic(Name=name)
    return {"name": name, "arn": resp["TopicArn"]}


def sns_delete_topic(cn: str, arn: str) -> None:
    _client(cn, "sns").delete_topic(TopicArn=arn)


def sns_subscribe(cn: str, topic_arn: str, protocol: str, endpoint: str) -> dict:
    resp = _client(cn, "sns").subscribe(TopicArn=topic_arn, Protocol=protocol, Endpoint=endpoint)
    return {"subscription_arn": resp["SubscriptionArn"]}


def sns_list_subscriptions(cn: str, topic_arn: str) -> list[dict]:
    resp = _client(cn, "sns").list_subscriptions_by_topic(TopicArn=topic_arn)
    return [
        {"arn": s["SubscriptionArn"], "protocol": s["Protocol"], "endpoint": s["Endpoint"]}
        for s in resp.get("Subscriptions", [])
    ]


def sns_publish(cn: str, topic_arn: str, message: str) -> dict:
    resp = _client(cn, "sns").publish(TopicArn=topic_arn, Message=message)
    return {"message_id": resp["MessageId"]}


# ────────────────────── IAM (read-only) ──────────────────────

def iam_list_users(cn: str) -> list[dict]:
    resp = _client(cn, "iam").list_users()
    return [{"name": u["UserName"], "arn": u["Arn"]} for u in resp.get("Users", [])]


def iam_list_roles(cn: str) -> list[dict]:
    resp = _client(cn, "iam").list_roles()
    return [{"name": r["RoleName"], "arn": r["Arn"]} for r in resp.get("Roles", [])]


def iam_list_policies(cn: str) -> list[dict]:
    resp = _client(cn, "iam").list_policies(Scope="Local")
    return [{"name": p["PolicyName"], "arn": p["Arn"]} for p in resp.get("Policies", [])]


# ────────────────────── Topology ──────────────────────

def discover_topology(cn: str) -> dict:
    """Scan all supported services and return nodes + edges for graph rendering."""
    nodes: list[dict] = []
    edges: list[dict] = []

    # S3
    try:
        for b in s3_list_buckets(cn):
            nodes.append({"id": f"s3:{b['name']}", "label": b["name"], "service": "s3"})
    except Exception:
        pass

    # SQS
    sqs_url_map: dict[str, str] = {}
    try:
        for q in sqs_list_queues(cn):
            node_id = f"sqs:{q['name']}"
            nodes.append({"id": node_id, "label": q["name"], "service": "sqs", "details": {"messages": q["messages"]}})
            sqs_url_map[q["url"]] = node_id
    except Exception:
        pass

    # Lambda
    try:
        for f in lambda_list_functions(cn):
            node_id = f"lambda:{f['name']}"
            nodes.append({"id": node_id, "label": f["name"], "service": "lambda", "details": {"runtime": f["runtime"]}})

            # Check event source mappings (SQS → Lambda)
            try:
                mappings = _client(cn, "lambda").list_event_source_mappings(FunctionName=f["name"]).get("EventSourceMappings", [])
                for m in mappings:
                    arn = m.get("EventSourceArn", "")
                    if ":sqs:" in arn:
                        queue_name = arn.rsplit(":", 1)[-1]
                        edges.append({"source": f"sqs:{queue_name}", "target": node_id, "label": "trigger"})
                    elif ":dynamodb:" in arn:
                        table_name = arn.split("/")[-1]
                        edges.append({"source": f"dynamodb:{table_name}", "target": node_id, "label": "stream"})
            except Exception:
                pass
    except Exception:
        pass

    # DynamoDB
    try:
        for t in dynamodb_list_tables(cn):
            nodes.append({"id": f"dynamodb:{t['name']}", "label": t["name"], "service": "dynamodb", "details": {"items": t["item_count"]}})
    except Exception:
        pass

    # SNS
    try:
        for t in sns_list_topics(cn):
            node_id = f"sns:{t['name']}"
            nodes.append({"id": node_id, "label": t["name"], "service": "sns"})

            # SNS → SQS subscriptions
            try:
                subs = sns_list_subscriptions(cn, t["arn"])
                for s in subs:
                    if s["protocol"] == "sqs":
                        queue_name = s["endpoint"].rsplit(":", 1)[-1]
                        edges.append({"source": node_id, "target": f"sqs:{queue_name}", "label": "subscribe"})
                    elif s["protocol"] == "lambda":
                        fn_name = s["endpoint"].rsplit(":", 1)[-1]
                        edges.append({"source": node_id, "target": f"lambda:{fn_name}", "label": "subscribe"})
            except Exception:
                pass
    except Exception:
        pass

    return {"nodes": nodes, "edges": edges}

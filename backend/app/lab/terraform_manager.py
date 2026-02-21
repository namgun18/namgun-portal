"""Terraform workspace management — init/plan/apply/destroy per lab environment."""

from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path

WORKSPACE_ROOT = Path("/tmp/lab-workspaces")
TERRAFORM_BIN = "terraform"
TF_TIMEOUT = 180  # seconds


def _workspace_dir(env_id: str) -> Path:
    d = WORKSPACE_ROOT / env_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _provider_tf(container_name: str) -> str:
    return f"""# !! 자동 생성 — 수정하지 마세요 !!
terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
    archive = {{
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }}
  }}
}}

provider "aws" {{
  access_key = "test"
  secret_key = "test"
  region     = "us-east-1"

  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {{
    s3             = "http://{container_name}:4566"
    sqs            = "http://{container_name}:4566"
    lambda         = "http://{container_name}:4566"
    dynamodb       = "http://{container_name}:4566"
    sns            = "http://{container_name}:4566"
    iam            = "http://{container_name}:4566"
    sts            = "http://{container_name}:4566"
    cloudwatch     = "http://{container_name}:4566"
    cloudwatchlogs = "http://{container_name}:4566"
  }}
}}
"""


DEFAULT_MAIN_TF = """# ============================================
# namgun.or.kr AWS Lab — Terraform 실습
# ============================================
# provider.tf는 자동 생성되므로 수정하지 마세요.
#
# 사용법:
#   1. 아래에 AWS 리소스를 정의하세요
#   2. [Init] → [Plan] → [Apply] 순서로 실행
#   3. 토폴로지 그래프에서 배포 결과 확인
#
# ── 예시: S3 버킷 ──
# resource "aws_s3_bucket" "my_bucket" {
#   bucket = "my-first-bucket"
# }
#
# ── 예시: SQS 큐 ──
# resource "aws_sqs_queue" "my_queue" {
#   name = "my-queue"
# }
"""


# ── Preset templates ──

TEMPLATES: dict[str, dict[str, str]] = {
    "s3_website": {
        "label": "S3 정적 웹사이트",
        "code": '''resource "aws_s3_bucket" "website" {
  bucket = "my-website"
}

resource "aws_s3_object" "index" {
  bucket       = aws_s3_bucket.website.id
  key          = "index.html"
  content      = "<h1>Hello from S3!</h1>"
  content_type = "text/html"
}
''',
    },
    "lambda_hello": {
        "label": "Lambda 함수",
        "code": '''resource "aws_iam_role" "lambda_role" {
  name = "lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "/tmp/lambda.zip"

  source {
    content  = <<-EOF
def lambda_handler(event, context):
    return {"statusCode": 200, "body": "Hello from Lambda!"}
EOF
    filename = "lambda_function.py"
  }
}

resource "aws_lambda_function" "hello" {
  function_name = "hello-function"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  filename      = data.archive_file.lambda_zip.output_path
}
''',
    },
    "sqs_sns": {
        "label": "SQS + SNS 연동",
        "code": '''resource "aws_sqs_queue" "orders" {
  name = "order-queue"
}

resource "aws_sns_topic" "notifications" {
  name = "order-notifications"
}

resource "aws_sns_topic_subscription" "sqs_sub" {
  topic_arn = aws_sns_topic.notifications.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.orders.arn
}
''',
    },
    "dynamodb_table": {
        "label": "DynamoDB 테이블",
        "code": '''resource "aws_dynamodb_table" "users" {
  name         = "users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  range_key    = "email"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }
}
''',
    },
    "full_stack": {
        "label": "풀스택 (S3 + Lambda + SQS + SNS + DynamoDB)",
        "code": '''# ── S3: 파일 저장소 ──
resource "aws_s3_bucket" "data" {
  bucket = "app-data-bucket"
}

# ── DynamoDB: 유저 테이블 ──
resource "aws_dynamodb_table" "users" {
  name         = "users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }
}

# ── SQS: 작업 큐 ──
resource "aws_sqs_queue" "tasks" {
  name                      = "task-queue"
  message_retention_seconds = 86400
}

# ── SNS: 알림 토픽 ──
resource "aws_sns_topic" "alerts" {
  name = "system-alerts"
}

resource "aws_sns_topic_subscription" "queue_sub" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.tasks.arn
}

# ── Lambda: 처리 함수 ──
resource "aws_iam_role" "lambda_role" {
  name = "lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

data "archive_file" "processor" {
  type        = "zip"
  output_path = "/tmp/processor.zip"

  source {
    content  = <<-EOF
import json
def lambda_handler(event, context):
    print(f"Processing: {json.dumps(event)}")
    return {"statusCode": 200, "body": "Processed!"}
EOF
    filename = "lambda_function.py"
  }
}

resource "aws_lambda_function" "processor" {
  function_name = "task-processor"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  filename      = data.archive_file.processor.output_path
}
''',
    },
}


# ── File I/O ──

def init_workspace(env_id: str, container_name: str) -> None:
    """Create workspace with provider.tf and default main.tf."""
    workspace = _workspace_dir(env_id)
    (workspace / "provider.tf").write_text(_provider_tf(container_name))
    main_tf = workspace / "main.tf"
    if not main_tf.exists():
        main_tf.write_text(DEFAULT_MAIN_TF)


def get_files(env_id: str) -> dict[str, str]:
    """Return all .tf files in the workspace."""
    workspace = _workspace_dir(env_id)
    files: dict[str, str] = {}
    for f in sorted(workspace.glob("*.tf")):
        files[f.name] = f.read_text()
    return files


def save_files(env_id: str, files: dict[str, str], container_name: str) -> None:
    """Save user .tf files. provider.tf is always regenerated."""
    workspace = _workspace_dir(env_id)
    # Always regenerate provider.tf
    (workspace / "provider.tf").write_text(_provider_tf(container_name))
    for name, content in files.items():
        if name == "provider.tf":
            continue  # Skip user attempts to overwrite provider
        if name.endswith(".tf"):
            (workspace / name).write_text(content)


def delete_file(env_id: str, filename: str) -> None:
    if filename == "provider.tf" or filename == "main.tf":
        return  # Don't delete essential files
    workspace = _workspace_dir(env_id)
    path = workspace / filename
    if path.exists() and path.suffix == ".tf":
        path.unlink()


def destroy_workspace(env_id: str) -> None:
    """Delete the entire workspace directory."""
    workspace = WORKSPACE_ROOT / env_id
    if workspace.exists():
        shutil.rmtree(workspace)


def clear_state(env_id: str) -> None:
    """Remove terraform state (used when container is recreated)."""
    workspace = WORKSPACE_ROOT / env_id
    for pattern in ("terraform.tfstate", "terraform.tfstate.backup", ".terraform.lock.hcl"):
        p = workspace / pattern
        if p.exists():
            p.unlink()
    tf_dir = workspace / ".terraform"
    if tf_dir.exists():
        shutil.rmtree(tf_dir)


# ── Terraform CLI ──

async def _run_tf(env_id: str, args: list[str], container_name: str) -> dict:
    """Execute terraform command and capture output."""
    workspace = _workspace_dir(env_id)
    # Ensure provider.tf is fresh
    (workspace / "provider.tf").write_text(_provider_tf(container_name))

    env = {**os.environ, "TF_IN_AUTOMATION": "1"}

    proc = await asyncio.create_subprocess_exec(
        TERRAFORM_BIN, *args, "-no-color",
        cwd=str(workspace),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=TF_TIMEOUT)
    except asyncio.TimeoutError:
        proc.kill()
        return {"exit_code": -1, "stdout": "", "stderr": "Timeout: 명령 실행이 시간 초과되었습니다 (180초)"}

    return {
        "exit_code": proc.returncode,
        "stdout": stdout.decode(errors="replace"),
        "stderr": stderr.decode(errors="replace"),
    }


async def tf_init(env_id: str, container_name: str) -> dict:
    init_workspace(env_id, container_name)
    return await _run_tf(env_id, ["init"], container_name)


async def tf_plan(env_id: str, container_name: str) -> dict:
    return await _run_tf(env_id, ["plan"], container_name)


async def tf_apply(env_id: str, container_name: str) -> dict:
    return await _run_tf(env_id, ["apply", "-auto-approve"], container_name)


async def tf_destroy(env_id: str, container_name: str) -> dict:
    return await _run_tf(env_id, ["destroy", "-auto-approve"], container_name)


def get_templates() -> list[dict]:
    return [{"id": k, "label": v["label"]} for k, v in TEMPLATES.items()]


def get_template_code(template_id: str) -> str | None:
    t = TEMPLATES.get(template_id)
    return t["code"] if t else None

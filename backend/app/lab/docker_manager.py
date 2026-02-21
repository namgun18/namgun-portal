"""Manage LocalStack containers for lab environments."""

import docker
from docker.errors import NotFound, APIError

LOCALSTACK_IMAGE = "localstack/localstack:3.8"
NETWORK_NAME = "lab-net"
MEMORY_LIMIT = "2g"
CPU_PERIOD = 100_000
CPU_QUOTA = 200_000  # 2 CPUs


def _client() -> docker.DockerClient:
    return docker.DockerClient(base_url="unix:///var/run/docker.sock")


def create_container(env_id: str) -> dict:
    """Create and start a LocalStack container on lab-net."""
    client = _client()
    container_name = f"lab-{env_id[:8]}"

    # Ensure network exists
    try:
        client.networks.get(NETWORK_NAME)
    except NotFound:
        client.networks.create(NETWORK_NAME, driver="bridge")

    container = client.containers.run(
        LOCALSTACK_IMAGE,
        name=container_name,
        detach=True,
        mem_limit=MEMORY_LIMIT,
        cpu_period=CPU_PERIOD,
        cpu_quota=CPU_QUOTA,
        environment={
            "SERVICES": "s3,sqs,lambda,dynamodb,sns,iam",
            "EAGER_SERVICE_LOADING": "1",
        },
        labels={
            "portal.lab": "true",
            "portal.lab.env": env_id,
        },
        network=NETWORK_NAME,
    )
    return {"container_id": container.id, "container_name": container_name}


def start_container(container_name: str) -> None:
    client = _client()
    container = client.containers.get(container_name)
    if container.status != "running":
        container.start()


def stop_container(container_name: str) -> None:
    client = _client()
    try:
        container = client.containers.get(container_name)
        container.stop(timeout=10)
    except NotFound:
        pass


def remove_container(container_name: str) -> None:
    client = _client()
    try:
        container = client.containers.get(container_name)
        container.remove(force=True)
    except NotFound:
        pass


def get_status(container_name: str) -> str:
    client = _client()
    try:
        container = client.containers.get(container_name)
        return container.status  # "running", "exited", "created", etc.
    except NotFound:
        return "removed"
    except APIError:
        return "error"

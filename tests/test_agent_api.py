import pytest
from aiohttp.test_utils import TestClient, TestServer

from helzer.api.agent import AgentAPI


class FakeDocker:
    def capacity(self):
        return {
            "available_cpu": 10.0,
            "available_ram_mb": 8192.0,
            "containers": 2.0,
        }


class FakeService:
    docker = FakeDocker()

    async def create_vps(self, owner_id, spec):
        return {
            "id": 9,
            "owner_id": owner_id,
            "name": spec.name,
            "container_id": "container-9",
            "host_port": 2209,
            "status": "running",
            "cpu_cores": spec.cpu_cores,
            "ram_mb": spec.ram_mb,
            "disk_gb": spec.disk_gb,
            "image": spec.image,
        }

    async def get(self, vps_id):
        return {"id": vps_id, "owner_id": 123, "status": "running"}

    async def action(self, vps_id, action):
        return {"id": vps_id, "status": action}

    async def stats(self, vps_id):
        return {"cpu_percent": 1.0, "memory_percent": 2.0}

    async def logs(self, vps_id):
        return "ok"


@pytest.fixture
async def client():
    server = TestServer(AgentAPI(FakeService(), "secret").app)
    await server.start_server()
    client = TestClient(server)
    await client.start_server()
    try:
        yield client
    finally:
        await client.close()
        await server.close()


async def test_agent_api_requires_bearer_token(client):
    response = await client.get("/v1/agent/health")
    assert response.status == 401


async def test_agent_api_exposes_nodes_and_os(client):
    headers = {"Authorization": "Bearer secret"}
    nodes = await client.get("/v1/agent/nodes", headers=headers)
    systems = await client.get("/v1/agent/operating-systems", headers=headers)

    assert nodes.status == 200
    assert (await nodes.json())["nodes"][0]["id"] == "local"
    assert systems.status == 200
    assert "ubuntu:24.04" in [item["image"] for item in (await systems.json())["operating_systems"]]


async def test_agent_api_creates_vps_without_exposing_docker_commands(client):
    headers = {"Authorization": "Bearer secret"}
    response = await client.post(
        "/v1/agent/vps",
        headers=headers,
        json={
            "owner_id": 123,
            "name": "invite-vps",
            "cpu_cores": 4,
            "ram_mb": 12288,
            "disk_gb": 20,
            "node_id": "local",
            "image": "ubuntu:24.04",
            "duration_days": 7,
        },
    )

    assert response.status == 201
    payload = await response.json()
    assert payload["vps"]["owner_id"] == 123
    assert payload["vps"]["node_id"] == "local"
    assert payload["vps"]["duration_days"] == 7

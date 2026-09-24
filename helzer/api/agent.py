from __future__ import annotations

from aiohttp import web

from helzer.core.limits import PLANS
from helzer.services.vps_service import VPSService, VPSSpec


OS_CATALOG = (
    {"id": "ubuntu-24.04", "name": "Ubuntu 24.04 LTS", "image": "ubuntu:24.04"},
    {"id": "debian-12", "name": "Debian 12", "image": "debian:12"},
    {"id": "alpine-3.20", "name": "Alpine 3.20", "image": "alpine:3.20"},
)


class AgentAPI:
    """Private, token-authenticated bridge for the separate AI Ticket Manager."""

    def __init__(self, service: VPSService, token: str):
        self.service = service
        self.token = token
        self.app = web.Application()
        self.app.add_routes([
            web.get("/v1/agent/health", self.health),
            web.get("/v1/agent/plans", self.plans),
            web.get("/v1/agent/nodes", self.nodes),
            web.get("/v1/agent/operating-systems", self.operating_systems),
            web.post("/v1/agent/vps", self.create_vps),
            web.get("/v1/agent/vps/{vps_id}", self.get_vps),
            web.post("/v1/agent/vps/{vps_id}/action", self.action),
            web.get("/v1/agent/vps/{vps_id}/stats", self.stats),
            web.get("/v1/agent/vps/{vps_id}/logs", self.logs),
        ])

    def _authorized(self, request: web.Request) -> bool:
        return bool(self.token) and request.headers.get("Authorization") == f"Bearer {self.token}"

    async def _guard(self, request: web.Request) -> web.Response | None:
        if not self._authorized(request):
            return web.json_response({"error": "unauthorized"}, status=401)
        return None

    async def health(self, request: web.Request) -> web.Response:
        denied = await self._guard(request)
        if denied: return denied
        return web.json_response({"ok": True, "service": "helzer-vps-agent"})

    async def plans(self, request: web.Request) -> web.Response:
        denied = await self._guard(request)
        if denied: return denied
        return web.json_response({"plans": [
            {"id": key, "name": plan.name, "cpu_cores": plan.cpu_cores, "ram_mb": plan.ram_mb, "disk_gb": plan.disk_gb, "max_vps": plan.max_vps}
            for key, plan in PLANS.items()
        ]})

    async def nodes(self, request: web.Request) -> web.Response:
        denied = await self._guard(request)
        if denied: return denied
        capacity = self.service.docker.capacity()
        return web.json_response({"nodes": [{
            "id": "local",
            "name": "Local Node",
            "location": "Local",
            "available": capacity["available_cpu"] > 0 and capacity["available_ram_mb"] > 0,
            "available_cpu": capacity["available_cpu"],
            "available_ram_mb": capacity["available_ram_mb"],
            "containers": int(capacity["containers"]),
        }]})

    async def operating_systems(self, request: web.Request) -> web.Response:
        denied = await self._guard(request)
        if denied: return denied
        return web.json_response({"operating_systems": list(OS_CATALOG)})

    async def create_vps(self, request: web.Request) -> web.Response:
        denied = await self._guard(request)
        if denied: return denied
        try:
            body = await request.json()
            owner_id = int(body["owner_id"])
            node_id = str(body.get("node_id") or "local")
            image = str(body.get("image") or "ubuntu:24.04")
            if node_id != "local":
                return web.json_response({"error": "unknown node"}, status=400)
            if image not in {item["image"] for item in OS_CATALOG}:
                return web.json_response({"error": "unsupported operating system"}, status=400)
            vps = await self.service.create_vps(
                owner_id,
                VPSSpec(
                    name=str(body.get("name") or f"Helzer-{owner_id}"),
                    cpu_cores=int(body["cpu_cores"]),
                    ram_mb=int(body["ram_mb"]),
                    disk_gb=int(body["disk_gb"]),
                    image=image,
                ),
            )
            os_info = next(item for item in OS_CATALOG if item["image"] == image)
            return web.json_response({"success": True, "vps": {
                **vps,
                "node_id": node_id,
                "node_name": "Local Node",
                "os": os_info,
                "duration_days": int(body.get("duration_days") or 7),
            }}, status=201)
        except (KeyError, TypeError, ValueError) as exc:
            return web.json_response({"error": str(exc)}, status=400)
        except Exception as exc:
            return web.json_response({"error": str(exc)}, status=409)

    async def get_vps(self, request: web.Request) -> web.Response:
        denied = await self._guard(request)
        if denied: return denied
        try:
            vps = await self.service.get(int(request.match_info["vps_id"]))
            if not vps: return web.json_response({"error": "VPS not found"}, status=404)
            return web.json_response({"vps": vps})
        except ValueError as exc:
            return web.json_response({"error": str(exc)}, status=400)

    async def action(self, request: web.Request) -> web.Response:
        denied = await self._guard(request)
        if denied: return denied
        try:
            action = str((await request.json())["action"])
            if action not in {"start", "stop", "restart"}:
                return web.json_response({"error": "unsupported action"}, status=400)
            return web.json_response({"vps": await self.service.action(int(request.match_info["vps_id"]), action)})
        except (KeyError, TypeError, ValueError) as exc:
            return web.json_response({"error": str(exc)}, status=400)
        except Exception as exc:
            return web.json_response({"error": str(exc)}, status=409)

    async def stats(self, request: web.Request) -> web.Response:
        denied = await self._guard(request)
        if denied: return denied
        try:
            return web.json_response({"stats": await self.service.stats(int(request.match_info["vps_id"]))})
        except (ValueError, KeyError) as exc:
            return web.json_response({"error": str(exc)}, status=404)

    async def logs(self, request: web.Request) -> web.Response:
        denied = await self._guard(request)
        if denied: return denied
        try:
            return web.json_response({"logs": (await self.service.logs(int(request.match_info["vps_id"])))[:10000]})
        except (ValueError, KeyError) as exc:
            return web.json_response({"error": str(exc)}, status=404)

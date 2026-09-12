from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from helzer.database.models import VPS
from helzer.docker.manager import DockerManager
from helzer.services.port_service import PortService


@dataclass(frozen=True, slots=True)
class VPSSpec:
    name: str
    cpu_cores: int
    ram_mb: int
    disk_gb: int
    image: str = "ubuntu:24.04"


class VPSService:
    ALLOWED_IMAGES = frozenset({"ubuntu:24.04", "debian:12", "alpine:3.20"})

    def __init__(self, sessions: async_sessionmaker[AsyncSession] | None, docker: DockerManager | None, ports: PortService | None):
        self.sessions, self.docker, self.ports = sessions, docker, ports

    def validate_spec(self, spec: VPSSpec) -> None:
        if not 1 <= spec.cpu_cores <= 32: raise ValueError("CPU cores must be between 1 and 32")
        if not 128 <= spec.ram_mb <= 131072: raise ValueError("RAM must be between 128 MB and 128 GB")
        if not 1 <= spec.disk_gb <= 2000: raise ValueError("disk must be between 1 GB and 2000 GB")
        if not spec.name.strip() or len(spec.name) > 64: raise ValueError("invalid VPS name")
        if spec.image not in self.ALLOWED_IMAGES: raise ValueError("Docker image is not allowed")

    @staticmethod
    def _dict(vps: VPS) -> dict[str, object]:
        return {"id": vps.id, "owner_id": vps.owner_id, "name": vps.name, "container_id": vps.container_id,
                "host_port": vps.host_port, "status": vps.status, "cpu_cores": vps.cpu_cores,
                "ram_mb": vps.ram_mb, "disk_gb": vps.disk_gb, "image": vps.image}

    async def create_vps(self, owner_id: int, spec: VPSSpec) -> dict[str, object]:
        self.validate_spec(spec)
        if not self.docker or not self.ports or not self.sessions: raise RuntimeError("VPS service is not configured")
        port = self.ports.allocate(); container = None
        try:
            container = await asyncio.to_thread(self.docker.create, name=f"hx_{owner_id}_{spec.name.lower().replace(' ', '-')[:40]}", image=spec.image, cpu_cores=spec.cpu_cores, ram_mb=spec.ram_mb, host_port=port)
            await asyncio.to_thread(container.start)
            async with self.sessions() as session:
                vps = VPS(owner_id=owner_id, name=spec.name, container_id=container.id, host_port=port, status="running", cpu_cores=spec.cpu_cores, ram_mb=spec.ram_mb, disk_gb=spec.disk_gb, image=spec.image)
                session.add(vps); await session.commit(); await session.refresh(vps); return self._dict(vps)
        except Exception:
            self.ports.release(port)
            if container is not None: await asyncio.to_thread(self.docker.delete, container.id)
            raise

    async def get(self, vps_id: int) -> dict[str, object] | None:
        if not self.sessions: raise RuntimeError("VPS service is not configured")
        async with self.sessions() as session:
            vps = await session.get(VPS, vps_id); return self._dict(vps) if vps else None

    async def list_for_user(self, owner_id: int) -> list[dict[str, object]]:
        if not self.sessions: raise RuntimeError("VPS service is not configured")
        async with self.sessions() as session:
            result = await session.scalars(select(VPS).where(VPS.owner_id == owner_id).order_by(VPS.id.desc()))
            return [self._dict(v) for v in result]

    async def all_vps(self) -> list[dict[str, object]]:
        if not self.sessions: raise RuntimeError("VPS service is not configured")
        async with self.sessions() as session:
            result = await session.scalars(select(VPS).order_by(VPS.id))
            return [self._dict(v) for v in result]

    async def action(self, vps_id: int, action: str) -> dict[str, object]:
        vps = await self.get(vps_id)
        if not vps or not vps.get("container_id") or not self.docker or not self.sessions: raise ValueError("VPS not found")
        cid = str(vps["container_id"])
        if action == "start": await asyncio.to_thread(self.docker.start, cid); status = "running"
        elif action == "stop": await asyncio.to_thread(self.docker.stop, cid); status = "stopped"
        elif action == "restart": await asyncio.to_thread(self.docker.restart, cid); status = "running"
        else: raise ValueError("unsupported VPS action")
        async with self.sessions() as session:
            row = await session.get(VPS, vps_id); row.status = status; await session.commit(); return self._dict(row)

    async def rename(self, vps_id: int, owner_id: int, name: str) -> dict[str, object]:
        if not name.strip() or len(name) > 64: raise ValueError("invalid VPS name")
        if not self.sessions: raise RuntimeError("VPS service is not configured")
        async with self.sessions() as session:
            vps = await session.get(VPS, vps_id)
            if not vps or vps.owner_id != owner_id: raise ValueError("VPS not found")
            vps.name = name.strip(); await session.commit(); return self._dict(vps)

    async def logs(self, vps_id: int) -> str:
        vps = await self.get(vps_id)
        if not vps or not vps.get("container_id") or not self.docker: raise ValueError("VPS not found")
        return await asyncio.to_thread(self.docker.logs, str(vps["container_id"]), 100)

    async def stats(self, vps_id: int) -> dict[str, float]:
        vps = await self.get(vps_id)
        if not vps or not vps.get("container_id") or not self.docker: raise ValueError("VPS not found")
        return await asyncio.to_thread(self.docker.stats, str(vps["container_id"]))

    async def delete(self, vps_id: int) -> None:
        if not self.docker or not self.ports or not self.sessions: raise RuntimeError("VPS service is not configured")
        async with self.sessions() as session:
            vps = await session.get(VPS, vps_id)
            if not vps: raise ValueError("VPS not found")
            if vps.container_id: await asyncio.to_thread(self.docker.delete, vps.container_id)
            if vps.host_port: self.ports.release(vps.host_port)
            await session.delete(vps); await session.commit()

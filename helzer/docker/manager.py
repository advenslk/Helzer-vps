from __future__ import annotations

from typing import Any


class DockerManager:
    ALLOWED_IMAGES = frozenset({"ubuntu:24.04", "debian:12", "alpine:3.20"})

    def __init__(self, client: Any):
        self.client = client

    def build_container_config(self, *, name: str, image: str, cpu_cores: int, ram_mb: int) -> dict[str, Any]:
        if image not in self.ALLOWED_IMAGES:
            raise ValueError("Docker image is not allowed")
        if cpu_cores < 1:
            raise ValueError("CPU cores must be at least 1")
        if ram_mb < 128:
            raise ValueError("RAM must be at least 128 MB")
        return {
            "name": name,
            "image": image,
            "mem_limit": ram_mb * 1024 * 1024,
            "nano_cpus": cpu_cores * 1_000_000_000,
            "detach": True,
            "tty": True,
            "stdin_open": True,
            "restart_policy": {"Name": "unless-stopped"},
        }

    def capacity(self, reserve_ram_mb: int = 256, reserve_cpu: int = 1) -> dict[str, float]:
        info = self.client.info()
        total_ram_mb = float(info.get("MemTotal", 0)) / 1024 / 1024
        total_cpu = float(info.get("NCPU", 0))
        containers = self.client.containers.list()
        used_ram = sum(float(c.attrs.get("HostConfig", {}).get("Memory", 0)) for c in containers) / 1024 / 1024
        used_cpu = sum(float(c.attrs.get("HostConfig", {}).get("NanoCpus", 0)) / 1_000_000_000 for c in containers)
        return {
            "total_ram_mb": total_ram_mb,
            "available_ram_mb": max(0.0, total_ram_mb - used_ram - reserve_ram_mb),
            "total_cpu": total_cpu,
            "available_cpu": max(0.0, total_cpu - used_cpu - reserve_cpu),
            "containers": float(len(containers)),
        }

    def can_fit(self, cpu_cores: int, ram_mb: int) -> bool:
        capacity = self.capacity(reserve_ram_mb=256, reserve_cpu=1)
        return capacity["available_cpu"] >= cpu_cores and capacity["available_ram_mb"] >= ram_mb

    def create(self, **kwargs: Any) -> Any:
        if self.client is None:
            raise RuntimeError("Docker client is not configured")
        if not self.can_fit(int(kwargs["cpu_cores"]), int(kwargs["ram_mb"])):
            raise RuntimeError("node does not have enough free CPU/RAM")
        return self.client.containers.create(**self.build_container_config(**kwargs))

    def start(self, container_id: str) -> None:
        self._container(container_id).start()

    def stop(self, container_id: str) -> None:
        self._container(container_id).stop(timeout=10)

    def restart(self, container_id: str) -> None:
        self._container(container_id).restart(timeout=10)

    def delete(self, container_id: str) -> None:
        self._container(container_id).remove(force=True)

    def logs(self, container_id: str, tail: int = 100) -> str:
        if not 1 <= tail <= 1000:
            raise ValueError("tail must be between 1 and 1000")
        return self._container(container_id).logs(tail=tail).decode(errors="replace")

    def stats(self, container_id: str) -> dict[str, float]:
        raw = self._container(container_id).stats(stream=False)
        cpu = raw.get("cpu_stats", {})
        prev = raw.get("precpu_stats", {})
        cpu_delta = cpu.get("cpu_usage", {}).get("total_usage", 0) - prev.get("cpu_usage", {}).get("total_usage", 0)
        system_delta = cpu.get("system_cpu_usage", 0) - prev.get("system_cpu_usage", 0)
        online = cpu.get("online_cpus") or len(cpu.get("cpu_usage", {}).get("percpu_usage", []) or [1])
        cpu_percent = (cpu_delta / system_delta * online * 100) if system_delta else 0.0
        memory = raw.get("memory_stats", {})
        usage = float(memory.get("usage", 0))
        limit = float(memory.get("limit", 1))
        networks = raw.get("networks", {}).values()
        rx = sum(float(n.get("rx_bytes", 0)) for n in networks) / 1024 / 1024
        tx = sum(float(n.get("tx_bytes", 0)) for n in networks) / 1024 / 1024
        return {"cpu_percent": cpu_percent, "memory_percent": usage / limit * 100, "net_rx_mb": rx, "net_tx_mb": tx}

    def _container(self, container_id: str) -> Any:
        if self.client is None:
            raise RuntimeError("Docker client is not configured")
        return self.client.containers.get(container_id)

from __future__ import annotations

from typing import Any


class DockerManager:
    ALLOWED_IMAGES = frozenset({"ubuntu:24.04", "debian:12", "alpine:3.20"})

    def __init__(self, client: Any):
        self.client = client

    def build_container_config(
        self, *, name: str, image: str, cpu_cores: int, ram_mb: int
    ) -> dict[str, Any]:
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
        }

    def create(self, **kwargs: Any) -> Any:
        if self.client is None:
            raise RuntimeError("Docker client is not configured")
        config = self.build_container_config(**kwargs)
        return self.client.containers.create(**config)

    def start(self, container_id: str) -> None:
        self._container(container_id).start()

    def stop(self, container_id: str) -> None:
        self._container(container_id).stop()

    def restart(self, container_id: str) -> None:
        self._container(container_id).restart()

    def delete(self, container_id: str) -> None:
        self._container(container_id).remove(force=True)

    def logs(self, container_id: str, tail: int = 100) -> str:
        if tail < 1 or tail > 1000:
            raise ValueError("tail must be between 1 and 1000")
        return self._container(container_id).logs(tail=tail).decode(errors="replace")

    def _container(self, container_id: str) -> Any:
        if self.client is None:
            raise RuntimeError("Docker client is not configured")
        return self.client.containers.get(container_id)

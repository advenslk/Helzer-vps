from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VPSSpec:
    name: str
    cpu_cores: int
    ram_mb: int
    disk_gb: int
    image: str = "ubuntu:24.04"


class VPSService:
    """Safe orchestration boundary for Docker VPS operations.

    Discord commands and the AI assistant should call this service rather than
    executing arbitrary Docker commands or shell input.
    """

    ALLOWED_IMAGES = frozenset({"ubuntu:24.04", "debian:12", "alpine:3.20"})

    def validate_spec(self, spec: VPSSpec) -> None:
        if spec.cpu_cores < 1:
            raise ValueError("CPU cores must be at least 1")
        if spec.ram_mb < 128:
            raise ValueError("RAM must be at least 128 MB")
        if spec.disk_gb < 1:
            raise ValueError("disk must be at least 1 GB")
        if spec.image not in self.ALLOWED_IMAGES:
            raise ValueError("Docker image is not allowed")

    async def create_vps(self, spec: VPSSpec) -> dict[str, object]:
        self.validate_spec(spec)
        # Docker provisioning will be wired here after DB/node scheduling exists.
        return {
            "name": spec.name,
            "status": "pending",
            "cpu_cores": spec.cpu_cores,
            "ram_mb": spec.ram_mb,
            "disk_gb": spec.disk_gb,
            "image": spec.image,
        }

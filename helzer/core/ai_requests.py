from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateVPSRequest:
    target_user_id: int
    ram_mb: int
    cpu_cores: int
    disk_gb: int

    @classmethod
    def from_text(cls, text: str) -> "CreateVPSRequest":
        user = re.search(r"@?(\d{3,})", text)
        ram = re.search(r"(\d+(?:\.\d+)?)\s*(gb|gib)\s*(?:ram)?", text, re.I)
        cpu = re.search(r"(\d+)\s*(?:cpu\s*)?(?:cores?|core)", text, re.I)
        disk = re.search(r"(\d+(?:\.\d+)?)\s*(gb|gib)\s*(?:disk|storage)", text, re.I)

        if not user:
            raise ValueError("target user is required")
        if not ram:
            raise ValueError("RAM is required")
        if not cpu:
            raise ValueError("CPU cores are required")
        if not disk:
            raise ValueError("disk is required")

        return cls(
            target_user_id=int(user.group(1)),
            ram_mb=int(float(ram.group(1)) * 1024),
            cpu_cores=int(cpu.group(1)),
            disk_gb=int(float(disk.group(1))),
        )

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DiskQuota:
    limit_gb: int

    def validate(self) -> None:
        if self.limit_gb < 1:
            raise ValueError("disk quota must be at least 1 GB")


def docker_storage_options(quota: DiskQuota) -> dict[str, str]:
    """Return storage-driver options when the host supports project quotas.

    Enforcement is intentionally delegated to the host filesystem/runtime; this
    function never pretends a metadata-only value is a real disk limit.
    """
    quota.validate()
    return {"helzer.disk_quota_gb": str(quota.limit_gb)}

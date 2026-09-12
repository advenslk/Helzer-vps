from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Plan:
    name: str
    cpu_cores: int
    ram_mb: int
    disk_gb: int
    max_vps: int


PLANS = {
    "free": Plan("FREE", 1, 512, 10, 1),
    "starter": Plan("STARTER", 2, 2048, 25, 3),
    "pro": Plan("PRO", 4, 8192, 80, 10),
}


def get_plan(name: str) -> Plan:
    try:
        return PLANS[name.lower()]
    except KeyError as exc:
        raise ValueError("unknown plan") from exc


def within_plan(plan: Plan, cpu_cores: int, ram_mb: int, disk_gb: int) -> bool:
    return cpu_cores <= plan.cpu_cores and ram_mb <= plan.ram_mb and disk_gb <= plan.disk_gb

from __future__ import annotations

import asyncio


class MonitoringService:
    """Lightweight health loop; state changes stay behind VPSService."""

    def __init__(self, service, interval_seconds: int = 60):
        self.service = service
        self.interval_seconds = max(10, interval_seconds)
        self._task: asyncio.Task | None = None
        self._stopped = asyncio.Event()

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._stopped.clear()
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stopped.set()
        if self._task:
            await self._task
            self._task = None

    async def _run(self) -> None:
        while not self._stopped.is_set():
            try:
                for vps in await self.service.all_vps():
                    if vps.get("status") == "running":
                        try:
                            await self.service.stats(int(vps["id"]))
                        except Exception:
                            # A later health pass can recover transient Docker errors.
                            continue
            finally:
                try:
                    await asyncio.wait_for(self._stopped.wait(), timeout=self.interval_seconds)
                except asyncio.TimeoutError:
                    pass

from __future__ import annotations

from aiohttp import web

from helzer.api.agent import AgentAPI


class AgentServer:
    def __init__(self, api: AgentAPI, host: str, port: int):
        self.api = api
        self.host = host
        self.port = port
        self.runner: web.AppRunner | None = None

    async def start(self) -> None:
        self.runner = web.AppRunner(self.api.app)
        await self.runner.setup()
        await web.TCPSite(self.runner, self.host, self.port).start()

    async def stop(self) -> None:
        if self.runner:
            await self.runner.cleanup()
            self.runner = None

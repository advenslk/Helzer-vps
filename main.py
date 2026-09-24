from __future__ import annotations

import asyncio

import docker
from sqlalchemy import select

from helzer.ai.assistant import AIAssistant
from helzer.api.agent import AgentAPI
from helzer.api.server import AgentServer
from helzer.bot import HelzerBot
from helzer.core.permissions import admin_user_ids
from helzer.core.config import Settings
from helzer.database.database import create_database, init_database
from helzer.database.models import VPS
from helzer.docker.manager import DockerManager
from helzer.services.port_service import PortService
from helzer.services.vps_service import VPSService


async def build_bot(settings: Settings) -> tuple[HelzerBot, AgentServer | None]:
    engine, sessions = create_database(settings.database_url)
    await init_database(engine)
    ports = PortService()
    async with sessions() as session:
        stored_ports = await session.scalars(select(VPS.host_port).where(VPS.host_port.is_not(None)))
        for port in stored_ports:
            ports.reserve(int(port))
    client = docker.DockerClient(base_url=settings.docker_host)
    client.ping()
    service = VPSService(sessions, DockerManager(client), ports)
    ai = AIAssistant(model=settings.ai_model, api_key=settings.ai_api_key, endpoint=settings.ai_endpoint)
    bot = HelzerBot(guild_id=settings.admin_guild_id, service=service, ai=ai)

    agent_server = None
    if settings.agent_api_token:
        agent_server = AgentServer(AgentAPI(service, settings.agent_api_token), settings.agent_api_host, settings.agent_api_port)
        await agent_server.start()
    return bot, agent_server


async def main() -> None:
    settings = Settings.from_env()
    bot, agent_server = await build_bot(settings)
    try:
        await bot.start(settings.discord_token)
    finally:
        if agent_server:
            await agent_server.stop()


if __name__ == "__main__":
    asyncio.run(main())

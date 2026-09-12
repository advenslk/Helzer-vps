from __future__ import annotations

import docker

from helzer.ai.assistant import AIAssistant
from helzer.bot import HelzerBot
from helzer.core.config import Settings
from helzer.database.database import create_database, init_database
from helzer.docker.manager import DockerManager
from helzer.services.port_service import PortService
from helzer.services.vps_service import VPSService


async def build_bot() -> HelzerBot:
    settings = Settings.from_env()
    engine, sessions = create_database(settings.database_url)
    await init_database(engine)
    client = docker.DockerClient(base_url=settings.docker_host)
    client.ping()
    service = VPSService(sessions, DockerManager(client), PortService())
    ai = AIAssistant(model=settings.ai_model, api_key=settings.ai_api_key)
    return HelzerBot(guild_id=settings.admin_guild_id, service=service, ai=ai)


async def main() -> None:
    bot = await build_bot()
    settings = Settings.from_env()
    await bot.start(settings.discord_token)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

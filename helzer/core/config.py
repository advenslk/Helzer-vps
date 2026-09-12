from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    discord_token: str
    admin_guild_id: int
    database_url: str
    docker_host: str = "unix:///var/run/docker.sock"
    ai_model: str = ""
    ai_api_key: str = ""
    ai_endpoint: str = "https://api.openai.com/v1/chat/completions"

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("DISCORD_TOKEN")
        guild_id = os.getenv("ADMIN_GUILD_ID")
        if not token:
            raise ValueError("DISCORD_TOKEN is required")
        if not guild_id:
            raise ValueError("ADMIN_GUILD_ID is required")
        return cls(
            discord_token=token,
            admin_guild_id=int(guild_id),
            database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///helzer.db"),
            docker_host=os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock"),
            ai_model=os.getenv("AI_MODEL", ""),
            ai_api_key=os.getenv("AI_API_KEY", ""),
            ai_endpoint=os.getenv("AI_ENDPOINT", "https://api.openai.com/v1/chat/completions"),
        )

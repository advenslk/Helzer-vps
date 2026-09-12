from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    discord_token: str
    admin_guild_id: int
    database_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("DISCORD_TOKEN")
        guild_id = os.getenv("ADMIN_GUILD_ID")
        database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///helzer.db")

        if not token:
            raise ValueError("DISCORD_TOKEN is required")
        if not guild_id:
            raise ValueError("ADMIN_GUILD_ID is required")

        return cls(
            discord_token=token,
            admin_guild_id=int(guild_id),
            database_url=database_url,
        )

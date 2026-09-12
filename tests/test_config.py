from helzer.core.config import Settings


def test_settings_reads_environment(monkeypatch):
    monkeypatch.setenv("DISCORD_TOKEN", "token")
    monkeypatch.setenv("ADMIN_GUILD_ID", "123")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///helzer.db")

    settings = Settings.from_env()

    assert settings.discord_token == "token"
    assert settings.admin_guild_id == 123
    assert settings.database_url.endswith("helzer.db")

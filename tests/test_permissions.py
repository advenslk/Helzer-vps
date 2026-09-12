from helzer.core.permissions import is_admin


def test_admin_matches_configured_guild_owner(monkeypatch):
    monkeypatch.setenv("ADMIN_USER_IDS", "123,456")
    assert is_admin(123) is True
    assert is_admin(999) is False


def test_admin_list_ignores_invalid_values(monkeypatch):
    monkeypatch.setenv("ADMIN_USER_IDS", "bad,123, ,456")
    assert is_admin(123) is True
    assert is_admin(456) is True
    assert is_admin(0) is False

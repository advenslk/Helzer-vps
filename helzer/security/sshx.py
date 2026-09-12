from __future__ import annotations

import secrets
import time
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SSHSession:
    token: str
    vps_id: int
    expires_at: int


class SSHSessionManager:
    """Issue short-lived, revocable SSH handoff tokens without storing secrets."""

    def __init__(self, ttl_seconds: int = 900):
        if ttl_seconds < 60:
            raise ValueError("SSH session TTL must be at least 60 seconds")
        self.ttl_seconds = ttl_seconds
        self._sessions: dict[str, SSHSession] = {}

    def issue(self, vps_id: int) -> SSHSession:
        token = secrets.token_urlsafe(32)
        session = SSHSession(token, vps_id, int(time.time()) + self.ttl_seconds)
        self._sessions[token] = session
        return session

    def validate(self, token: str, vps_id: int) -> bool:
        session = self._sessions.get(token)
        if not session or session.vps_id != vps_id:
            return False
        if session.expires_at <= int(time.time()):
            self._sessions.pop(token, None)
            return False
        return True

    def revoke(self, token: str) -> None:
        self._sessions.pop(token, None)

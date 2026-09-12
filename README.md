# Helzer VPS

Discord-only Docker VPS hosting with an optional AI admin planner.

## What is implemented

- Discord slash commands under `/vps` and `/admin`
- Components V2 VPS control panel
- Docker lifecycle: create, start, stop, restart, delete, logs and resource stats
- SQLite/SQLAlchemy persistence
- CPU/RAM resource limits and Docker image allowlist
- Port allocation service
- Admin-only natural-language AI provisioning
- Automatic VPS-ready DM after AI provisioning
- Configurable OpenAI-compatible AI endpoint
- Docker Compose deployment
- GitHub Actions test workflow

## Setup

1. Copy `.env.example` to `.env`.
2. Set `DISCORD_TOKEN`, `ADMIN_GUILD_ID`, and `ADMIN_USER_IDS`.
3. Set `AI_MODEL` and `AI_API_KEY` if AI planning is wanted.
4. Ensure Docker is available to the bot. The Compose deployment mounts the Docker socket.
5. Run `docker compose up -d --build`.

The bot intentionally keeps AI execution behind `VPSService`; the model does not receive arbitrary Docker shell access.

## Important production notes

- The Docker socket is highly privileged. Run Helzer on a dedicated host/node and restrict host access.
- Disk is currently a requested quota stored with the VPS record; hard filesystem quota enforcement should be added before selling hard storage guarantees.
- SSHX one-time session provisioning is reserved for the SSH service layer; no session credentials are persisted by the current panel.

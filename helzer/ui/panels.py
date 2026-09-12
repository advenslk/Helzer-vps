from __future__ import annotations

import discord
from discord import ui

from helzer.emoji import E


class VPSPanel(ui.LayoutView):
    def __init__(self, vps: dict[str, object], service):
        super().__init__(timeout=300)
        self.vps = vps
        self.service = service
        self._build()

    def _build(self) -> None:
        self.clear_items()
        status = str(self.vps.get("status", "unknown")).upper()
        text = (
            f"# {E.VPS} {self.vps.get('name', 'VPS')}\n"
            f"**ID:** `HX-{self.vps.get('id', 'PENDING')}`\n"
            f"**Status:** {E.RUNNING if status == 'RUNNING' else E.STOPPED} `{status}`\n\n"
            f"{E.CPU} **CPU** `{self.vps.get('cpu_cores', 0)} cores`\n"
            f"{E.RAM} **RAM** `{self.vps.get('ram_mb', 0)} MB`\n"
            f"{E.STORAGE} **Disk** `{self.vps.get('disk_gb', 0)} GB`\n"
            f"{E.DOCKER} **Image** `{self.vps.get('image', 'unknown')}`"
        )
        container = ui.Container(
            ui.TextDisplay(text),
            ui.Separator(),
            ui.ActionRow(
                ui.Button(label="Start", emoji=E.START, style=discord.ButtonStyle.success, custom_id="vps:start"),
                ui.Button(label="Stop", emoji=E.STOP, style=discord.ButtonStyle.secondary, custom_id="vps:stop"),
                ui.Button(label="Restart", emoji=E.RESTART, style=discord.ButtonStyle.primary, custom_id="vps:restart"),
            ),
            ui.ActionRow(
                ui.Button(label="Stats", emoji=E.STATS, style=discord.ButtonStyle.secondary, custom_id="vps:stats"),
                ui.Button(label="Logs", emoji=E.LOGS, style=discord.ButtonStyle.secondary, custom_id="vps:logs"),
                ui.Button(label="SSH", emoji=E.SSH, style=discord.ButtonStyle.primary, custom_id="vps:ssh"),
                ui.Button(label="Delete", emoji=E.DELETE, style=discord.ButtonStyle.danger, custom_id="vps:delete"),
            ),
        )
        for row in container.children:
            for child in getattr(row, "children", []):
                child.callback = self._callback
        self.add_item(container)

    async def _callback(self, interaction: discord.Interaction) -> None:
        custom_id = getattr(interaction.data, "get", lambda *_: None)("custom_id") if interaction.data else None
        action = str(custom_id or "").split(":")[-1]
        if action == "ssh":
            await interaction.response.send_message(
                f"{E.SSH} SSH access setup is available for `{self.vps.get('name')}`. "
                "SSHX provisioning will use a one-time session and will never store the session secret.",
                ephemeral=True,
            )
            return
        if action == "stats":
            stats = await self.service.stats(int(self.vps["id"]))
            await interaction.response.send_message(
                f"{E.STATS} CPU `{stats['cpu_percent']:.1f}%` · RAM `{stats['memory_percent']:.1f}%` · "
                f"Network `{stats['net_rx_mb']:.1f}MB ↓ / {stats['net_tx_mb']:.1f}MB ↑`",
                ephemeral=True,
            )
            return
        if action == "logs":
            logs = await self.service.logs(int(self.vps["id"]))
            await interaction.response.send_message(f"```text\n{logs[-1900:]}\n```", ephemeral=True)
            return
        if action in {"start", "stop", "restart"}:
            updated = await self.service.action(int(self.vps["id"]), action)
            self.vps = updated
            self._build()
            await interaction.response.edit_message(view=self)
            return
        if action == "delete":
            await self.service.delete(int(self.vps["id"]))
            await interaction.response.send_message(f"{E.SUCCESS} VPS deleted.", ephemeral=True)
            self.stop()
            return

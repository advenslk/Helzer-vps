from __future__ import annotations

import discord
from discord import app_commands, ui
from discord.ext import commands

from helzer.ai.assistant import AIAssistant
from helzer.core.permissions import is_admin
from helzer.emoji import E
from helzer.services.vps_service import VPSService, VPSSpec
from helzer.ui.panels import VPSPanel


class HelzerBot(commands.Bot):
    def __init__(self, *, guild_id: int, service: VPSService, ai: AIAssistant):
        intents = discord.Intents.none()
        intents.guilds = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
        self.guild_id = guild_id
        self.service = service
        self.ai = ai

    async def setup_hook(self) -> None:
        await self.add_cog(VPSCog(self))
        guild = discord.Object(id=self.guild_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

    async def on_ready(self) -> None:
        print(f"Helzer VPS online as {self.user}")


class VPSCog(commands.Cog):
    vps = app_commands.Group(name="vps", description="Manage your VPS")
    admin = app_commands.Group(name="admin", description="Helzer administrator controls")

    def __init__(self, bot: HelzerBot):
        self.bot = bot

    @vps.command(name="list", description="List your VPS instances")
    async def list_vps(self, interaction: discord.Interaction) -> None:
        items = await self.bot.service.list_for_user(interaction.user.id)
        layout = ui.LayoutView()
        text = "\n".join(
            f"**HX-{v['id']}** · `{v['name']}` · {E.RUNNING if v['status'] == 'running' else E.STOPPED} `{v['status']}`"
            for v in items
        ) or "No VPS instances yet. Use `/vps create` to provision one."
        layout.add_item(ui.Container(ui.TextDisplay(f"# {E.VPS} Your VPS\n{text}")))
        await interaction.response.send_message(view=layout, ephemeral=True)

    @vps.command(name="manage", description="Open the interactive VPS control panel")
    @app_commands.describe(vps_id="Your VPS ID")
    async def manage_vps(self, interaction: discord.Interaction, vps_id: int) -> None:
        vps = await self.bot.service.get(vps_id)
        if not vps or vps["owner_id"] != interaction.user.id:
            await interaction.response.send_message(f"{E.ERROR} VPS not found.", ephemeral=True)
            return
        await interaction.response.send_message(view=VPSPanel(vps, self.bot.service), ephemeral=True)

    @vps.command(name="create", description="Create a VPS for yourself")
    @app_commands.describe(name="VPS name", cpu="CPU cores", ram_mb="RAM in MB", disk_gb="Disk in GB", image="Docker image")
    @app_commands.choices(image=[
        app_commands.Choice(name="Ubuntu 24.04", value="ubuntu:24.04"),
        app_commands.Choice(name="Debian 12", value="debian:12"),
        app_commands.Choice(name="Alpine 3.20", value="alpine:3.20"),
    ])
    async def create_vps(self, interaction: discord.Interaction, name: str, cpu: int, ram_mb: int, disk_gb: int, image: app_commands.Choice[str]) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            vps = await self.bot.service.create_vps(interaction.user.id, VPSSpec(name, cpu, ram_mb, disk_gb, image.value))
        except Exception as exc:
            await interaction.followup.send(f"{E.ERROR} Creation failed: `{exc}`", ephemeral=True)
            return
        await interaction.followup.send(f"{E.SUCCESS} VPS `HX-{vps['id']}` is ready.", ephemeral=True)

    async def _user_action(self, interaction: discord.Interaction, vps_id: int, action: str) -> None:
        vps = await self.bot.service.get(vps_id)
        if not vps or vps["owner_id"] != interaction.user.id:
            await interaction.response.send_message(f"{E.ERROR} VPS not found.", ephemeral=True)
            return
        try:
            await self.bot.service.action(vps_id, action)
            await interaction.response.send_message(f"{E.SUCCESS} `{action}` completed for `HX-{vps_id}`.", ephemeral=True)
        except Exception as exc:
            await interaction.response.send_message(f"{E.ERROR} `{exc}`", ephemeral=True)

    @vps.command(name="start", description="Start your VPS")
    @app_commands.describe(vps_id="VPS ID")
    async def start(self, interaction: discord.Interaction, vps_id: int) -> None:
        await self._user_action(interaction, vps_id, "start")

    @vps.command(name="stop", description="Stop your VPS")
    @app_commands.describe(vps_id="VPS ID")
    async def stop(self, interaction: discord.Interaction, vps_id: int) -> None:
        await self._user_action(interaction, vps_id, "stop")

    @vps.command(name="restart", description="Restart your VPS")
    @app_commands.describe(vps_id="VPS ID")
    async def restart(self, interaction: discord.Interaction, vps_id: int) -> None:
        await self._user_action(interaction, vps_id, "restart")

    @vps.command(name="logs", description="Show recent VPS logs")
    @app_commands.describe(vps_id="VPS ID")
    async def logs(self, interaction: discord.Interaction, vps_id: int) -> None:
        vps = await self.bot.service.get(vps_id)
        if not vps or vps["owner_id"] != interaction.user.id:
            await interaction.response.send_message(f"{E.ERROR} VPS not found.", ephemeral=True)
            return
        logs = await self.bot.service.logs(vps_id)
        await interaction.response.send_message(f"```text\n{logs[-1900:]}\n```", ephemeral=True)

    @admin.command(name="ai", description="Ask Helzer AI to perform a safe VPS admin operation")
    @app_commands.describe(prompt="Natural-language admin request")
    async def admin_ai(self, interaction: discord.Interaction, prompt: str) -> None:
        if not is_admin(interaction.user.id):
            await interaction.response.send_message(f"{E.ERROR} Admin access required.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        try:
            request = await self.bot.ai.parse_create_vps(prompt)
            member = interaction.guild.get_member(request.target_user_id) if interaction.guild else None
            if member is None:
                member = await self.bot.fetch_user(request.target_user_id)
            vps = await self.bot.service.create_vps(request.target_user_id, VPSSpec(f"Helzer-{request.target_user_id}", request.cpu_cores, request.ram_mb, request.disk_gb))
            try:
                await member.send(
                    f"# {E.SUCCESS} YOUR VPS IS READY\n**Name:** `{vps['name']}`\n**ID:** `HX-{vps['id']}`\n"
                    f"**CPU:** `{vps['cpu_cores']} cores`\n**RAM:** `{vps['ram_mb']} MB`\n**Disk:** `{vps['disk_gb']} GB`\n"
                    f"**Image:** `{vps['image']}`\n\nPlease reply with your feedback about the setup."
                )
            except discord.Forbidden:
                pass
            await interaction.followup.send(f"{E.SUCCESS} Created `HX-{vps['id']}` for <@{request.target_user_id}> and attempted the DM notification.", ephemeral=True)
        except Exception as exc:
            await interaction.followup.send(f"{E.ERROR} AI operation failed: `{exc}`", ephemeral=True)

    @admin.command(name="node", description="Show current Docker node capacity")
    async def admin_node(self, interaction: discord.Interaction) -> None:
        if not is_admin(interaction.user.id):
            await interaction.response.send_message(f"{E.ERROR} Admin access required.", ephemeral=True)
            return
        capacity = self.bot.service.docker.capacity()
        await interaction.response.send_message(
            f"# {E.DOCKER} Node Capacity\n**CPU:** `{capacity['available_cpu']:.1f}/{capacity['total_cpu']:.1f}` cores available\n"
            f"**RAM:** `{capacity['available_ram_mb']:.0f}/{capacity['total_ram_mb']:.0f}` MB available\n"
            f"**Containers:** `{int(capacity['containers'])}`",
            ephemeral=True,
        )

    @admin.command(name="vps", description="Inspect a VPS as an administrator")
    @app_commands.describe(vps_id="VPS ID")
    async def admin_vps(self, interaction: discord.Interaction, vps_id: int) -> None:
        if not is_admin(interaction.user.id):
            await interaction.response.send_message(f"{E.ERROR} Admin access required.", ephemeral=True)
            return
        vps = await self.bot.service.get(vps_id)
        if not vps:
            await interaction.response.send_message(f"{E.ERROR} VPS not found.", ephemeral=True)
            return
        await interaction.response.send_message(view=VPSPanel(vps, self.bot.service), ephemeral=True)

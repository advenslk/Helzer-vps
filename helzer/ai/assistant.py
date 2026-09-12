from __future__ import annotations

import asyncio
import json
import urllib.request

from helzer.ai.tools import ToolCall, tool_definitions, validate_tool_call
from helzer.core.ai_requests import CreateVPSRequest

class AIAssistant:
    """Provider-neutral AI planner. Models can propose only allowlisted tool calls."""
    def __init__(self, model: str = "", api_key: str = "", endpoint: str = "https://api.openai.com/v1/chat/completions"):
        self.model, self.api_key, self.endpoint = model, api_key, endpoint

    async def parse_create_vps(self, text: str) -> CreateVPSRequest:
        if not self.model or not self.api_key:
            return CreateVPSRequest.from_text(text)
        prompt = ("Extract a VPS creation request. Return JSON only with keys "
                  "target_user_id, ram_mb, cpu_cores, disk_gb. Do not invent values.\nRequest: " + text)
        values = await self._json(prompt)
        return CreateVPSRequest(target_user_id=int(values["target_user_id"]), ram_mb=int(values["ram_mb"]), cpu_cores=int(values["cpu_cores"]), disk_gb=int(values["disk_gb"]))

    async def plan(self, text: str) -> ToolCall:
        """Return one validated tool call; never executes it and never exposes shell access."""
        if not self.model or not self.api_key:
            req = await self.parse_create_vps(text)
            return validate_tool_call(ToolCall("create_vps", {"owner_id": req.target_user_id, "name": f"Helzer-{req.target_user_id}", "cpu_cores": req.cpu_cores, "ram_mb": req.ram_mb, "disk_gb": req.disk_gb}))
        prompt = ("You are Helzer VPS planner. Choose exactly one tool from this allowlist: "
                  + json.dumps(tool_definitions()) + "\nReturn JSON {name,arguments}. Never use shell, docker exec, secrets, or arbitrary commands.\nRequest: " + text)
        values = await self._json(prompt)
        return validate_tool_call(ToolCall(str(values["name"]), dict(values.get("arguments", {}))))

    async def _json(self, prompt: str) -> dict:
        payload = json.dumps({"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0, "response_format": {"type": "json_object"}}).encode()
        request = urllib.request.Request(self.endpoint, data=payload, headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, method="POST")
        response = await asyncio.to_thread(lambda: urllib.request.urlopen(request, timeout=20).read())
        data = json.loads(response)
        return json.loads(data["choices"][0]["message"]["content"])

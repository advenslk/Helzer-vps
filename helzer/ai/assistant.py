from __future__ import annotations

import json
import urllib.request

from helzer.core.ai_requests import CreateVPSRequest


class AIAssistant:
    """Optional OpenAI-compatible planner with a safe local fallback.

    The model proposes intent only; execution remains inside VPSService.
    """

    def __init__(self, model: str = "", api_key: str = "", endpoint: str = "https://api.openai.com/v1/chat/completions"):
        self.model = model
        self.api_key = api_key
        self.endpoint = endpoint

    async def parse_create_vps(self, text: str) -> CreateVPSRequest:
        if not self.model or not self.api_key:
            return CreateVPSRequest.from_text(text)

        prompt = (
            "Extract a VPS creation request. Return JSON only with keys "
            "target_user_id, ram_mb, cpu_cores, disk_gb. Do not invent values.\n"
            f"Request: {text}"
        )
        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }).encode()
        request = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        import asyncio
        response = await asyncio.to_thread(lambda: urllib.request.urlopen(request, timeout=20).read())
        data = json.loads(response)
        content = data["choices"][0]["message"]["content"]
        values = json.loads(content)
        return CreateVPSRequest(
            target_user_id=int(values["target_user_id"]),
            ram_mb=int(values["ram_mb"]),
            cpu_cores=int(values["cpu_cores"]),
            disk_gb=int(values["disk_gb"]),
        )

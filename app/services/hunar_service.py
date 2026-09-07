from __future__ import annotations

from typing import Any
import httpx

from app.core.config import get_settings


class HunarAPIError(RuntimeError):
    pass


class HunarService:
    BASE_URL = "https://api.voice.hunar.ai/external/v1"

    def __init__(self) -> None:
        self.settings = get_settings()

    def _headers(self) -> dict[str, str]:
        if not self.settings.HUNAR_API_KEY:
            raise HunarAPIError("HUNAR_API_KEY is not configured")
        return {"X-API-Key": self.settings.HUNAR_API_KEY, "Content-Type": "application/json"}

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        async with httpx.AsyncClient(timeout=self.settings.HUNAR_TIMEOUT_SECONDS) as client:
            response = await client.request(method, f"{self.BASE_URL}{path}", headers=self._headers(), **kwargs)
        if response.status_code >= 400:
            raise HunarAPIError(f"Hunar API {response.status_code}: {response.text[:1000]}")
        return response.json() if response.content else {}

    async def list_agents(self) -> Any:
        return await self.request("GET", "/agents/")

    async def get_agent(self, agent_id: str) -> Any:
        return await self.request("GET", f"/agents/{agent_id}/")

    async def list_numbers(self) -> Any:
        return await self.request("GET", "/numbers/")

    async def create_call(self, payload: dict[str, Any]) -> Any:
        return await self.request("POST", "/calls/", json=payload)

    async def create_bulk_calls(self, payload: dict[str, Any]) -> Any:
        return await self.request("POST", "/calls/bulk/", json=payload)

    async def get_call(self, call_id: str) -> Any:
        return await self.request("GET", f"/calls/{call_id}/")

    async def list_calls(self, **params: Any) -> Any:
        return await self.request("GET", "/calls/", params={k: v for k, v in params.items() if v is not None})

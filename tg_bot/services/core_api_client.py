from __future__ import annotations

from typing import Any, Dict

import httpx


class CoreApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def init_profile(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = await self._client.post("/profile/init", json=payload)
        response.raise_for_status()
        return response.json()

    async def log_daily_intake(self, payload: Dict[str, Any]) -> None:
        response = await self._client.post("/log/daily-intake", json=payload)
        response.raise_for_status()

    async def log_body(self, payload: Dict[str, Any]) -> None:
        response = await self._client.post("/log/body", json=payload)
        response.raise_for_status()

    async def get_progress_summary(self, telegram_id: str) -> Dict[str, Any]:
        response = await self._client.get("/progress/summary", params={"telegram_id": telegram_id})
        response.raise_for_status()
        return response.json()

    async def get_week_menu(self, telegram_id: str) -> Dict[str, Any]:
        response = await self._client.get("/menu/week", params={"telegram_id": telegram_id})
        response.raise_for_status()
        return response.json()

    async def get_weekly_report(self, telegram_id: str) -> Dict[str, Any]:
        response = await self._client.get("/report/weekly", params={"telegram_id": telegram_id})
        response.raise_for_status()
        return response.json()

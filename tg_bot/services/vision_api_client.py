from typing import Any, Dict

import httpx


class VisionApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=15.0)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def estimate_meal(self, image_bytes: bytes, filename: str) -> Dict[str, Any]:
        files = {"image": (filename, image_bytes, "image/jpeg")}
        response = await self._client.post("/vision/estimate_meal", files=files)
        response.raise_for_status()
        return response.json()

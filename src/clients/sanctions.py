"""Sanctions Client — EU/US Sanktionslisten-Prüfung (OpenSanctions API)."""

import httpx
from src.config import settings


class SanctionsClient:
    """Async-Client für OpenSanctions API + EU Consolidated Sanctions List.

    OpenSanctions aggregiert EU, US (OFAC/SDN), UN und weitere Listen.
    Basis-API ist gratis und ohne Key nutzbar.
    """

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=settings.http_timeout)
        self._base = settings.opensanctions_url

    async def search_entity(self, query: str, limit: int = 10) -> dict:
        """Nach Person oder Firma in Sanktionslisten suchen.

        Durchsucht EU, US OFAC/SDN, UN und weitere Listen gleichzeitig.
        """
        resp = await self._client.get(
            f"{self._base}/search/default",
            params={
                "q": query,
                "limit": min(limit, 50),
            },
        )
        resp.raise_for_status()
        return resp.json()

    async def match_entity(
        self,
        name: str,
        schema: str = "LegalEntity",
        countries: list[str] | None = None,
    ) -> dict:
        """Fuzzy-Match gegen Sanktionslisten (für KYC/AML-Screening).

        Args:
            name: Name der Person oder Firma
            schema: "LegalEntity" für Firmen, "Person" für Personen
            countries: Optionale Länderfilter (ISO-2-Codes)
        """
        payload = {
            "queries": {
                "q1": {
                    "schema": schema,
                    "properties": {
                        "name": [name],
                    },
                }
            }
        }
        if countries:
            payload["queries"]["q1"]["properties"]["country"] = countries

        resp = await self._client.post(
            f"{self._base}/match/default",
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self._client.aclose()

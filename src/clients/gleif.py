"""GLEIF Client — Firmensuche, LEI-Lookup, Konzernstrukturen."""

import httpx
from src.config import settings


class GleifClient:
    """Async-Client für GLEIF LEI API. Kein Key nötig. 60 req/min."""

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=settings.http_timeout)
        self._base = settings.gleif_base_url

    async def search_by_name(
        self, name: str, country: str = "", limit: int = 10,
    ) -> dict:
        """Firmen nach Name suchen (optional nach Land filtern)."""
        params = {
            "filter[fulltext]": name,
            "page[size]": min(limit, 50),
        }
        if country:
            params["filter[entity.legalAddress.country]"] = country.upper()
        resp = await self._client.get(f"{self._base}/lei-records", params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_by_lei(self, lei: str) -> dict:
        """Firma per LEI-Code abrufen."""
        resp = await self._client.get(f"{self._base}/lei-records/{lei}")
        resp.raise_for_status()
        return resp.json()

    async def search_by_register(
        self, register_number: str, country: str = "DE",
    ) -> dict:
        """Firma per Handelsregisternummer suchen."""
        params = {
            "filter[entity.registeredAs]": register_number,
            "filter[entity.legalAddress.country]": country.upper(),
        }
        resp = await self._client.get(f"{self._base}/lei-records", params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_direct_parent(self, lei: str) -> dict:
        """Direkte Muttergesellschaft abrufen."""
        resp = await self._client.get(f"{self._base}/lei-records/{lei}/direct-parent")
        resp.raise_for_status()
        return resp.json()

    async def get_ultimate_parent(self, lei: str) -> dict:
        """Oberste Konzernmutter abrufen."""
        resp = await self._client.get(f"{self._base}/lei-records/{lei}/ultimate-parent")
        resp.raise_for_status()
        return resp.json()

    async def get_direct_children(self, lei: str, limit: int = 20) -> dict:
        """Direkte Tochtergesellschaften abrufen."""
        resp = await self._client.get(
            f"{self._base}/lei-records/{lei}/direct-children",
            params={"page[size]": min(limit, 50)},
        )
        resp.raise_for_status()
        return resp.json()

    async def autocomplete(self, query: str) -> dict:
        """Autocomplete für Firmennamen."""
        resp = await self._client.get(
            f"{self._base}/autocompletions",
            params={"field": "fulltext", "q": query},
        )
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self._client.aclose()

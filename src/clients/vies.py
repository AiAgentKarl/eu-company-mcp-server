"""VIES Client — EU USt-ID Validierung."""

import httpx
from src.config import settings


class ViesClient:
    """Async-Client für VIES VAT Validation. Kein Key nötig."""

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=settings.http_timeout)
        self._base = settings.vies_base_url

    async def validate_vat(self, country_code: str, vat_number: str) -> dict:
        """USt-ID prüfen und Firmeninfos abrufen.

        Hinweis: Deutschland gibt nie Name/Adresse zurück (immer "---").
        Die meisten anderen EU-Länder geben Details zurück.
        """
        resp = await self._client.get(
            f"{self._base}/ms/{country_code.upper()}/vat/{vat_number}"
        )
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self._client.aclose()

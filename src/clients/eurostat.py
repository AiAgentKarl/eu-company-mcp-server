"""Eurostat Client — EU Wirtschafts- und Unternehmensstatistiken."""

import httpx
from src.config import settings


# Wichtige Dataset-Codes
DATASETS = {
    "gdp": "nama_10_gdp",
    "unemployment": "une_rt_m",
    "inflation": "prc_hicp_manr",
    "business_demography": "bd_9bd_sz_cl_r2",
}


class EurostatClient:
    """Async-Client für Eurostat API. Kein Key nötig."""

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=settings.http_timeout)
        self._base = settings.eurostat_base_url

    async def get_data(self, dataset: str, **params) -> dict:
        """Eurostat-Datensatz abfragen.

        Args:
            dataset: Dataset-Code (z.B. "nama_10_gdp")
            **params: Dimension-Filter (z.B. geo="DE", time="2023")
        """
        query_params = {"lang": "EN"}

        # Parameter in Eurostat-Format umwandeln
        for key, value in params.items():
            if isinstance(value, list):
                # Mehrere Werte: wiederholter Parameter
                for v in value:
                    query_params[key] = value
            else:
                query_params[key] = value

        resp = await self._client.get(
            f"{self._base}/{dataset}",
            params=query_params,
        )
        resp.raise_for_status()
        return resp.json()

    async def get_gdp(self, countries: list[str], years: list[str]) -> dict:
        """BIP für Länder abrufen."""
        params = {
            "geo": countries,
            "na_item": "B1GQ",
            "unit": "CP_MEUR",
            "time": years,
            "lang": "EN",
        }
        resp = await self._client.get(f"{self._base}/nama_10_gdp", params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_unemployment(self, countries: list[str], periods: list[str]) -> dict:
        """Arbeitslosenquote abrufen (monatlich, saisonbereinigt)."""
        params = {
            "geo": countries,
            "age": "TOTAL",
            "sex": "T",
            "s_adj": "SA",
            "unit": "PC_ACT",
            "time": periods,
            "lang": "EN",
        }
        resp = await self._client.get(f"{self._base}/une_rt_m", params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_inflation(self, countries: list[str], periods: list[str]) -> dict:
        """Inflationsrate (HICP) abrufen."""
        params = {
            "coicop": "CP00",
            "geo": countries,
            "time": periods,
            "lang": "EN",
        }
        resp = await self._client.get(f"{self._base}/prc_hicp_manr", params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_business_demography(
        self, countries: list[str], year: str = "2021",
    ) -> dict:
        """Unternehmensdemografie (Gründungen, Schließungen, aktive Firmen)."""
        params = {
            "geo": countries,
            "indic_sb": ["V11910", "V11920", "V11930"],
            "nace_r2": "B-S_X_K642",
            "sizeclas": "TOTAL",
            "time": year,
            "lang": "EN",
        }
        resp = await self._client.get(f"{self._base}/bd_9bd_sz_cl_r2", params=params)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self._client.aclose()

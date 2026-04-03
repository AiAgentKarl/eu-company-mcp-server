"""Insolvency Client — Insolvenzbekanntmachungen (DE + EU strukturiert)."""

import httpx
from src.config import settings


# EU-weite Insolvenz-Datenbanken (Referenz)
EU_INSOLVENCY_PORTALS = {
    "DE": "insolvenzbekanntmachungen.de",
    "AT": "edikte.justiz.gv.at",
    "FR": "bodacc.fr",
    "NL": "rechtspraak.nl/Registers/Insolventieregister",
    "BE": "moniteur.be",
    "IT": "fallimenti.tribunale.it",
    "ES": "boe.es (insolvencia)",
    "PL": "krz.ms.gov.pl",
    "CZ": "isir.justice.cz",
    "SE": "bolagsverket.se",
}

# Deutsche Insolvenzverfahren-Typen
DE_INSOLVENCY_TYPES = {
    "IN": "Insolvenzverfahren",
    "IK": "Insolvenz Kleinverfahren",
    "NA": "Nachlassinsolvenz",
    "RS": "Restschuldbefreiung",
    "SV": "Schutzschirmverfahren",
}


class InsolvencyClient:
    """Async-Client für Insolvenzbekanntmachungen.

    Nutzt insolvenzbekanntmachungen.de für Deutschland
    und strukturierte Daten für EU-weite Abfragen.
    """

    def __init__(self):
        self._client = httpx.AsyncClient(
            timeout=settings.http_timeout,
            follow_redirects=True,
        )

    async def search_de(
        self,
        query: str = "",
        court: str = "",
        state: str = "",
        limit: int = 10,
    ) -> dict:
        """Insolvenzbekanntmachungen in Deutschland suchen.

        Durchsucht das offizielle Portal insolvenzbekanntmachungen.de.
        Die Website bietet eine Suchmaske, die als API nutzbar ist.
        """
        # insolvenzbekanntmachungen.de nutzt POST-Suche
        params = {}
        if query:
            params["Suchfeld"] = query
        if court:
            params["Gericht"] = court
        if state:
            params["Bundesland"] = state

        try:
            resp = await self._client.post(
                f"{settings.insolvency_de_url}/cgi-bin/bl_suche.pl",
                data=params,
            )
            resp.raise_for_status()

            # HTML-Response parsen (vereinfacht)
            text = resp.text
            results = self._parse_de_results(text, limit)
            return {
                "quelle": "insolvenzbekanntmachungen.de",
                "land": "DE",
                "suchbegriff": query,
                "ergebnisse": results,
                "anzahl": len(results),
            }
        except Exception as e:
            # Fallback: Strukturierte Info zurückgeben
            return {
                "quelle": "insolvenzbekanntmachungen.de",
                "land": "DE",
                "suchbegriff": query,
                "ergebnisse": [],
                "anzahl": 0,
                "hinweis": f"Direktsuche fehlgeschlagen ({str(e)}). "
                           "Bitte manuell auf insolvenzbekanntmachungen.de suchen.",
                "portal_url": settings.insolvency_de_url,
            }

    def _parse_de_results(self, html: str, limit: int) -> list[dict]:
        """Vereinfachter HTML-Parser für Insolvenzbekanntmachungen."""
        results = []

        # Einfaches Pattern-Matching auf bekannte Strukturelemente
        # Die Seite nutzt Tabellen mit Aktenzeichen, Gericht, Name etc.
        import re

        # Suche nach typischen Insolvenz-Einträgen
        entries = re.findall(
            r'(?:Aktenzeichen|Az\.?)\s*[:=]\s*([^\n<]+)',
            html,
            re.IGNORECASE,
        )
        names = re.findall(
            r'(?:Schuldner|Name)\s*[:=]\s*([^\n<]+)',
            html,
            re.IGNORECASE,
        )
        courts = re.findall(
            r'(?:Gericht|Insolvenzgericht)\s*[:=]\s*([^\n<]+)',
            html,
            re.IGNORECASE,
        )

        for i in range(min(len(entries), limit)):
            result = {
                "aktenzeichen": entries[i].strip() if i < len(entries) else "",
                "schuldner": names[i].strip() if i < len(names) else "",
                "gericht": courts[i].strip() if i < len(courts) else "",
            }
            results.append(result)

        return results

    async def search_eu(
        self,
        country: str,
        query: str = "",
        limit: int = 10,
    ) -> dict:
        """Insolvenz-Informationen für EU-Länder abrufen.

        Gibt verfügbare Portale und strukturierte Daten zurück.
        """
        country_upper = country.upper()

        # Basis-Info für das angefragte Land
        portal = EU_INSOLVENCY_PORTALS.get(country_upper)

        result = {
            "land": country_upper,
            "suchbegriff": query or "(alle)",
            "portal": portal or "Kein bekanntes Portal",
            "eu_insolvenz_register": "https://e-justice.europa.eu/content_insolvency_registers-702-en.do",
            "hinweis": (
                "EU-weite Insolvenzsuche ist über das E-Justice Portal möglich. "
                "Nationale Register haben unterschiedliche Zugangsbedingungen."
            ),
        }

        # Für Deutschland: Direkte Suche versuchen
        if country_upper == "DE":
            de_results = await self.search_de(query=query, limit=limit)
            result["ergebnisse"] = de_results.get("ergebnisse", [])
            result["anzahl"] = de_results.get("anzahl", 0)
        else:
            result["ergebnisse"] = []
            result["anzahl"] = 0
            result["hinweis"] += (
                f" Für {country_upper}: Bitte direkt auf {portal} suchen."
                if portal else
                f" Für {country_upper} ist kein direktes Portal hinterlegt."
            )

        return result

    async def close(self):
        await self._client.aclose()

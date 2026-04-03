"""Beneficial Owners Client — Wirtschaftlich Berechtigte (EU AML Directive).

Nutzt OpenSanctions + GLEIF für Beneficial-Ownership-Daten.
EU Anti-Money Laundering Directive (AMLD) verlangt öffentliche Register.
"""

import httpx
from src.config import settings


# EU Transparenzregister nach Land
EU_OWNERSHIP_REGISTERS = {
    "DE": {
        "name": "Transparenzregister",
        "url": "https://www.transparenzregister.de",
        "zugang": "Registrierung erforderlich, gebührenpflichtig",
    },
    "AT": {
        "name": "Wirtschaftliches Eigentümerregister (WiEReG)",
        "url": "https://www.bmf.gv.at/themen/finanzmarkt/geldwaesche/WiEReG.html",
        "zugang": "Registrierung erforderlich",
    },
    "FR": {
        "name": "Registre des Bénéficiaires Effectifs (RBE)",
        "url": "https://data.inpi.fr",
        "zugang": "Kostenlos über INPI Open Data",
    },
    "NL": {
        "name": "UBO-register",
        "url": "https://www.kvk.nl/ubo-register/",
        "zugang": "Über KVK (Handelskammer)",
    },
    "LU": {
        "name": "Registre des Bénéficiaires Effectifs (RBE)",
        "url": "https://www.lbr.lu",
        "zugang": "Kostenlos einsehbar",
    },
    "BE": {
        "name": "UBO-Register",
        "url": "https://finances.belgium.be/fr/E-services/ubo-register",
        "zugang": "Registrierung erforderlich",
    },
    "IT": {
        "name": "Registro dei Titolari Effettivi",
        "url": "https://www.mise.gov.it",
        "zugang": "Über Handelskammern",
    },
    "ES": {
        "name": "Registro de Titularidades Reales",
        "url": "https://www.registradores.org",
        "zugang": "Über Notare/Registerführer",
    },
    "IE": {
        "name": "Register of Beneficial Ownership (RBO)",
        "url": "https://rbo.gov.ie",
        "zugang": "Kostenlos einsehbar",
    },
    "DK": {
        "name": "Ejerregistret",
        "url": "https://datacvr.virk.dk",
        "zugang": "Kostenlos über CVR",
    },
    "SE": {
        "name": "Verklig huvudman (Bolagsverket)",
        "url": "https://bolagsverket.se",
        "zugang": "Registrierung erforderlich",
    },
    "FI": {
        "name": "Tosiasiallisten edunsaajien rekisteri (PRH)",
        "url": "https://www.prh.fi",
        "zugang": "Teilweise kostenlos",
    },
    "PL": {
        "name": "Centralny Rejestr Beneficjentów Rzeczywistych (CRBR)",
        "url": "https://crbr.podatki.gov.pl",
        "zugang": "Kostenlos einsehbar",
    },
    "CZ": {
        "name": "Evidence skutečných majitelů",
        "url": "https://esm.justice.cz",
        "zugang": "Kostenlos einsehbar",
    },
}


class BeneficialOwnersClient:
    """Client für Beneficial-Ownership-Daten (wirtschaftlich Berechtigte).

    Kombiniert OpenSanctions-Daten mit GLEIF-Ownership und
    nationalen Transparenzregister-Infos.
    """

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=settings.http_timeout)
        self._opensanctions_base = settings.opensanctions_url
        self._gleif_base = settings.gleif_base_url

    async def lookup_ownership(self, company_name: str, country: str = "") -> dict:
        """Wirtschaftlich Berechtigte einer Firma suchen.

        Kombiniert:
        1. OpenSanctions Ownership-Daten (falls vorhanden)
        2. GLEIF Relationship-Daten (Konzernstruktur)
        3. Nationales Transparenzregister-Info
        """
        country_upper = country.upper() if country else ""
        result = {
            "firma": company_name,
            "land": country_upper or "unbekannt",
            "beneficial_owners": [],
            "konzern_eigentümer": [],
            "register_info": None,
            "rechtsgrundlage": "EU Anti-Money Laundering Directive (AMLD 5/6)",
        }

        # 1. OpenSanctions durchsuchen (Ownership-Daten)
        try:
            os_data = await self._search_opensanctions(company_name)
            owners = self._extract_ownership(os_data)
            result["beneficial_owners"] = owners
        except Exception:
            result["beneficial_owners"] = []

        # 2. GLEIF-Daten (Konzernstruktur/Muttergesellschaft)
        try:
            gleif_data = await self._search_gleif(company_name, country_upper)
            parent_info = self._extract_gleif_ownership(gleif_data)
            result["konzern_eigentümer"] = parent_info
        except Exception:
            result["konzern_eigentümer"] = []

        # 3. Nationales Register-Info
        if country_upper in EU_OWNERSHIP_REGISTERS:
            result["register_info"] = EU_OWNERSHIP_REGISTERS[country_upper]
        else:
            result["register_info"] = {
                "hinweis": (
                    f"Kein Transparenzregister für '{country_upper}' hinterlegt. "
                    "EU-Mitgliedstaaten sind seit AMLD5 verpflichtet, "
                    "ein öffentliches Register zu führen."
                ),
            }

        return result

    async def _search_opensanctions(self, name: str) -> dict:
        """OpenSanctions nach Ownership-Daten durchsuchen."""
        resp = await self._client.get(
            f"{self._opensanctions_base}/search/default",
            params={
                "q": name,
                "schema": "LegalEntity",
                "limit": 5,
            },
        )
        resp.raise_for_status()
        return resp.json()

    async def _search_gleif(self, name: str, country: str) -> dict:
        """GLEIF nach Firma und deren Beziehungen suchen."""
        params = {
            "filter[fulltext]": name,
            "page[size]": 3,
        }
        if country:
            params["filter[entity.legalAddress.country]"] = country

        resp = await self._client.get(
            f"{self._gleif_base}/lei-records",
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

    def _extract_ownership(self, data: dict) -> list[dict]:
        """Ownership-Daten aus OpenSanctions extrahieren."""
        owners = []
        for result in data.get("results", []):
            props = result.get("properties", {})
            owner_entry = {
                "name": props.get("name", [""])[0] if props.get("name") else "",
                "typ": result.get("schema", ""),
                "land": props.get("country", [""])[0] if props.get("country") else "",
                "datasets": [d.get("name", "") for d in result.get("datasets", [])],
                "score": result.get("score", 0),
            }
            if owner_entry["name"]:
                owners.append(owner_entry)
        return owners

    def _extract_gleif_ownership(self, data: dict) -> list[dict]:
        """Konzern-Ownership aus GLEIF extrahieren."""
        owners = []
        for record in data.get("data", []):
            attrs = record.get("attributes", {})
            entity = attrs.get("entity", {})
            owners.append({
                "name": entity.get("legalName", {}).get("name", ""),
                "lei": attrs.get("lei", ""),
                "status": entity.get("status", ""),
                "land": entity.get("jurisdiction", ""),
            })
        return owners

    async def close(self):
        await self._client.aclose()

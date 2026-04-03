"""Compliance-Tools — Insolvenzen, Beneficial Owners, Sanktionen."""

from mcp.server.fastmcp import FastMCP
from src.clients.insolvency import InsolvencyClient
from src.clients.beneficial_owners import BeneficialOwnersClient
from src.clients.sanctions import SanctionsClient

_insolvency = InsolvencyClient()
_beneficial = BeneficialOwnersClient()
_sanctions = SanctionsClient()


def register_compliance_tools(mcp: FastMCP):

    @mcp.tool()
    async def search_insolvencies(
        country: str, query: str = "", limit: int = 10,
    ) -> dict:
        """Nach Firmen-Insolvenzen/Konkursen in EU-Ländern suchen.

        Durchsucht nationale Insolvenzregister. Für Deutschland wird
        insolvenzbekanntmachungen.de direkt abgefragt, für andere
        EU-Länder werden die zuständigen Portale angegeben.

        Nützlich für: Due Diligence, Kreditprüfung, Lieferanten-Check.

        Args:
            country: ISO-Ländercode (z.B. "DE", "AT", "FR")
            query: Firmenname oder Suchbegriff (leer = alle)
            limit: Max. Ergebnisse (1-50)
        """
        data = await _insolvency.search_eu(
            country=country,
            query=query,
            limit=min(limit, 50),
        )

        return {
            "land": data.get("land", country.upper()),
            "suchbegriff": query or "(alle)",
            "treffer": data.get("anzahl", 0),
            "ergebnisse": data.get("ergebnisse", []),
            "portal": data.get("portal", ""),
            "eu_portal": data.get("eu_insolvenz_register", ""),
            "hinweis": data.get("hinweis", ""),
        }

    @mcp.tool()
    async def get_beneficial_owners(
        company_name: str, country: str = "",
    ) -> dict:
        """Wirtschaftlich Berechtigte (Beneficial Owners) einer Firma ermitteln.

        Sucht nach den echten Eigentümern hinter einer Firma.
        Kombiniert OpenSanctions-Daten, GLEIF-Konzernstrukturen
        und nationale Transparenzregister-Informationen.

        Rechtsgrundlage: EU Anti-Money Laundering Directive (AMLD 5/6)
        verpflichtet alle EU-Staaten zu öffentlichen Registern.

        Nützlich für: AML/KYC-Prüfungen, Due Diligence, Compliance.

        Args:
            company_name: Name der Firma (z.B. "Wirecard AG", "Danske Bank")
            country: ISO-Ländercode (z.B. "DE", "NL"). Leer = weltweit suchen.
        """
        data = await _beneficial.lookup_ownership(company_name, country)

        return {
            "firma": data.get("firma", company_name),
            "land": data.get("land", ""),
            "beneficial_owners": data.get("beneficial_owners", []),
            "konzern_eigentümer": data.get("konzern_eigentümer", []),
            "transparenzregister": data.get("register_info"),
            "rechtsgrundlage": data.get("rechtsgrundlage", ""),
            "hinweis": (
                "Vollständige Beneficial-Ownership-Daten sind oft nur "
                "in nationalen Transparenzregistern verfügbar. "
                "Hier gezeigte Daten stammen aus öffentlichen Quellen."
            ),
        }

    @mcp.tool()
    async def check_sanctions(
        company_name: str, include_persons: bool = False,
    ) -> dict:
        """Prüfen ob eine Firma oder Person auf Sanktionslisten steht.

        Durchsucht gleichzeitig:
        - EU Consolidated Sanctions List
        - US OFAC/SDN List (Treasury)
        - UN Security Council Sanctions
        - Weitere nationale Listen

        Quelle: OpenSanctions (aggregiert 90+ Datensätze).

        Nützlich für: Compliance-Screening, KYC, AML, Export-Kontrolle.

        Args:
            company_name: Name der Firma oder Person
            include_persons: Auch Personen mit ähnlichem Namen suchen (Standard: nur Firmen)
        """
        results = []
        is_sanctioned = False
        matched_lists = []

        # Firmen-Check (LegalEntity)
        try:
            company_data = await _sanctions.match_entity(
                name=company_name,
                schema="LegalEntity",
            )
            # Responses aus match_entity extrahieren
            for query_id, response in company_data.get("responses", {}).items():
                for result in response.get("results", []):
                    score = result.get("score", 0)
                    if score > 0.5:  # Nur relevante Treffer
                        props = result.get("properties", {})
                        datasets = [
                            d.get("name", "") for d in result.get("datasets", [])
                        ]
                        entry = {
                            "name": props.get("name", [""])[0] if props.get("name") else "",
                            "typ": "Firma",
                            "übereinstimmung": round(score * 100, 1),
                            "land": props.get("country", [""])[0] if props.get("country") else "",
                            "listen": datasets,
                            "schema": result.get("schema", ""),
                            "id": result.get("id", ""),
                        }
                        results.append(entry)
                        if score > 0.7:
                            is_sanctioned = True
                            matched_lists.extend(datasets)
        except Exception:
            pass

        # Optional: Personen-Check
        if include_persons:
            try:
                person_data = await _sanctions.match_entity(
                    name=company_name,
                    schema="Person",
                )
                for query_id, response in person_data.get("responses", {}).items():
                    for result in response.get("results", []):
                        score = result.get("score", 0)
                        if score > 0.5:
                            props = result.get("properties", {})
                            datasets = [
                                d.get("name", "") for d in result.get("datasets", [])
                            ]
                            entry = {
                                "name": props.get("name", [""])[0] if props.get("name") else "",
                                "typ": "Person",
                                "übereinstimmung": round(score * 100, 1),
                                "land": props.get("country", [""])[0] if props.get("country") else "",
                                "listen": datasets,
                                "schema": result.get("schema", ""),
                                "id": result.get("id", ""),
                            }
                            results.append(entry)
                            if score > 0.7:
                                is_sanctioned = True
                                matched_lists.extend(datasets)
            except Exception:
                pass

        # Ergebnis sortiert nach Score
        results.sort(key=lambda x: x.get("übereinstimmung", 0), reverse=True)

        return {
            "geprüft": company_name,
            "sanktioniert": is_sanctioned,
            "treffer": len(results),
            "betroffene_listen": list(set(matched_lists)),
            "ergebnisse": results[:20],  # Max 20 Treffer
            "datenquellen": [
                "EU Consolidated Sanctions List",
                "US OFAC/SDN List",
                "UN Security Council Sanctions",
                "OpenSanctions (90+ Datensätze)",
            ],
            "hinweis": (
                "ACHTUNG: Sanktioniert!" if is_sanctioned else
                "Kein Treffer auf bekannten Sanktionslisten."
            ),
        }

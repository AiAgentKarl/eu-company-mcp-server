"""Company-Tools — Firmensuche, LEI-Lookup, Konzernstrukturen (GLEIF)."""

from mcp.server.fastmcp import FastMCP
from src.clients.gleif import GleifClient

_gleif = GleifClient()


def _parse_entity(record: dict) -> dict:
    """GLEIF-Record in lesbares Format umwandeln."""
    attrs = record.get("attributes", {})
    entity = attrs.get("entity", {})
    legal_addr = entity.get("legalAddress", {})
    hq_addr = entity.get("headquartersAddress", {})
    reg = attrs.get("registration", {})

    return {
        "lei": attrs.get("lei", ""),
        "name": entity.get("legalName", {}).get("name", ""),
        "status": entity.get("status", ""),
        "rechtsform": entity.get("legalForm", {}).get("id", ""),
        "registernummer": entity.get("registeredAs", ""),
        "jurisdiktion": entity.get("jurisdiction", ""),
        "gruendung": entity.get("creationDate", ""),
        "adresse": {
            "strasse": ", ".join(legal_addr.get("addressLines", [])),
            "plz": legal_addr.get("postalCode", ""),
            "stadt": legal_addr.get("city", ""),
            "land": legal_addr.get("country", ""),
        },
        "hauptsitz": {
            "stadt": hq_addr.get("city", ""),
            "land": hq_addr.get("country", ""),
        },
        "registrierung_status": reg.get("status", ""),
        "bic_codes": attrs.get("bic", []),
    }


def register_company_tools(mcp: FastMCP):

    @mcp.tool()
    async def company_search(
        name: str, country: str = "", limit: int = 10,
    ) -> dict:
        """Firmen in der GLEIF-Datenbank suchen (weltweit, 2M+ Einträge).

        Findet Unternehmen nach Name mit LEI, Adresse, Registernummer,
        Rechtsform und Gründungsdatum. Perfekt für Due Diligence und KYC.

        Args:
            name: Firmenname oder Suchbegriff (z.B. "Siemens", "Deutsche Bank")
            country: ISO-Ländercode (z.B. "DE", "FR", "US"). Leer = weltweit.
            limit: Max. Ergebnisse (1-50)
        """
        data = await _gleif.search_by_name(name, country, limit)
        records = data.get("data", [])
        total = data.get("meta", {}).get("pagination", {}).get("total", 0)

        firmen = [_parse_entity(r) for r in records]

        return {
            "suchbegriff": name,
            "land_filter": country or "weltweit",
            "treffer_gesamt": total,
            "firmen": firmen,
        }

    @mcp.tool()
    async def company_by_lei(lei: str) -> dict:
        """Firma per LEI-Code abrufen (volle Details).

        LEI = Legal Entity Identifier, 20-stelliger Code.
        Gibt alle verfügbaren Daten inkl. BIC-Codes und Events.

        Args:
            lei: LEI-Code (z.B. "7LTWFZYICNSX8D621K86" für Deutsche Bank)
        """
        data = await _gleif.get_by_lei(lei)
        record = data.get("data", {})
        return _parse_entity(record)

    @mcp.tool()
    async def company_by_register(
        register_number: str, country: str = "DE",
    ) -> dict:
        """Firma per Handelsregisternummer suchen.

        Args:
            register_number: Registernummer (z.B. "HRB 30000")
            country: Ländercode (Standard: DE)
        """
        data = await _gleif.search_by_register(register_number, country)
        records = data.get("data", [])

        firmen = [_parse_entity(r) for r in records]

        return {
            "registernummer": register_number,
            "land": country,
            "treffer": len(firmen),
            "firmen": firmen,
        }

    @mcp.tool()
    async def company_structure(lei: str, limit: int = 20) -> dict:
        """Konzernstruktur einer Firma abrufen (Mutter + Töchter).

        Zeigt die direkte Muttergesellschaft, die oberste Konzernmutter
        und alle direkten Tochtergesellschaften.

        Args:
            lei: LEI-Code der Firma
            limit: Max. Tochtergesellschaften (1-50)
        """
        result = {
            "lei": lei,
            "direct_parent": None,
            "ultimate_parent": None,
            "direct_children": [],
            "children_count": 0,
        }

        # Muttergesellschaft
        try:
            parent = await _gleif.get_direct_parent(lei)
            parent_data = parent.get("data", {})
            if parent_data:
                result["direct_parent"] = _parse_entity(parent_data)
        except Exception:
            pass

        # Oberste Konzernmutter
        try:
            ultimate = await _gleif.get_ultimate_parent(lei)
            ult_data = ultimate.get("data", {})
            if ult_data:
                result["ultimate_parent"] = _parse_entity(ult_data)
        except Exception:
            pass

        # Tochtergesellschaften
        try:
            children = await _gleif.get_direct_children(lei, limit)
            children_data = children.get("data", [])
            total = children.get("meta", {}).get("pagination", {}).get("total", 0)

            result["direct_children"] = [_parse_entity(c) for c in children_data]
            result["children_count"] = total
        except Exception:
            pass

        return result

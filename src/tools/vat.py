"""VAT-Tools — EU USt-ID Validierung (VIES)."""

from mcp.server.fastmcp import FastMCP
from src.clients.vies import ViesClient

_vies = ViesClient()


def register_vat_tools(mcp: FastMCP):

    @mcp.tool()
    async def validate_vat_number(
        country_code: str, vat_number: str,
    ) -> dict:
        """EU-Umsatzsteuer-ID (USt-ID / VAT) überprüfen.

        Prüft ob eine USt-ID gültig ist und gibt (falls verfügbar)
        Firmenname und Adresse zurück. Quelle: EU VIES System.

        Hinweis: Deutschland gibt nie Name/Adresse zurück.
        Die meisten anderen EU-Länder liefern Details.

        Args:
            country_code: 2-Buchstaben Ländercode (z.B. "DE", "FR", "IT", "NL")
            vat_number: USt-ID Nummer ohne Länderprefix (z.B. "811128135")
        """
        data = await _vies.validate_vat(country_code, vat_number)

        return {
            "gueltig": data.get("isValid", False),
            "ust_id": f"{country_code.upper()}{vat_number}",
            "land": country_code.upper(),
            "firmenname": data.get("name", "---"),
            "adresse": data.get("address", "---"),
            "pruefzeitpunkt": data.get("requestDate", ""),
            "hinweis": "Deutschland gibt nie Name/Adresse zurück"
            if country_code.upper() == "DE" else "",
        }

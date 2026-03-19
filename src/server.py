"""EU Company MCP Server — Firmendaten, USt-ID Prüfung, EU-Wirtschaftsstatistiken.

3 kostenlose APIs:
- GLEIF (Firmensuche, LEI, Konzernstrukturen — 2M+ Unternehmen weltweit)
- VIES (EU USt-ID Validierung)
- Eurostat (BIP, Arbeitsmarkt, Inflation, Unternehmensdemografie)
"""

from mcp.server.fastmcp import FastMCP

from src.tools.company import register_company_tools
from src.tools.vat import register_vat_tools
from src.tools.statistics import register_statistics_tools

mcp = FastMCP(
    "EU Company MCP Server",
    instructions=(
        "Provides AI agents with EU company and business data: "
        "company search (GLEIF/LEI), corporate structures, "
        "VAT validation (VIES), and EU economic statistics (Eurostat)."
    ),
)

register_company_tools(mcp)
register_vat_tools(mcp)
register_statistics_tools(mcp)

def main():
    """Server starten."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

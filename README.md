# EU Company MCP Server

MCP server providing AI agents with European company data — company search, corporate structures, VAT validation, and EU economic statistics.

## 9 Tools in 3 Categories

### Company Data (GLEIF)
- `company_search` — Search 2M+ companies worldwide by name, filter by country
- `company_by_lei` — Look up company details by LEI code
- `company_by_register` — Find company by trade register number (e.g. HRB)
- `company_structure` — Get corporate structure: parent company + subsidiaries

### VAT Validation (VIES)
- `validate_vat_number` — Validate EU VAT numbers, get company name & address

### EU Statistics (Eurostat)
- `eu_gdp` — GDP for EU countries (in million EUR)
- `eu_unemployment` — Monthly unemployment rates (seasonally adjusted)
- `eu_inflation` — Monthly inflation rates (HICP)
- `eu_business_demography` — Business births, deaths, and active enterprises

## Installation

```bash
pip install eu-company-mcp-server
```

## Usage with Claude Code

`.mcp.json`:

```json
{
  "mcpServers": {
    "eu-company": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "src.server"]
    }
  }
}
```

## Data Sources

All APIs are **free and require no API key**:

| API | Data |
|-----|------|
| GLEIF | Company search, LEI codes, corporate structures (2M+ entities) |
| VIES | EU VAT number validation with company details |
| Eurostat | GDP, unemployment, inflation, business demography |

## Use Cases

- **Due Diligence** — Verify company identity, check corporate structure
- **KYC (Know Your Customer)** — Validate company registration and VAT
- **Market Research** — Compare EU economies, track business trends
- **Compliance** — Verify VAT numbers for cross-border transactions

## License

MIT

# Lead Scraper Template (Audience Edition)

This is a beginner-friendly Python lead scraper template for finding local business leads by keyword and zip code.

It can extract:
- Contact Name (full name, when available)
- Phone
- Email (primary)
- All Emails (backup)
- Website
- Address 1
- Company Name

It supports:
- Single search mode
- Batch mode (`keyword|zip`)
- Loading batch input from `.txt` or `.csv`
- **Optional AI** (OpenAI): per-lead enrichment + personalized outreach columns (GUI, CLI, MCP)

## 1) Requirements

- Python 3.9+ for scraping GUI/CLI (Python **3.10+** recommended if you use MCP)
- Google Cloud API key with:
  - Geocoding API enabled
  - Places API enabled
- **Optional AI:** OpenAI API key for enrichment/outreach (`OPENAI_API_KEY` or enter in GUI / CLI / MCP tool args)

Install dependency:

```bash
pip install -r requirements.txt
```

### AI environment variables (optional)

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Required when AI enrichment or outreach is enabled |
| `LEAD_SCRAPER_AI_MODEL` | Default chat model (default: `gpt-4o-mini`) |
| `OPENAI_API_BASE` | Override API base (default: `https://api.openai.com/v1`) |

**Cost note:** AI runs **once per lead row** when enabled (plus caching within a single run for duplicate websites). Large radii / many Places results increase OpenAI spend.

## 2) Run

From this folder:

```bash
python business_scraper_ui.py
```

### Headless CLI (automation / MCP / scripts)

Uses the same logic as the GUI. Set `GOOGLE_MAPS_API_KEY` or pass `--api-key`.

Single search:

```bash
python scrape_cli.py single --keyword realtor --zip 08830 --radius-miles 5
```

With OpenAI enrichment + outreach (requires `OPENAI_API_KEY` or `--openai-api-key`):

```bash
python scrape_cli.py single --keyword realtor --zip 08830 --radius-miles 5 ^
  --ai-enrich --ai-outreach --tone Friendly --service-offer "We build local SEO sites for SMBs"
```

Batch from file (`.txt` with `keyword|zip` lines or `.csv` with `keyword,zip`):

```bash
python scrape_cli.py batch --batch-file batch_input_template.txt --radius-miles 5 -o my_batch.csv
```

Stdin batch (`-`):

```bash
type batch_input_template.txt | python scrape_cli.py batch --batch-file - --radius-miles 5
```

## 2b) Claude Desktop (MCP)

The MCP server uses **stdio** (default for Claude Desktop). Install deps including `mcp`, then add a local MCP server in Claude Desktop settings.

Example `claude_desktop_config.json` fragment (adjust paths to your machine):

```json
{
  "mcpServers": {
    "lead-scraper": {
      "command": "C:\\\\Users\\\\YOUR_USER\\\\AppData\\\\Local\\\\Programs\\\\Python\\\\Python312\\\\python.exe",
      "args": ["D:\\\\AI Agency\\\\Lead Scaper\\\\mcp_server.py"],
      "env": {
        "GOOGLE_MAPS_API_KEY": "YOUR_KEY_HERE"
      }
    }
  }
}
```

**Tools exposed:**

- `run_lead_scrape` — keyword, zip, radius miles; returns `csv_path` and `row_count`. Optional: `enable_ai_enrichment`, `enable_ai_outreach`, `openai_api_key`, `outreach_tone`, `service_offer`.
- `run_lead_scrape_batch` — `batch_text` (newline `keyword|zip`) or `batch_file` path; same optional AI flags.
- `preview_leads_csv` — first rows of a CSV for quick review.

You can put `OPENAI_API_KEY` in the MCP `env` block alongside `GOOGLE_MAPS_API_KEY` so you do not pass the key in every tool call.

**Note:** The official `mcp` package targets **Python 3.10+**. Use Python 3.10 or newer for the MCP server; the GUI/CLI scraping still works on 3.9 if you omit `mcp`.

## 3) Batch Input Formats

### TXT example (`batch_input_template.txt`)

```txt
realtor|10001
barber shop|30303
dentist|60610
```

### CSV example (`batch_input_template.csv`)

```csv
keyword,zip
realtor,10001
barber shop,30303
dentist,60610
```

## 4) CSV Output Fields

**Core (always present)**

- Search Keyword
- Search Zip Code
- Company Name
- Contact Name (regex/heuristic from website when available)
- Phone
- Address 1
- Website
- Email
- All Emails
- Rating
- Google Reviews
- Price Level
- Types

**AI columns** (filled when AI is enabled + valid OpenAI key; otherwise `N/A`)

- AI Best Contact Full Name
- AI Contact Role
- AI Business Category
- AI Lead Quality Score (0–100)
- AI Contact Confidence (`low` / `medium` / `high`)
- AI Reasoning Summary
- Personalized Subject
- Personalized Email Body
- Personalized SMS

For **Go High Level**, you can map `AI Best Contact Full Name` to **Full Name** when you trust AI over regex `Contact Name`, or keep `Contact Name` as primary and store AI fields as custom properties.

## 5) Go High Level Mapping (Recommended)

- Contact Name -> Full Name
- Email -> Email
- Phone -> Phone
- Company Name -> Company Name
- Website -> Website
- Address 1 -> Address

Optional custom fields:
- Search Keyword
- Search Zip Code
- All Emails
- Rating
- Google Reviews
- Price Level
- Types
- All **AI** columns above (recommended as custom fields)

## 6) Notes for Your Audience

- Some businesses do not publish emails or contact names.
- Respect Google API quota and billing settings.
- Follow local laws and platform terms before outreach.
- AI output is **assistive**: review before sending; do not rely on it for regulated claims.

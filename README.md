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

## 1) Requirements

- Python 3.9+
- Google Cloud API key with:
  - Geocoding API enabled
  - Places API enabled

Install dependency:

```bash
pip install -r requirements.txt
```

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

- `run_lead_scrape` — keyword, zip, radius miles; returns `csv_path` and `row_count`.
- `run_lead_scrape_batch` — `batch_text` (newline `keyword|zip`) or `batch_file` path.
- `preview_leads_csv` — first rows of a CSV for quick review.

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

- Search Keyword
- Search Zip Code
- Company Name
- Contact Name
- Phone
- Address 1
- Website
- Email
- All Emails
- Rating
- Google Reviews
- Price Level
- Types

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

## 6) Notes for Your Audience

- Some businesses do not publish emails or contact names.
- Respect Google API quota and billing settings.
- Follow local laws and platform terms before outreach.

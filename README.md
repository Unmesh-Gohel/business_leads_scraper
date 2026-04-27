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

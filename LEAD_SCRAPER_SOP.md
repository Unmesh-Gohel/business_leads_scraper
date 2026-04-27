# Lead Scraper SOP (Windows + Mac)

This guide shows how to run the included Python lead scraper to collect business contact data (name, phone, website, and discovered emails) for professional services like:

- realtors
- landscapers
- salons
- barber shops
- construction companies
- dental offices
- primary care physicians

## 1) Install Python

### Windows
1. Download Python from [python.org](https://www.python.org/downloads/).
2. Run installer and check **Add Python to PATH**.
3. Click **Install Now**.
4. Verify in Command Prompt:
   - `python --version`

### Mac
1. Download Python from [python.org](https://www.python.org/downloads/).
2. Install package.
3. Verify in Terminal:
   - `python3 --version`

## 2) Install Required Library

Open Terminal/Command Prompt and run:

- Windows: `pip install requests`
- Mac: `pip3 install requests`

## 3) Create Google API Key

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project.
3. Enable:
   - **Geocoding API**
   - **Places API**
4. Go to **APIs & Services > Credentials**.
5. Create and copy an API key.

## 4) Run the Script

The script is already in this project:

- `business_scraper_ui.py`

Navigate to this folder first.

### Windows (Command Prompt)
- `cd "D:\AI Agency\Lead Scaper"`
- `python business_scraper_ui.py`

### Mac/Linux (if copied to a Mac)
- `cd /path/to/Lead\ Scaper`
- `python3 business_scraper_ui.py`

## 5) Use the GUI

Fill these fields:

- **API Key**: your Google API key.
- **Business Type (Keyword)**: one profession at a time (examples below).
- **Zip Code**: search center zip.
- **Search Radius (meters)**: e.g. `5000`.
- **Custom File Name (optional)**: output file prefix.

Click **Run Query**.

### Recommended profession keywords

Use specific phrases for cleaner results:

- `realtor`
- `landscaping company`
- `hair salon`
- `barber shop`
- `construction company`
- `dentist`
- `primary care physician`
- `chiropractor`
- `plumber`
- `electrician`

## 6) Output

A timestamped CSV is created in the same folder with columns:

- Name
- Phone
- Address
- Website
- Emails
- Rating
- Google Reviews
- Price Level
- Types

## How It Works (High Level)

1. Converts zip code to latitude/longitude using Geocoding API.
2. Queries Places Nearby Search using your keyword + radius.
3. Follows pagination (up to ~60 results).
4. Calls Place Details API for each business.
5. Visits the business website and regex-extracts emails from page HTML.
6. Saves everything to CSV and shows success popup.

## Notes

- API billing/quota applies in Google Cloud.
- Some businesses have no website or visible email.
- Respect local laws, platform terms, and anti-spam rules when using contact data.

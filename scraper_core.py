"""
Shared lead scraping logic used by the Tkinter GUI, CLI, and MCP server.
"""

from __future__ import annotations

import csv
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Sequence
from urllib.parse import urljoin, urlparse

import requests

METERS_PER_MILE = 1609.34


def miles_to_meters(radius_miles: float) -> int:
    return int(radius_miles * METERS_PER_MILE)


def extract_phones_from_text(text):
    phone_pattern = r"(?:\+?1[\s.\-]?)?(?:\(?\d{3}\)?[\s.\-]?)\d{3}[\s.\-]?\d{4}"
    phones = set(re.findall(phone_pattern, text))
    return sorted(p.strip() for p in phones if p.strip())


def extract_contact_names_from_text(text):
    patterns = [
        r"(?:Owner|Broker|Agent|Manager|Founder|Dentist|Doctor|Dr\.?|Physician)\s*[:\-]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
        r"(?:Contact|Reach)\s*[:\-]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
    ]
    names = set()
    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        for m in matches:
            name = re.sub(r"\s+", " ", m).strip()
            if len(name) > 2:
                names.add(name.title())
    return sorted(names)


def fetch_website_content(url):
    response = requests.get(url, timeout=12)
    if response.status_code != 200:
        return ""
    return response.text


def extract_candidate_contact_pages(base_url, html):
    links = re.findall(r'href=["\'](.*?)["\']', html, flags=re.IGNORECASE)
    contact_keywords = ("contact", "about", "team", "staff")
    base_domain = urlparse(base_url).netloc.lower()
    pages = []
    for link in links:
        if not any(k in link.lower() for k in contact_keywords):
            continue
        abs_url = urljoin(base_url, link)
        parsed = urlparse(abs_url)
        if parsed.scheme not in ("http", "https"):
            continue
        if parsed.netloc.lower() != base_domain:
            continue
        if abs_url not in pages:
            pages.append(abs_url)
        if len(pages) >= 3:
            break
    return pages


def extract_contact_data_from_website(website_url):
    try:
        main_html = fetch_website_content(website_url)
    except Exception as exc:
        print(f"Error fetching {website_url}: {exc}")
        return [], [], []

    combined_html = [main_html]
    for page_url in extract_candidate_contact_pages(website_url, main_html):
        try:
            combined_html.append(fetch_website_content(page_url))
        except Exception as exc:
            print(f"Error fetching contact page {page_url}: {exc}")

    joined_html = "\n".join(combined_html)
    emails = set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", joined_html))
    phones = set(extract_phones_from_text(joined_html))
    names = set(extract_contact_names_from_text(joined_html))
    return sorted(names), sorted(phones), sorted(emails)


def get_location_from_zip(api_key, zip_code):
    geocode_url = (
        f"https://maps.googleapis.com/maps/api/geocode/json"
        f"?address={zip_code}&key={api_key}"
    )
    geocode_response = requests.get(geocode_url, timeout=20)
    geocode_data = geocode_response.json()

    if geocode_data.get("status") != "OK":
        return None

    location_data = geocode_data["results"][0]["geometry"]["location"]
    latitude = location_data["lat"]
    longitude = location_data["lng"]
    return f"{latitude},{longitude}"


def fetch_places_results(api_key, business_type, location, radius):
    places_url = (
        f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        f"?location={location}&radius={radius}&keyword={business_type}&key={api_key}"
    )

    all_results = []
    response = requests.get(places_url, timeout=20)
    data = response.json()
    all_results.extend(data.get("results", []))

    next_page_token = data.get("next_page_token")
    while next_page_token:
        time.sleep(2)
        paged_url = (
            f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            f"?pagetoken={next_page_token}&key={api_key}"
        )
        paged_response = requests.get(paged_url, timeout=20)
        paged_data = paged_response.json()
        all_results.extend(paged_data.get("results", []))
        next_page_token = paged_data.get("next_page_token")
    return all_results


def build_rows_for_results(api_key, all_results, business_type, zip_code):
    rows = []
    for result in all_results:
        business_name = result.get("name", "N/A")
        address = result.get("vicinity", "N/A")
        place_id = result.get("place_id", "")

        details_url = (
            f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}"
            f"&fields=name,international_phone_number,formatted_address,website,"
            f"rating,user_ratings_total,price_level,types&key={api_key}"
        )
        details_response = requests.get(details_url, timeout=20)
        details_data = details_response.json()
        details_result = details_data.get("result", {})

        google_phone = details_result.get("international_phone_number", "N/A")
        website = details_result.get("website", "N/A")
        rating = details_result.get("rating", "N/A")
        google_reviews = details_result.get("user_ratings_total", "N/A")
        price_level = details_result.get("price_level", "N/A")
        types = ", ".join(details_result.get("types", []))

        contact_names = []
        phones_found = []
        emails_found = []
        if website != "N/A":
            contact_names, phones_found, emails_found = extract_contact_data_from_website(website)
        contact_names_str = ", ".join(contact_names) if contact_names else "N/A"
        phones_str = ", ".join(phones_found) if phones_found else "N/A"
        if phones_str == "N/A" and google_phone != "N/A":
            phones_str = google_phone
        emails_str = ", ".join(emails_found) if emails_found else "N/A"

        rows.append(
            {
                "Search Keyword": business_type,
                "Search Zip Code": zip_code,
                "Company Name": business_name,
                "Contact Name": contact_names_str,
                "Phone": phones_str,
                "Address 1": address,
                "Website": website,
                "Email": emails_found[0] if emails_found else "N/A",
                "All Emails": emails_str,
                "Rating": rating,
                "Google Reviews": google_reviews,
                "Price Level": price_level,
                "Types": types,
            }
        )
    return rows


def scrape_keyword_zip(api_key, business_type, zip_code, radius):
    location = get_location_from_zip(api_key, zip_code)
    if not location:
        raise ValueError(f"Geocoding failed for zip code: {zip_code}")
    all_results = fetch_places_results(api_key, business_type, location, radius)
    return build_rows_for_results(api_key, all_results, business_type, zip_code)


def write_rows_to_csv(csv_filename, rows):
    fieldnames = [
        "Search Keyword",
        "Search Zip Code",
        "Company Name",
        "Contact Name",
        "Phone",
        "Address 1",
        "Website",
        "Email",
        "All Emails",
        "Rating",
        "Google Reviews",
        "Price Level",
        "Types",
    ]
    path = Path(csv_filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_batch_lines(raw_text):
    batch_pairs = []
    for line in raw_text.splitlines():
        cleaned = line.strip()
        if not cleaned or cleaned.startswith("#"):
            continue
        if "|" not in cleaned:
            raise ValueError(
                "Each batch line must be in this format: keyword|zip (example: realtor|10001)."
            )
        keyword, zip_code = cleaned.split("|", 1)
        keyword = keyword.strip()
        zip_code = zip_code.strip()
        if not keyword or not zip_code:
            raise ValueError("Batch lines must include both keyword and zip code.")
        batch_pairs.append((keyword, zip_code))
    return batch_pairs


def parse_batch_file(file_path):
    lowered = str(file_path).lower()

    if lowered.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as txt_file:
            content = txt_file.read()
        return parse_batch_lines(content)

    if lowered.endswith(".csv"):
        pairs = []
        with open(file_path, "r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            if not reader.fieldnames:
                raise ValueError("CSV file is empty or missing headers.")

            normalized_headers = {h.strip().lower(): h for h in reader.fieldnames if h}

            keyword_header = None
            zip_header = None
            for candidate in ["keyword", "business_type", "business type", "profession", "type"]:
                if candidate in normalized_headers:
                    keyword_header = normalized_headers[candidate]
                    break
            for candidate in ["zip", "zip_code", "zipcode", "postal_code", "postal code"]:
                if candidate in normalized_headers:
                    zip_header = normalized_headers[candidate]
                    break

            if not keyword_header or not zip_header:
                raise ValueError(
                    "CSV must include keyword and zip headers (example: keyword,zip)."
                )

            for row in reader:
                keyword = (row.get(keyword_header) or "").strip()
                zip_code = (row.get(zip_header) or "").strip()
                if not keyword and not zip_code:
                    continue
                if not keyword or not zip_code:
                    raise ValueError("Each CSV row must include both keyword and zip.")
                pairs.append((keyword, zip_code))
        return pairs

    raise ValueError("Unsupported file type. Please use .txt or .csv.")


def default_single_output_path(keyword, zip_code, custom_base=""):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_kw = re.sub(r'[\\/:*?"<>|]', "_", keyword) or "leads"
    if custom_base:
        safe_base = re.sub(r'[\\/:*?"<>|]', "_", custom_base)
        return f"{safe_base}_{timestamp}.csv"
    return f"{safe_kw}_{zip_code}_{timestamp}.csv"


def default_batch_output_path(custom_base=""):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if custom_base:
        safe_base = re.sub(r'[\\/:*?"<>|]', "_", custom_base)
        return f"{safe_base}_{timestamp}.csv"
    return f"batch_leads_{timestamp}.csv"


def run_single_scrape(
    api_key,
    keyword,
    zip_code,
    radius_miles,
    output_path=None,
    custom_filename="",
):
    """Run one keyword+zip scrape and write CSV. Returns (absolute_path_str, row_count)."""
    radius_meters = miles_to_meters(radius_miles)
    rows = scrape_keyword_zip(api_key, keyword, zip_code, radius_meters)
    out = output_path or default_single_output_path(keyword, zip_code, custom_filename)
    out = str(Path(out).resolve())
    write_rows_to_csv(out, rows)
    return out, len(rows)


def run_batch_scrape(
    api_key,
    batch_pairs: Sequence[tuple[str, str]],
    radius_miles,
    output_path=None,
    custom_filename="",
):
    """
    Run multiple keyword|zip pairs. Returns (absolute_path_str, row_count, errors).
    errors is a list of strings for failed pairs.
    """
    radius_meters = miles_to_meters(radius_miles)
    all_rows = []
    errors = []
    for keyword, zip_code in batch_pairs:
        try:
            rows = scrape_keyword_zip(api_key, keyword, zip_code, radius_meters)
            all_rows.extend(rows)
        except Exception as exc:
            errors.append(f"{keyword}|{zip_code}: {exc}")

    if not all_rows and errors:
        raise RuntimeError("No rows collected.\n" + "\n".join(errors[:20]))

    out = output_path or default_batch_output_path(custom_filename)
    out = str(Path(out).resolve())
    write_rows_to_csv(out, all_rows)
    return out, len(all_rows), errors


def read_csv_preview(csv_path, max_rows=15, max_chars=12000):
    """Return first max_rows data rows as list of dicts (for MCP / Claude)."""
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    rows_out = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= max_rows:
                break
            rows_out.append(dict(row))

    text = str(rows_out)
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars] + "..."

    return {
        "path": str(path.resolve()),
        "preview_rows": rows_out,
        "preview_text": text,
        "truncated": truncated,
    }

"""
MCP server (stdio) for Claude Desktop: exposes tools to run the lead scraper.

Register in Claude Desktop developer settings with:
  command: full path to python.exe
  args: full path to this file
  env: GOOGLE_MAPS_API_KEY=...

Requires: pip install mcp  (Python 3.10+ recommended for MCP SDK)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

# Ensure project root is on path when launched from arbitrary cwd
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mcp.server.fastmcp import FastMCP

from ai_config import AIOptions
from scraper_core import (
    parse_batch_file,
    parse_batch_lines,
    read_csv_preview,
    run_batch_scrape,
    run_single_scrape,
)

mcp = FastMCP("Lead Scraper", json_response=True)


def _api_key(explicit: Optional[str]) -> str:
    key = (explicit or "").strip() or os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "Missing Google API key. Pass api_key to the tool or set GOOGLE_MAPS_API_KEY in the MCP server env."
        )
    return key


def _ai_options(
    enable_enrichment: bool,
    enable_outreach: bool,
    openai_key: Optional[str],
    tone: str,
    service_offer: str,
) -> Optional[AIOptions]:
    if not enable_enrichment and not enable_outreach:
        return None
    return AIOptions.from_env_overrides(
        enable_enrichment=bool(enable_enrichment),
        enable_outreach=bool(enable_outreach),
        openai_api_key=(openai_key or "").strip(),
        model="",
        tone=tone or "Professional",
        service_offer=service_offer or "",
    )


@mcp.tool()
def run_lead_scrape(
    keyword: str,
    zip_code: str,
    radius_miles: float = 5.0,
    api_key: Optional[str] = None,
    custom_filename: str = "",
    output_path: Optional[str] = None,
    enable_ai_enrichment: bool = False,
    enable_ai_outreach: bool = False,
    openai_api_key: Optional[str] = None,
    outreach_tone: str = "Professional",
    service_offer: str = "",
) -> dict:
    """
    Scrape local businesses for one keyword and zip (radius in miles). Writes a CSV and returns path and row count.
    """
    key = _api_key(api_key)
    ai_opt = _ai_options(
        enable_ai_enrichment,
        enable_ai_outreach,
        openai_api_key,
        outreach_tone,
        service_offer,
    )
    path, count = run_single_scrape(
        key,
        keyword.strip(),
        zip_code.strip(),
        float(radius_miles),
        output_path=output_path.strip() if output_path else None,
        custom_filename=custom_filename.strip(),
        ai_options=ai_opt,
    )
    return {"csv_path": path, "row_count": count, "status": "ok"}


@mcp.tool()
def run_lead_scrape_batch(
    radius_miles: float,
    batch_text: str = "",
    batch_file: str = "",
    api_key: Optional[str] = None,
    custom_filename: str = "",
    output_path: Optional[str] = None,
    enable_ai_enrichment: bool = False,
    enable_ai_outreach: bool = False,
    openai_api_key: Optional[str] = None,
    outreach_tone: str = "Professional",
    service_offer: str = "",
) -> dict:
    """
    Batch scrape: provide either batch_text (newline-separated keyword|zip) or batch_file path (.txt or .csv).
    """
    key = _api_key(api_key)
    batch_text = (batch_text or "").strip()
    batch_file = (batch_file or "").strip()
    if batch_file:
        pairs = parse_batch_file(batch_file)
    elif batch_text:
        pairs = parse_batch_lines(batch_text)
    else:
        raise ValueError("Provide either batch_text or batch_file.")

    ai_opt = _ai_options(
        enable_ai_enrichment,
        enable_ai_outreach,
        openai_api_key,
        outreach_tone,
        service_offer,
    )
    path, count, errors = run_batch_scrape(
        key,
        pairs,
        float(radius_miles),
        output_path=output_path.strip() if output_path else None,
        custom_filename=custom_filename.strip(),
        ai_options=ai_opt,
    )
    return {
        "csv_path": path,
        "row_count": count,
        "errors": errors,
        "error_count": len(errors),
        "status": "ok" if not errors else "completed_with_errors",
    }


@mcp.tool()
def preview_leads_csv(csv_path: str, max_rows: int = 15) -> dict:
    """Read the first rows of a leads CSV for quick review in chat."""
    return read_csv_preview(csv_path.strip(), max_rows=int(max_rows))


if __name__ == "__main__":
    mcp.run(transport="stdio")

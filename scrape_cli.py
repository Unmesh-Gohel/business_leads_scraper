"""
Headless CLI for lead scraping (used from terminal, scripts, or MCP).

API key: pass --api-key or set environment variable GOOGLE_MAPS_API_KEY.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional

from scraper_core import (
    parse_batch_file,
    parse_batch_lines,
    run_batch_scrape,
    run_single_scrape,
)


def _resolve_api_key(explicit: Optional[str]) -> str:
    key = (explicit or "").strip() or os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    if not key:
        print(
            "Error: missing API key. Use --api-key or set GOOGLE_MAPS_API_KEY.",
            file=sys.stderr,
        )
        sys.exit(2)
    return key


def cmd_single(args: argparse.Namespace) -> None:
    api_key = _resolve_api_key(args.api_key)
    path, count = run_single_scrape(
        api_key,
        args.keyword,
        args.zip,
        args.radius_miles,
        output_path=args.output,
        custom_filename=args.custom_name or "",
    )
    print(f"Wrote {count} rows to {path}")


def cmd_batch(args: argparse.Namespace) -> None:
    api_key = _resolve_api_key(args.api_key)
    if args.batch_file:
        if args.batch_file == "-":
            raw = sys.stdin.read()
            pairs = parse_batch_lines(raw)
        else:
            pairs = parse_batch_file(args.batch_file)
    elif args.batch_text:
        pairs = parse_batch_lines(args.batch_text)
    else:
        print("Error: provide --batch-file or --batch-text.", file=sys.stderr)
        sys.exit(2)

    path, count, errors = run_batch_scrape(
        api_key,
        pairs,
        args.radius_miles,
        output_path=args.output,
        custom_filename=args.custom_name or "",
    )
    print(f"Wrote {count} rows to {path}")
    if errors:
        print(f"Warnings: {len(errors)} item(s) failed.", file=sys.stderr)
        for e in errors[:20]:
            print(f"  {e}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Lead scraper CLI (Google Places + website extract).")
    parser.add_argument(
        "--api-key",
        default=None,
        help="Google Maps API key (or set GOOGLE_MAPS_API_KEY).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_single = sub.add_parser("single", help="One keyword + zip search.")
    p_single.add_argument("--keyword", required=True, help="Business type / search keyword.")
    p_single.add_argument("--zip", required=True, help="Zip or postal code center.")
    p_single.add_argument(
        "--radius-miles",
        type=float,
        default=5.0,
        help="Search radius in miles (default 5).",
    )
    p_single.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output CSV path (default: auto name in current directory).",
    )
    p_single.add_argument(
        "--custom-name",
        default="",
        help="Optional base name for default output filename.",
    )
    p_single.set_defaults(func=cmd_single)

    p_batch = sub.add_parser("batch", help="Multiple keyword|zip pairs.")
    src = p_batch.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--batch-file",
        default=None,
        help="Path to .txt (keyword|zip lines) or .csv (keyword,zip). Use - for stdin.",
    )
    src.add_argument(
        "--batch-text",
        default=None,
        help="Inline batch text (newline-separated keyword|zip).",
    )
    p_batch.add_argument(
        "--radius-miles",
        type=float,
        default=5.0,
        help="Search radius in miles (default 5).",
    )
    p_batch.add_argument("-o", "--output", default=None, help="Output CSV path.")
    p_batch.add_argument("--custom-name", default="", help="Optional base name for output file.")
    p_batch.set_defaults(func=cmd_batch)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

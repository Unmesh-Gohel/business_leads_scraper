"""
OpenAI Chat Completions (JSON) for lead enrichment and outreach copy.
Falls back to N/A fields when disabled, missing key, or on error.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any, Optional

import requests

from ai_config import AIOptions

_TEMPLATE_DIR = Path(__file__).resolve().parent / "prompt_templates"

# In-process cache: key -> enrichment dict (avoids duplicate calls for same site in one run)
_enrichment_cache: dict[str, dict[str, Any]] = {}
_outreach_cache: dict[str, dict[str, str]] = {}


def clear_ai_caches() -> None:
    _enrichment_cache.clear()
    _outreach_cache.clear()


def _load(name: str) -> str:
    path = _TEMPLATE_DIR / name
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def html_to_plain_text(html: str, max_chars: int = 12000) -> str:
    if not html:
        return ""
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def _cache_key(prefix: str, website: str, snippet: str, tone: str) -> str:
    h = hashlib.sha256(
        f"{website}|{snippet[:2000]}|{tone}".encode("utf-8", errors="ignore")
    ).hexdigest()[:40]
    return f"{prefix}:{website}:{h}"


def _call_openai_json(
    api_key: str,
    api_base: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    timeout: int = 90,
) -> dict[str, Any]:
    url = f"{api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "temperature": 0.35,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    resp = requests.post(url, headers=headers, json=body, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    if not content:
        return {}
    return json.loads(content)


def _validate_enrichment(raw: dict[str, Any]) -> dict[str, Any]:
    score = raw.get("leadQualityScore", 0)
    try:
        score = int(score)
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(100, score))
    conf = str(raw.get("contactConfidence", "low")).lower()
    if conf not in ("low", "medium", "high"):
        conf = "low"

    def _s(key: str, max_len: int = 200) -> str:
        v = raw.get(key)
        if v is None:
            return "N/A"
        s = str(v).strip()
        if not s:
            return "N/A"
        return s[:max_len]

    summary = _s("reasoningSummary", 400)
    return {
        "bestContactFullName": _s("bestContactFullName", 200),
        "bestContactRole": _s("bestContactRole", 120),
        "businessCategory": _s("businessCategory", 120),
        "leadQualityScore": score,
        "contactConfidence": conf,
        "reasoningSummary": summary if summary != "N/A" else "N/A",
    }


def _validate_outreach(raw: dict[str, Any]) -> dict[str, str]:
    def clip(s: str, n: int) -> str:
        s = (s or "").strip()
        return s[:n] if s else "N/A"

    return {
        "personalizedSubject": clip(str(raw.get("personalizedSubject", "")), 200),
        "personalizedEmailBody": clip(str(raw.get("personalizedEmailBody", "")), 8000),
        "personalizedSms": clip(str(raw.get("personalizedSms", "")), 320),
    }


def enrich_lead(
    row: dict[str, Any],
    website_plain_text: str,
    options: AIOptions,
) -> tuple[dict[str, Any], Optional[str]]:
    """
    Returns (enrichment_fields_for_csv, error_or_none).
    CSV keys: AI Best Contact Full Name, AI Contact Role, ...
    """
    defaults = {
        "AI Best Contact Full Name": "N/A",
        "AI Contact Role": "N/A",
        "AI Business Category": "N/A",
        "AI Lead Quality Score": "N/A",
        "AI Contact Confidence": "N/A",
        "AI Reasoning Summary": "N/A",
    }
    if not options.effective_enrichment():
        return defaults, None

    website = str(row.get("Website", "N/A"))
    key = _cache_key("enrich", website, website_plain_text, options.tone)
    if key in _enrichment_cache:
        cached = _enrichment_cache[key]
        return {**defaults, **cached}, None

    system = _load("enrichment_system.txt") or "You output JSON only."
    user = f"""Return JSON with exactly these keys:
- bestContactFullName (string or null)
- bestContactRole (string or null)
- businessCategory (string or null)
- leadQualityScore (integer 0-100)
- contactConfidence (string: low, medium, or high)
- reasoningSummary (string, max 300 chars)

Lead row (from Google Places + basic site scrape):
{json.dumps(row, ensure_ascii=False)[:6000]}

Website plain text (may be empty):
{website_plain_text[:8000]}
"""
    try:
        raw = _call_openai_json(
            options.openai_api_key,
            options.api_base(),
            options.model,
            system,
            user,
        )
        v = _validate_enrichment(raw)
        out = {
            "AI Best Contact Full Name": v["bestContactFullName"],
            "AI Contact Role": v["bestContactRole"],
            "AI Business Category": v["businessCategory"],
            "AI Lead Quality Score": str(v["leadQualityScore"]),
            "AI Contact Confidence": v["contactConfidence"],
            "AI Reasoning Summary": v["reasoningSummary"],
        }
        _enrichment_cache[key] = out
        time.sleep(0.25)
        return out, None
    except Exception as exc:
        err = str(exc)[:500]
        return {**defaults, "AI Reasoning Summary": f"AI error: {err}"}, err


def generate_outreach(
    row: dict[str, Any],
    website_plain_text: str,
    enrichment: dict[str, Any],
    options: AIOptions,
) -> tuple[dict[str, str], Optional[str]]:
    defaults = {
        "Personalized Subject": "N/A",
        "Personalized Email Body": "N/A",
        "Personalized SMS": "N/A",
    }
    if not options.effective_outreach():
        return defaults, None

    website = str(row.get("Website", "N/A"))
    key = _cache_key("outreach", website, website_plain_text + json.dumps(enrichment), options.tone)
    if key in _outreach_cache:
        cached = _outreach_cache[key]
        return {**defaults, **cached}, None

    system = _load("outreach_system.txt") or "You output JSON only."
    user = f"""Tone: {options.tone}

Our service / value prop to weave in lightly (may be empty): {options.service_offer or "N/A"}

Return JSON with keys:
- personalizedSubject (string)
- personalizedEmailBody (string)
- personalizedSms (string, under 300 chars)

Lead data:
{json.dumps(row, ensure_ascii=False)[:4000]}

AI enrichment:
{json.dumps(enrichment, ensure_ascii=False)[:2000]}

Website plain text (may be empty):
{website_plain_text[:6000]}
"""
    try:
        raw = _call_openai_json(
            options.openai_api_key,
            options.api_base(),
            options.model,
            system,
            user,
        )
        v = _validate_outreach(raw)
        out = {
            "Personalized Subject": v["personalizedSubject"],
            "Personalized Email Body": v["personalizedEmailBody"],
            "Personalized SMS": v["personalizedSms"],
        }
        _outreach_cache[key] = out
        time.sleep(0.25)
        return out, None
    except Exception as exc:
        err = str(exc)[:500]
        return {**defaults, "Personalized Email Body": f"AI error: {err}"}, err


def apply_ai_to_row(
    row: dict[str, Any],
    website_plain_text: str,
    options: Optional[AIOptions],
) -> dict[str, Any]:
    """Mutate/extend row with AI columns; never raises."""
    merged = dict(row)
    if not options or not options.wants_any_ai():
        merged.update(_empty_ai_columns())
        return merged

    if not options.has_openai_credentials():
        merged.update(_empty_ai_columns())
        merged["AI Reasoning Summary"] = "N/A (enable AI requires OPENAI_API_KEY or key in app)"
        return merged

    enrichment, _e1 = enrich_lead(row, website_plain_text, options)
    merged.update(enrichment)

    outreach, _e2 = generate_outreach(row, website_plain_text, enrichment, options)
    merged.update(outreach)

    return merged


def _empty_ai_columns() -> dict[str, str]:
    return {
        "AI Best Contact Full Name": "N/A",
        "AI Contact Role": "N/A",
        "AI Business Category": "N/A",
        "AI Lead Quality Score": "N/A",
        "AI Contact Confidence": "N/A",
        "AI Reasoning Summary": "N/A",
        "Personalized Subject": "N/A",
        "Personalized Email Body": "N/A",
        "Personalized SMS": "N/A",
    }


def csv_ai_fieldnames() -> list[str]:
    return [
        "AI Best Contact Full Name",
        "AI Contact Role",
        "AI Business Category",
        "AI Lead Quality Score",
        "AI Contact Confidence",
        "AI Reasoning Summary",
        "Personalized Subject",
        "Personalized Email Body",
        "Personalized SMS",
    ]

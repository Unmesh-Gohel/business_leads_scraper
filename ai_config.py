"""
AI configuration for lead enrichment and outreach (OpenAI-compatible Chat Completions).

Environment variables (optional; GUI/MCP can override):
  OPENAI_API_KEY          Required when AI features are enabled
  LEAD_SCRAPER_AI_MODEL   Default: gpt-4o-mini
  OPENAI_API_BASE         Default: https://api.openai.com/v1
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AIOptions:
    """Runtime options for optional AI post-processing of scraped rows."""

    enable_enrichment: bool = False
    enable_outreach: bool = False
    openai_api_key: str = ""
    model: str = ""
    tone: str = "Professional"  # Professional | Friendly | Direct
    service_offer: str = ""

    @classmethod
    def from_env_overrides(
        cls,
        enable_enrichment: bool = False,
        enable_outreach: bool = False,
        openai_api_key: str = "",
        model: str = "",
        tone: str = "Professional",
        service_offer: str = "",
    ) -> "AIOptions":
        key = (openai_api_key or "").strip() or os.environ.get("OPENAI_API_KEY", "").strip()
        m = (model or "").strip() or os.environ.get("LEAD_SCRAPER_AI_MODEL", "gpt-4o-mini").strip()
        return cls(
            enable_enrichment=enable_enrichment,
            enable_outreach=enable_outreach,
            openai_api_key=key,
            model=m,
            tone=(tone or "Professional").strip(),
            service_offer=(service_offer or "").strip(),
        )

    def api_base(self) -> str:
        return (os.environ.get("OPENAI_API_BASE") or "https://api.openai.com/v1").rstrip("/")

    def has_openai_credentials(self) -> bool:
        return bool(self.openai_api_key)

    def wants_any_ai(self) -> bool:
        return self.enable_enrichment or self.enable_outreach

    def effective_enrichment(self) -> bool:
        return self.enable_enrichment and self.has_openai_credentials()

    def effective_outreach(self) -> bool:
        return self.enable_outreach and self.has_openai_credentials()

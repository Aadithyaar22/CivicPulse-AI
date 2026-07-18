"""Thin, reusable Gemini wrapper.

Supports two backends via env vars (auto-detected):
  * Gemini Developer API  -> set GEMINI_API_KEY (or GOOGLE_API_KEY)
  * Vertex AI              -> set GOOGLE_GENAI_USE_VERTEXAI=true,
                              GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION

Design goals: one call per user action, cheap flash-lite model by default,
graceful retries, and a deterministic offline fallback so the demo never dies.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

from .prompt_templates import (
    SYSTEM_INSTRUCTION,
    build_brief_prompt,
    build_question_prompt,
    build_text_summary_prompt,
)
from .utils import extract_json, humanize

# Smaller / cheaper Gemini tier by default. Override with GEMINI_MODEL.
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
MAX_RETRIES = 2
RETRY_BACKOFF_SEC = 1.5


@dataclass
class GeminiResult:
    ok: bool
    data: dict[str, Any]
    raw_text: str = ""
    used_fallback: bool = False
    model: str = DEFAULT_MODEL
    error: str | None = None


class GeminiClient:
    """Lazy-initialized client. Never raises on construction."""

    def __init__(self, model: str | None = None):
        self.model = model or DEFAULT_MODEL
        self._client = None
        self._init_error: str | None = None
        self._backend = "none"
        self._try_init()

    def _try_init(self) -> None:
        try:
            from google import genai  # imported lazily to keep startup fast
        except ImportError as exc:  # pragma: no cover
            self._init_error = f"google-genai not installed: {exc}"
            return

        use_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in {
            "1",
            "true",
            "yes",
        }
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

        try:
            if use_vertex:
                project = os.environ.get("GOOGLE_CLOUD_PROJECT")
                location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
                if not project:
                    self._init_error = "GOOGLE_CLOUD_PROJECT not set for Vertex AI."
                    return
                self._client = genai.Client(
                    vertexai=True, project=project, location=location
                )
                self._backend = "vertex"
            elif api_key:
                self._client = genai.Client(api_key=api_key)
                self._backend = "gemini_api"
            else:
                self._init_error = (
                    "No credentials found. Set GEMINI_API_KEY, or "
                    "GOOGLE_GENAI_USE_VERTEXAI=true with GOOGLE_CLOUD_PROJECT."
                )
        except Exception as exc:  # pragma: no cover - defensive
            self._init_error = f"Failed to init Gemini client: {exc}"

    @property
    def available(self) -> bool:
        return self._client is not None

    @property
    def backend(self) -> str:
        return self._backend

    @property
    def status_message(self) -> str:
        if self.available:
            return f"Connected via {self._backend} ({self.model})."
        return self._init_error or "Gemini unavailable."

    # ---------- low-level generation ----------

    def _generate(self, prompt: str) -> tuple[bool, str, str | None]:
        """Return (ok, text, error). Retries transient failures."""
        if not self.available:
            return False, "", self._init_error

        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.3,
            max_output_tokens=1024,
            response_mime_type="application/json",
        )

        last_error: str | None = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = self._client.models.generate_content(
                    model=self.model, contents=prompt, config=config
                )
                return True, (resp.text or ""), None
            except Exception as exc:  # noqa: BLE001 - report and retry
                last_error = str(exc)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_SEC * (attempt + 1))
        return False, "", last_error

    def _run(self, prompt: str, fallback_fn) -> GeminiResult:
        ok, text, error = self._generate(prompt)
        if ok:
            parsed = extract_json(text)
            if parsed is not None:
                return GeminiResult(ok=True, data=parsed, raw_text=text, model=self.model)
            # Model replied but not clean JSON -> keep prose, still succeed.
            return GeminiResult(
                ok=True,
                data={"summary": text.strip()},
                raw_text=text,
                model=self.model,
            )
        # Failure -> deterministic fallback so the demo continues.
        return GeminiResult(
            ok=False,
            data=fallback_fn(),
            used_fallback=True,
            model=self.model,
            error=error,
        )

    # ---------- public high-level calls ----------

    def executive_brief(self, insights: dict[str, Any], domain: str) -> GeminiResult:
        prompt = build_brief_prompt(insights, domain)
        return self._run(prompt, lambda: _fallback_brief(insights))

    def answer_question(
        self, insights: dict[str, Any], question: str, domain: str
    ) -> GeminiResult:
        prompt = build_question_prompt(insights, question, domain)
        return self._run(prompt, lambda: _fallback_answer(insights, question))

    def summarize_text(self, raw_text: str, domain: str) -> GeminiResult:
        prompt = build_text_summary_prompt(raw_text, domain)
        return self._run(prompt, lambda: _fallback_text(raw_text))


# ---------- deterministic fallbacks (no API needed) ----------
# These make sure the dashboard is fully usable offline / without a key.


def _top(d: dict[str, int]) -> str | None:
    return next(iter(d), None) if d else None


def _fallback_brief(insights: dict[str, Any]) -> dict[str, Any]:
    total = insights.get("total_records", 0)
    hotspot = insights.get("hotspot_area")
    top_cat = insights.get("top_category")
    trend = insights.get("trend_direction", "flat")
    anomalies = insights.get("anomalies", [])
    open_rate = insights.get("open_rate_pct", 0)

    findings = [f"{total} records analyzed."]
    if hotspot:
        findings.append(f"'{humanize(hotspot)}' is the top hotspot area.")
    if top_cat:
        findings.append(f"'{humanize(top_cat)}' is the leading category.")
    findings.append(f"Overall volume is {trend}.")
    if open_rate:
        findings.append(f"{open_rate}% of cases are still open/unresolved.")

    actions = []
    if hotspot:
        actions.append(
            {
                "action": f"Deploy a rapid-response team to {humanize(hotspot)}.",
                "owner": "Operations",
                "timeframe": "this week",
            }
        )
    if top_cat:
        actions.append(
            {
                "action": f"Prioritize resolution of '{humanize(top_cat)}' cases.",
                "owner": "Relevant department",
                "timeframe": "2 weeks",
            }
        )

    return {
        "title": "Community Situation Brief",
        "summary": (
            f"{total} community records analyzed. Volume is {trend}; "
            f"top hotspot is {humanize(hotspot) if hotspot else 'n/a'} and the leading "
            f"issue is {humanize(top_cat) if top_cat else 'n/a'}."
        ),
        "key_findings": findings,
        "anomalies": [a.get("detail", "") for a in anomalies] or ["No significant anomalies detected."],
        "recommended_actions": actions or [
            {"action": "Continue monitoring; no urgent hotspot.", "owner": "Ops", "timeframe": "ongoing"}
        ],
        "explanation": (
            "Recommendations follow the highest-volume area and category, weighted by "
            "open-case rate and detected anomalies."
        ),
        "confidence": "medium",
        "_note": "Offline fallback (Gemini not called). Numbers are from local analytics.",
    }


def _fallback_answer(insights: dict[str, Any], question: str) -> dict[str, Any]:
    hotspot = insights.get("hotspot_area")
    top_cat = insights.get("top_category")
    trend = insights.get("trend_direction", "flat")
    return {
        "what_is_happening": (
            f"Based on local analytics, '{humanize(top_cat)}' leads and "
            f"'{humanize(hotspot)}' is the busiest area."
            if top_cat and hotspot
            else "Not enough structured data to answer precisely."
        ),
        "why_it_matters": f"Volume trend is {trend}, affecting service planning.",
        "where": humanize(hotspot) if hotspot else "not enough data",
        "recommended_next_step": (
            f"Focus resources on {humanize(hotspot)}." if hotspot else "Collect more data."
        ),
        "confidence": "low",
        "executive_summary": (
            f"{humanize(hotspot)} needs attention for {humanize(top_cat)} issues."
            if hotspot and top_cat
            else "Insufficient data for a firm answer."
        ),
        "_note": "Offline fallback (Gemini not called).",
    }


def _fallback_text(raw_text: str) -> dict[str, Any]:
    snippet = (raw_text or "").strip().replace("\n", " ")
    return {
        "title": "Document Summary (offline)",
        "summary": snippet[:280] + ("..." if len(snippet) > 280 else ""),
        "key_findings": ["Gemini was not called; showing raw excerpt."],
        "recommended_actions": [
            {"action": "Enable Gemini for a full summary.", "owner": "Admin", "timeframe": "now"}
        ],
        "confidence": "low",
        "_note": "Offline fallback (Gemini not called).",
    }

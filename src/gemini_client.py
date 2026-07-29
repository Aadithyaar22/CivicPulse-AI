"""Thin, reusable Gemini wrapper.

Supports two backends via env vars (auto-detected):
  * Gemini Developer API  -> set GEMINI_API_KEY (or GOOGLE_API_KEY)
  * Vertex AI              -> set GOOGLE_GENAI_USE_VERTEXAI=true,
                              GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION

Design goals: one call per user action, the best Gemini tier this project
actually has access to, graceful retries, and a deterministic offline
fallback so the demo never dies.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

from .prompt_templates import (
    agentic_system_instruction,
    build_agentic_followup_prompt,
    build_agentic_question_prompt,
    build_brief_prompt,
    build_question_prompt,
    build_text_summary_prompt,
    system_instruction,
)
from .utils import extract_json, humanize

# gemini-3.x variants all 404 on this project's Vertex AI despite appearing
# in the model catalog listing (an access-tier gate, not a naming issue --
# see git history around commit 44f0067 for the same failure mode on
# gemini-3.1-flash-lite). gemini-2.5-pro is the strongest tier actually
# invokable here. Override with GEMINI_MODEL.
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")
MAX_RETRIES = 2
RETRY_BACKOFF_SEC = 1.5
# Hard cap on tool-call round-trips per agentic question. Bounds latency/cost
# and guarantees we fall back to the static grounded answer instead of ever
# hanging in a loop.
MAX_TOOL_TURNS = 4
# Cap on how many follow-up questions one conversation can carry before the
# caller should start fresh. Bounds token cost/latency growth over a long
# chat session; app.py resets the stored conversation once this is hit.
MAX_CONVERSATION_QUESTIONS = 8


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

    def _generate(self, prompt: str, lang: str = "English") -> tuple[bool, str, str | None]:
        """Return (ok, text, error). Retries transient failures."""
        if not self.available:
            return False, "", self._init_error

        from google.genai import types

        # Kannada/Hindi script costs noticeably more output tokens than
        # English for equivalent content (observed: a Kannada Executive
        # Brief truncated mid-JSON at 3072 and silently fell back to the
        # English offline summary -- the language fix was working, the
        # token budget just wasn't big enough to let it finish). The verbose
        # Executive Brief schema (dataset_overview + full findings +
        # peculiar_patterns + urgency-tagged actions) already needed real
        # headroom in English; give non-English runs more still.
        budget = 3072 if (not lang or lang == "English") else 6144
        config = types.GenerateContentConfig(
            system_instruction=system_instruction(lang),
            temperature=0.3,
            max_output_tokens=budget,
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

    def _run(self, prompt: str, fallback_fn, lang: str = "English") -> GeminiResult:
        last_error: str | None = None
        # One retry if the model returns text that isn't valid JSON -- e.g.
        # a response cut off mid-structure by max_output_tokens. Showing
        # that raw/truncated text to the user is worse than a fresh attempt
        # (same failure mode fixed on the agentic tool-calling path).
        for _attempt in range(2):
            ok, text, error = self._generate(prompt, lang=lang)
            if not ok:
                last_error = error
                break  # _generate() already retried transient errors internally
            parsed = extract_json(text)
            if parsed is not None:
                return GeminiResult(ok=True, data=parsed, raw_text=text, model=self.model)
            last_error = f"Model returned unparseable JSON (possible truncation): {text[:200]!r}"
        # Failure -> deterministic fallback so the demo continues.
        return GeminiResult(
            ok=False,
            data=fallback_fn(),
            used_fallback=True,
            model=self.model,
            error=last_error,
        )

    # ---------- public high-level calls ----------

    def executive_brief(self, insights: dict[str, Any], domain: str, lang: str = "English") -> GeminiResult:
        prompt = build_brief_prompt(insights, domain, lang=lang)
        return self._run(prompt, lambda: _fallback_brief(insights), lang=lang)

    def answer_question(
        self, insights: dict[str, Any], question: str, domain: str, lang: str = "English"
    ) -> GeminiResult:
        prompt = build_question_prompt(insights, question, domain, lang=lang)
        return self._run(prompt, lambda: _fallback_answer(insights, question), lang=lang)

    def answer_question_agentic(
        self,
        df: Any,
        insights: dict[str, Any],
        question: str,
        domain: str,
        conversation: list | None = None,
        lang: str = "English",
    ) -> tuple[GeminiResult, list]:
        """Agentic Q&A: Gemini calls real query tools (see qa_tools.py) against
        the live DataFrame instead of reasoning over one static analytics
        snapshot -- so it can answer comparisons and drill-downs a single
        precomputed payload can't ("compare Koramangala vs Indiranagar this
        month"). Every number still comes from a deterministic pandas query;
        Gemini only chooses which query to run and narrates the real result.

        `conversation` is the prior turn history (as returned by an earlier
        call) to continue, or None/empty to start fresh -- this is what makes
        "what about last month?" work as a real follow-up instead of an
        unrelated one-shot question. Returns (result, updated_conversation);
        the caller should store the second value and pass it back in on the
        next question. Callers should also start a fresh conversation (pass
        None) once MAX_CONVERSATION_QUESTIONS is reached.

        Small/cheap models occasionally produce a malformed function call or
        an empty final turn on multi-step tool loops (observed with
        flash-lite on comparison-style questions) -- a fresh attempt often
        succeeds, so this retries once before falling back to the static
        grounded `answer_question` (which itself falls back to a
        deterministic offline answer). This upgrade never makes the demo
        less reliable than before it existed.
        """
        if not self.available or df is None or getattr(df, "empty", True):
            return self.answer_question(insights, question, domain, lang=lang), (conversation or [])

        last_error: str | None = None
        for _attempt in range(2):
            try:
                result, new_conversation = self._run_agentic_once(df, question, domain, conversation, lang=lang)
            except Exception as exc:  # noqa: BLE001 - the agentic path must never crash the app
                last_error = str(exc)
                result, new_conversation = None, None
            if result is not None:
                return result, new_conversation

        fallback = self.answer_question(insights, question, domain, lang=lang)
        fallback.error = last_error or "Agentic Q&A produced no usable answer after retry; used grounded fallback."
        return fallback, (conversation or [])

    def _run_agentic_once(
        self, df: Any, question: str, domain: str, conversation: list | None, lang: str = "English"
    ) -> tuple[GeminiResult | None, list | None]:
        """One attempt at the tool-calling loop. Returns (None, None) (rather
        than a hollow ok=True with blank content) if the model produced an
        unusable turn -- a malformed function call, an empty response, or
        exhausted MAX_TOOL_TURNS without a final answer -- so the caller can
        retry or fall back instead of showing nothing. On success, returns
        the full updated conversation (including this question's tool calls
        and final answer) so the next follow-up can continue from it."""
        from google.genai import types

        from .qa_tools import TOOL_DECLARATIONS, dispatch_tool

        tool = types.Tool(function_declarations=TOOL_DECLARATIONS)
        config = types.GenerateContentConfig(
            system_instruction=agentic_system_instruction(lang),
            temperature=0.2,
            # The answer schema includes a 2-3 sentence "explanation" paragraph
            # on top of the other fields; 1024 was tight enough to sometimes
            # truncate mid-JSON (observed: a cut-off response with no closing
            # brace, silently rendered as raw text). 2048 gives headroom.
            max_output_tokens=2048,
            tools=[tool],
        )
        is_followup = bool(conversation)
        prompt = (
            build_agentic_followup_prompt(question, lang=lang)
            if is_followup
            else build_agentic_question_prompt(question, domain, lang=lang)
        )
        contents = list(conversation or [])
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))

        trace: list[dict[str, Any]] = []
        for _ in range(MAX_TOOL_TURNS):
            resp = self._client.models.generate_content(
                model=self.model, contents=contents, config=config
            )
            candidate = resp.candidates[0] if resp.candidates else None
            calls = resp.function_calls or []

            if not calls:
                text = (resp.text or "").strip()
                if not text:
                    # e.g. finish_reason MALFORMED_FUNCTION_CALL / SAFETY --
                    # not a tool call and no usable text either.
                    return None, None
                parsed = extract_json(text)
                if parsed is None:
                    # The prompt requires ONLY JSON; unparseable text here
                    # usually means the response got cut off mid-JSON (e.g.
                    # max_output_tokens hit before the closing brace). Showing
                    # that raw truncated string to the user is worse than
                    # retrying, so treat this the same as an unusable turn.
                    return None, None
                parsed["_tool_trace"] = trace
                if candidate is not None:
                    contents.append(candidate.content)
                return GeminiResult(ok=True, data=parsed, raw_text=text, model=self.model), contents

            if candidate is None:
                return None, None
            contents.append(candidate.content)
            response_parts = []
            for fc in calls:
                args = dict(fc.args or {})
                result = dispatch_tool(df, fc.name, args)
                trace_entry: dict[str, Any] = {"tool": fc.name, "args": args}
                # Only set record_count when the tool actually reports one --
                # get_summary_stats has no such concept (it's a whole-dataset
                # snapshot, not a filtered count), and the app's confidence
                # scoring treats "key absent" and "explicitly zero" as
                # meaningfully different signals, not the same as None.
                if "record_count" in result:
                    trace_entry["record_count"] = result.get("record_count")
                if result.get("error"):
                    trace_entry["error"] = result.get("error")
                trace.append(trace_entry)
                response_parts.append(
                    types.Part.from_function_response(name=fc.name, response={"result": result})
                )
            contents.append(types.Content(role="user", parts=response_parts))

        return None, None  # exhausted MAX_TOOL_TURNS without a final answer

    def summarize_text(self, raw_text: str, domain: str, lang: str = "English") -> GeminiResult:
        prompt = build_text_summary_prompt(raw_text, domain, lang=lang)
        return self._run(prompt, lambda: _fallback_text(raw_text), lang=lang)

    def ocr_extract_text(self, image_bytes: bytes, mime_type: str) -> GeminiResult:
        """Transcribe a photo or scanned page (including handwriting) to
        plain text using Gemini's own vision input -- no separate OCR/Vision
        API call needed, since the model already reads images directly.
        There's no offline fallback here (unlike the JSON-producing calls
        above): a wrong guess at handwritten text would be worse than a
        clear "try again" error.
        """
        if not self.available:
            return GeminiResult(ok=False, data={"text": ""}, model=self.model, error=self._init_error)

        from google.genai import types

        prompt = (
            "Transcribe ALL visible text in this image exactly as written, "
            "including handwriting. Preserve line breaks and word order. "
            "Output ONLY the transcribed text -- no commentary, no markdown, "
            "no translation, no summary."
        )
        config = types.GenerateContentConfig(temperature=0.0, max_output_tokens=2048)
        try:
            resp = self._client.models.generate_content(
                model=self.model,
                contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime_type), prompt],
                config=config,
            )
            text = (resp.text or "").strip()
            if not text:
                return GeminiResult(ok=False, data={"text": ""}, model=self.model, error="No text detected in the image.")
            return GeminiResult(ok=True, data={"text": text}, raw_text=text, model=self.model)
        except Exception as exc:  # noqa: BLE001 - report, don't crash the demo
            return GeminiResult(ok=False, data={"text": ""}, model=self.model, error=str(exc))


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
    by_area = insights.get("by_area", {}) or {}
    by_category = insights.get("by_category", {}) or {}
    severity_dist = insights.get("severity_distribution", {}) or {}
    date_range = insights.get("date_range", {}) or {}

    overview_parts = [f"This dataset has {total} community report(s)"]
    if date_range.get("start") and date_range.get("end"):
        overview_parts.append(f"from {date_range['start']} to {date_range['end']}")
    overview_parts.append(
        f"spread across {len(by_area)} area(s) and {len(by_category)} categor{'y' if len(by_category) == 1 else 'ies'}."
    )
    overview = " ".join(overview_parts)
    if hotspot:
        overview += f" '{humanize(hotspot)}' has the most reports."
    if top_cat:
        overview += f" '{humanize(top_cat)}' is the most common issue type."
    overview += f" Overall volume is {trend}, and {open_rate}% of cases are still open/unresolved."
    if severity_dist:
        crit = severity_dist.get("critical", 0)
        high = severity_dist.get("high", 0)
        if crit or high:
            overview += f" {crit + high} report(s) are marked high or critical severity."
    overview += (
        " This is a rule-based summary (Gemini wasn't reachable), so it covers the headline "
        "numbers only -- enable Gemini for a full plain-language walkthrough."
    )

    findings = [f"{total} records analyzed."]
    if hotspot:
        findings.append(f"'{humanize(hotspot)}' is the top hotspot area.")
    if top_cat:
        findings.append(f"'{humanize(top_cat)}' is the leading category.")
    findings.append(f"Overall volume is {trend}.")
    if open_rate:
        findings.append(f"{open_rate}% of cases are still open/unresolved.")
    if severity_dist:
        findings.append(
            "Severity mix: " + ", ".join(f"{k} {v}" for k, v in severity_dist.items())
        )

    peculiar = [a.get("detail", "") for a in anomalies] or [
        "No statistically flagged anomalies in this offline summary -- enable Gemini for a "
        "closer read of less obvious patterns."
    ]

    actions = []
    if hotspot:
        actions.append(
            {
                "action": f"Deploy a rapid-response team to {humanize(hotspot)}.",
                "owner": "Operations",
                "timeframe": "this week",
                "urgency": "high",
            }
        )
    if top_cat:
        actions.append(
            {
                "action": f"Prioritize resolution of '{humanize(top_cat)}' cases.",
                "owner": "Relevant department",
                "timeframe": "2 weeks",
                "urgency": "normal",
            }
        )

    return {
        "title": "Community Situation Brief",
        "dataset_overview": overview,
        "summary": (
            f"{total} community records analyzed. Volume is {trend}; "
            f"top hotspot is {humanize(hotspot) if hotspot else 'n/a'} and the leading "
            f"issue is {humanize(top_cat) if top_cat else 'n/a'}."
        ),
        "key_findings": findings,
        "peculiar_patterns": peculiar,
        "recommended_actions": actions or [
            {"action": "Continue monitoring; no urgent hotspot.", "owner": "Ops", "timeframe": "ongoing", "urgency": "normal"}
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
    total = insights.get("total_records", 0)
    open_rate = insights.get("open_rate_pct", 0)
    return {
        "what_is_happening": (
            f"Based on local analytics, '{humanize(top_cat)}' leads and "
            f"'{humanize(hotspot)}' is the busiest area."
            if top_cat and hotspot
            else "Not enough structured data to answer precisely."
        ),
        "why_it_matters": f"Volume trend is {trend}, affecting service planning.",
        "where": [humanize(hotspot)] if hotspot else [],
        "recommended_next_step": (
            f"Focus resources on {humanize(hotspot)}." if hotspot else "Collect more data."
        ),
        "executive_summary": (
            f"{humanize(hotspot)} needs attention for {humanize(top_cat)} issues."
            if hotspot and top_cat
            else "Insufficient data for a firm answer."
        ),
        "explanation": (
            f"Out of {total} records analyzed, {humanize(hotspot)} has the highest volume "
            f"and {humanize(top_cat)} is the leading issue category, with volume trending "
            f"{trend} and {open_rate}% of cases still open. This is a rule-based summary "
            "(Gemini wasn't reachable for this answer), not a generated narrative."
            if hotspot and top_cat
            else "Gemini wasn't reachable and the uploaded data doesn't have enough "
            "structured area/category information for a rule-based summary either."
        ),
        "suggested_follow_ups": [
            f"What's driving the volume in {humanize(hotspot)}?" if hotspot else "Which area needs attention?",
            f"How urgent are {humanize(top_cat)} cases?" if top_cat else "What's the most common issue type?",
            "What should we prioritize this week?",
        ],
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

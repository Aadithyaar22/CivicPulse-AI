"""Prompt templates that make Gemini behave like a civic decision analyst.

All prompts are grounded strictly in the deterministic analytics dict, so the
model explains and recommends but never invents numbers.
"""

from __future__ import annotations

import json
from typing import Any


def _language_instruction(lang: str) -> str:
    """Gemini already writes fluent Kannada/Hindi, so the UI's language
    toggle is threaded straight into the prompt rather than machine-
    translating English output after the fact -- more natural phrasing,
    and it's a single line, not a second pipeline stage."""
    if not lang or lang == "English":
        return ""
    return (
        f"\n\nRespond entirely in {lang}. Every text field in the JSON output "
        f"must be written in {lang} (not English) -- explanations, findings, "
        f"recommendations, all of it. Area/category names may stay as given "
        f"in the data if there's no natural {lang} equivalent.\n"
    )

def system_instruction(lang: str = "English") -> str:
    """Built as a function (not a constant) for the same reason as
    agentic_system_instruction below: a language directive placed only in
    the per-turn prompt (see _language_instruction above) is unreliable --
    small/cheap models, and it turns out even gemini-2.5-pro on a long
    prompt dominated by an English JSON analytics blob, default back to
    English prose despite an instruction buried at the end of that prompt.
    Putting the rule in the higher-priority system instruction is what
    actually makes the Executive Brief, Ask AI's grounded fallback, and the
    OCR text summary come back in the selected language."""
    lang_rule = (
        f" Respond ENTIRELY in {lang} -- every text field in your JSON output "
        f"(title, summary, findings, explanations, recommendations, all of it) "
        f"must be written in {lang}, not English. Area/category names may stay "
        f"as given in the data if there's no natural {lang} equivalent."
        if lang and lang != "English" else ""
    )
    return (
        "You are CivicPulse AI, a community decision intelligence assistant for city "
        "and neighborhood teams. Use ONLY the provided analytics JSON as evidence. "
        "Never invent numbers, areas, or categories that are not in the data. "
        "Clearly separate facts (from the analytics) from recommendations (your advice). "
        "Be concise, practical, and evidence-based. Write for a busy public official who "
        "has 60 seconds. Explain what matters, why it matters, and what to do next."
        f"{lang_rule}"
    )

# JSON schema for the Executive Brief. Framed as a handoff document for
# someone who must fully understand this dataset before acting on it, not a
# 60-second skim -- see build_brief_prompt for the full instructions.
_REPORT_SHAPE = {
    "title": "string, <= 8 words",
    "dataset_overview": (
        "4-6 sentences in simple, jargon-free language giving a complete walkthrough of "
        "what this dataset contains: the time range covered, total volume, which areas and "
        "categories are involved, how severe/urgent it generally looks, and overall data "
        "quality -- written for someone who has never seen this data before and needs to "
        "fully understand it before making any changes"
    ),
    "summary": "2-3 sentence executive summary",
    "key_findings": [
        "5-8 short bullet strings covering ALL the important patterns in the data, not just "
        "the single biggest one -- volume, trend, severity mix, status/department breakdown, "
        "whatever is notable -- grounded in specific numbers"
    ],
    "peculiar_patterns": [
        "every unusual, surprising, or noteworthy pattern visible in the data, in plain "
        "language -- statistically flagged anomalies AND anything else that looks off or "
        "worth a second look (e.g. one area/category dominating, an odd status or department "
        "imbalance, a sudden shift). Say 'nothing unusual stands out beyond the hotspot above' "
        "if genuinely none."
    ],
    "recommended_actions": [
        {
            "action": (
                "specific, complete next step -- enough detail that someone could start on "
                "it without needing to ask a follow-up question"
            ),
            "owner": "which department/team",
            "timeframe": "e.g. this week / 2 weeks",
            "urgency": "one of: immediate (respond today/ASAP), high (this week), normal (this month)",
        }
    ],
    "explanation": "plain-language reasoning connecting the findings and patterns above to why these specific actions were recommended",
    "confidence": "one of: high, medium, low",
}


_AGENTIC_ANSWER_SHAPE = """{
  "what_is_happening": "1-2 sentences of factual answer grounded in tool results",
  "why_it_matters": "1-2 sentences on impact",
  "where": "array of the relevant area name(s), ranked most-relevant first (e.g. [\"Koramangala\", \"Jayanagar\"]); empty array if not enough data",
  "recommended_next_step": "one concrete action",
  "executive_summary": "one crisp sentence a mayor could repeat",
  "explanation": "a fuller 2-3 sentence plain-language paragraph walking through what the tool results show and why it leads to that recommendation -- written for someone who wants the full context, not just the bullet points",
  "suggested_follow_ups": "array of 2-3 short, specific follow-up questions the user could naturally ask next, grounded in this data and conversation (not generic filler)"
}"""


def _analytics_block(insights: dict[str, Any]) -> str:
    return json.dumps(insights, indent=2, default=str)


def build_brief_prompt(insights: dict[str, Any], domain: str = "citizen complaints", lang: str = "English") -> str:
    """One-click executive brief over the whole dataset.

    Framed as a handoff document, not a 60-second skim: the reader is
    whoever is responsible for acting on this data and may be seeing it for
    the first time, so the brief must give them full understanding, not just
    the single headline finding.
    """
    return f"""Domain context: {domain}.

Here is the deterministic analytics computed from the uploaded community data:

```json
{_analytics_block(insights)}
```

Write this for someone who is responsible for making changes based on this
data and needs to fully understand it -- not a 60-second skim. Assume they
have not seen this dataset before. Use simple, plain language (avoid jargon
and statistics-speak); explain what the numbers mean in practice, not just
what they are.

Cover the dataset completely: don't cherry-pick only the single biggest
issue -- walk through the overall picture (volume, trend, severity, area and
category spread, status/department breakdown) so the reader has full
context, then call out every unusual or noteworthy pattern you can see in
the analytics, even minor ones.

Recommended actions must be complete and immediately actionable, and each
one must be tagged with how urgently it needs a response so nothing that
requires action today gets missed.

Return ONLY valid JSON (no markdown fences, no prose before/after) matching
exactly this shape:

{json.dumps(_REPORT_SHAPE, indent=2)}

Rules:
- Ground every finding in the analytics above; cite specific counts/areas/categories.
- If a field has no data, say so rather than guessing.
- Do not invent patterns that aren't supported by the analytics.
{_language_instruction(lang)}"""


def build_question_prompt(
    insights: dict[str, Any],
    question: str,
    domain: str = "citizen complaints",
    lang: str = "English",
) -> str:
    """Answer a specific natural-language question over the analytics."""
    return f"""Domain context: {domain}.

Deterministic analytics from the uploaded data:

```json
{_analytics_block(insights)}
```

The user asks: "{question}"

Answer using ONLY the analytics above. Return ONLY valid JSON (no markdown fences)
matching this shape:

{_AGENTIC_ANSWER_SHAPE}

If the analytics do not contain enough information to answer, say so honestly in
'what_is_happening'.
{_language_instruction(lang)}"""


def agentic_system_instruction(lang: str = "English") -> str:
    """Built as a function (not a constant) so the language directive can
    live in the SYSTEM instruction rather than only the per-turn prompt --
    a small model like flash-lite follows a directive in the higher-
    priority system instruction far more reliably than one appended after
    the task description in an ordinary user-turn prompt, which is where
    an earlier version of this put it and Gemini would often just answer
    in English anyway despite the reminder."""
    lang_rule = (
        f"Respond ENTIRELY in {lang} -- every field in your final JSON answer "
        f"(what_is_happening, why_it_matters, recommended_next_step, executive_summary, "
        f"explanation, suggested_follow_ups) must be written in {lang}, not English. "
        f"Area/category names may stay as given in the data if there's no natural "
        f"{lang} equivalent. "
        if lang and lang != "English" else ""
    )
    return (
        "You are CivicPulse AI, a community decision intelligence assistant for city "
        "and neighborhood teams. You have tools that query the REAL uploaded dataset "
        "(get_summary_stats, filter_records, get_top_complaints). You must call one or "
        "more tools to gather evidence before answering -- never answer from memory or "
        "general knowledge about cities. "
        "To compare two areas, categories, or time periods, call filter_records "
        "once per side and compare the real numbers returned. If asked to "
        "compare the top two but the question does not name them, first call "
        "get_summary_stats to find out which two, then call filter_records once "
        "for each before answering. Do not answer a comparison using only one "
        "tool call. "
        "If a tool returns an 'error' field (e.g. an area/category that doesn't exist), "
        "do not guess a substitute value -- either try a corrected argument once, or "
        "tell the user honestly that it wasn't found, using the 'available_values' the "
        "tool gave you. "
        "If a tool returns record_count: 0, that is a real zero -- report it as 'no "
        "matching records', not as missing data. "
        "Once you have enough tool results to answer, STOP calling tools and write the "
        "final answer using ONLY numbers that appeared in tool results. Never invent "
        "a count, percentage, area, or category that didn't come from a tool call. "
        "Clearly separate facts (from tool results) from recommendations (your advice). "
        "Be concise and practical -- write for a busy public official who has 60 seconds. "
        f"{lang_rule}"
    )


def build_agentic_question_prompt(question: str, domain: str = "citizen complaints", lang: str = "English") -> str:
    """Kick off a tool-calling turn for a natural-language question.

    Unlike build_question_prompt, this does NOT embed a precomputed analytics
    blob -- the model must call tools to fetch exactly the evidence it needs,
    which is what makes multi-step questions (comparisons, drill-downs) work.
    """
    return f"""Domain context: {domain}.

The user asks: "{question}"

Use the available tools to gather real evidence from the dataset, then answer.
When you have enough evidence, return ONLY valid JSON (no markdown fences, no
prose before/after) matching this shape:

{_AGENTIC_ANSWER_SHAPE}

If tool results do not contain enough information to answer, say so honestly in
'what_is_happening'.
{_language_instruction(lang)}"""


def build_agentic_followup_prompt(question: str, lang: str = "English") -> str:
    """Continue an existing agentic conversation with a follow-up question.

    Deliberately lighter than build_agentic_question_prompt: the full
    instructions and JSON shape are already in the conversation history (the
    system instruction plus the first turn), so this only needs to state the
    new question and remind the model to fetch fresh evidence rather than
    assume the previous answer's numbers still apply.
    """
    lang_reminder = f" Keep responding in {lang}." if lang and lang != "English" else ""
    return f"""Follow-up question in this same conversation: "{question}"

This may be about a different area, category, time range, or comparison than
before -- call tools again to get evidence specific to THIS question rather
than reusing the previous answer's numbers, unless the question is clearly
still about the same thing. Return ONLY valid JSON in the exact same shape as
your previous answer (no markdown fences, no prose before/after).{lang_reminder}
"""


def build_text_summary_prompt(raw_text: str, domain: str = "citizen complaints", lang: str = "English") -> str:
    """Summarize pasted text or extracted PDF content (no numeric analytics)."""
    snippet = raw_text[:6000]
    return f"""Domain context: {domain}.

The user pasted the following community report / document text:

\"\"\"
{snippet}
\"\"\"

Summarize it for a decision-maker. Return ONLY valid JSON (no markdown fences):

{{
  "title": "<= 8 words",
  "summary": "2-3 sentences",
  "key_findings": ["3-5 bullets"],
  "recommended_actions": [{{"action": "...", "owner": "...", "timeframe": "..."}}],
  "confidence": "high | medium | low"
}}

Do not invent statistics that are not stated in the text.
{_language_instruction(lang)}"""

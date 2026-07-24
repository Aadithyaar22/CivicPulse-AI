"""Deterministic query tools exposed to Gemini via function calling.

This is the core of the "statistics first, Gemini narrates second" guarantee
extended to multi-turn Q&A: every tool here is a thin wrapper around pandas
aggregation over the *real* uploaded DataFrame. Gemini never computes a
number -- it only chooses which of these functions to call and with what
arguments, then explains what the (real) result says.

Guardrails baked in here (see gemini_client.answer_question_agentic for the
loop that uses them):
  1. Fuzzy-but-honest value matching: if the model asks for an area/category
     that doesn't exist, we return an explicit error + the real list of valid
     values instead of silently returning empty/zero data the model could
     misinterpret as "no complaints".
  2. Every successful result carries an explicit `record_count` so the model
     can distinguish "genuinely zero events" from "tool didn't run".
  3. Nothing here ever fabricates a value -- unmatched/unparseable inputs are
     errors, not guesses.
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any

import pandas as pd
from google.genai import types

from .analytics import _open_rate, _severity_distribution, _value_counts
from .utils import humanize, normalize_text

FUZZY_MATCH_THRESHOLD = 0.6
MAX_TOP_N = 10
DEFAULT_TOP_N = 5


# ---------------------------------------------------------------- matching helpers


def _fuzzy_match(value: str, candidates: list[str]) -> str | None:
    """Case-insensitive exact match first, then fuzzy similarity fallback.

    Returns the *original* candidate string (not the normalized form) so
    filters compare correctly against the DataFrame, or None if nothing is
    close enough -- callers must treat None as "not found", never guess.
    """
    if not value or not candidates:
        return None
    norm_value = normalize_text(value)
    norm_map = {normalize_text(c): c for c in candidates}

    if norm_value in norm_map:
        return norm_map[norm_value]

    # substring containment catches things like "koramangala" vs "koramangala 4th block"
    for norm_c, original in norm_map.items():
        if norm_value in norm_c or norm_c in norm_value:
            return original

    best_score, best_match = 0.0, None
    for norm_c, original in norm_map.items():
        score = SequenceMatcher(None, norm_value, norm_c).ratio()
        if score > best_score:
            best_score, best_match = score, original
    return best_match if best_score >= FUZZY_MATCH_THRESHOLD else None


def _match_column_value(df: pd.DataFrame, column: str, value: str) -> dict[str, Any]:
    """Resolve a free-text value against real values in `column`.

    Returns {"matched": <value>} on success or {"error": ..., "available": [...]}
    on failure -- callers should short-circuit on "error".
    """
    if column not in df.columns:
        return {"error": f"Dataset has no '{column}' column."}
    candidates = sorted(df[column].dropna().astype(str).unique().tolist())
    matched = _fuzzy_match(value, candidates)
    if matched is None:
        return {
            "error": f"No {column} matching '{value}' found in this dataset.",
            "available_values": candidates[:25],
        }
    return {"matched": matched}


def _parse_date(value: str | None) -> pd.Timestamp | None:
    if not value:
        return None
    try:
        ts = pd.to_datetime(value, errors="coerce")
        return None if pd.isna(ts) else ts
    except Exception:
        return None


# ---------------------------------------------------------------- tools


def filter_records(
    df: pd.DataFrame,
    area: str | None = None,
    category: str | None = None,
    complaint_type: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Filter the dataset by any combination of area/category/severity/status/date
    range and return an aggregated snapshot of the matching slice. Call this
    twice with different filters to compare two areas, categories, or periods.
    """
    out = df
    applied: list[str] = []
    filtered_cols: set[str] = set()

    for col, raw in (
        ("area", area),
        ("category", category),
        ("complaint_type", complaint_type),
        ("severity", severity),
        ("status", status),
    ):
        if not raw:
            continue
        match = _match_column_value(out, col, raw)
        if "error" in match:
            return match
        out = out[out[col].astype(str) == match["matched"]]
        applied.append(f"{col}={match['matched']}")
        filtered_cols.add(col)

    if start_date or end_date:
        if "date" not in df.columns:
            return {"error": "Dataset has no 'date' column; cannot filter by date."}
        start_ts = _parse_date(start_date)
        end_ts = _parse_date(end_date)
        if start_date and start_ts is None:
            return {"error": f"Could not parse start_date '{start_date}'."}
        if end_date and end_ts is None:
            return {"error": f"Could not parse end_date '{end_date}'."}
        if start_ts is not None:
            out = out[out["date"] >= start_ts]
            applied.append(f"start_date={start_ts.date()}")
        if end_ts is not None:
            out = out[out["date"] <= end_ts]
            applied.append(f"end_date={end_ts.date()}")

    n = int(len(out))
    result: dict[str, Any] = {
        "filters_applied": applied or ["none (full dataset)"],
        "record_count": n,
    }
    if n == 0:
        result["note"] = "No records match these filters. This is a real zero, not missing data."
        return result

    if "date" in out.columns and not out["date"].isna().all():
        valid = out["date"].dropna()
        result["date_range"] = {"start": valid.min().strftime("%Y-%m-%d"), "end": valid.max().strftime("%Y-%m-%d")}
    if "area" not in filtered_cols and "area" in out.columns:
        result["by_area"] = _value_counts(out, "area", top=5)
    if "category" not in filtered_cols and "category" in out.columns:
        result["by_category"] = _value_counts(out, "category", top=5)
    result["severity_distribution"] = _severity_distribution(out)
    result["open_rate_pct"] = _open_rate(out)
    return result


def get_top_complaints(
    df: pd.DataFrame,
    area: str | None = None,
    category: str | None = None,
    n: int = DEFAULT_TOP_N,
) -> dict[str, Any]:
    """Return the top individual complaint records (most severe, most recent
    first) for an optional area/category, so answers can cite specific real
    rows instead of only aggregates.
    """
    out = df
    applied: list[str] = []
    for col, raw in (("area", area), ("category", category)):
        if not raw:
            continue
        match = _match_column_value(out, col, raw)
        if "error" in match:
            return match
        out = out[out[col].astype(str) == match["matched"]]
        applied.append(f"{col}={match['matched']}")

    total = int(len(out))
    if total == 0:
        return {"filters_applied": applied or ["none"], "record_count": 0, "complaints": []}

    n = max(1, min(int(n or DEFAULT_TOP_N), MAX_TOP_N))

    sort_cols, ascending = [], []
    if "severity" in out.columns:
        sev_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        out = out.assign(_sev_rank=out["severity"].map(lambda s: sev_rank.get(normalize_text(s), 4)))
        sort_cols.append("_sev_rank")
        ascending.append(True)
    if "date" in out.columns:
        sort_cols.append("date")
        ascending.append(False)

    ordered = out.sort_values(sort_cols, ascending=ascending) if sort_cols else out
    rows = ordered.head(n)

    fields = ["date", "area", "category", "complaint_type", "severity", "status", "notes"]
    complaints = []
    for _, r in rows.iterrows():
        rec = {}
        for f in fields:
            if f not in rows.columns:
                continue
            val = r[f]
            if pd.isna(val):
                continue
            rec[f] = val.strftime("%Y-%m-%d") if f == "date" else (humanize(val) if f in {"area", "category", "complaint_type", "severity", "status"} else str(val))
        complaints.append(rec)

    return {"filters_applied": applied or ["none"], "record_count": total, "returned": len(complaints), "complaints": complaints}


def get_summary_stats(df: pd.DataFrame) -> dict[str, Any]:
    """Return the full precomputed dataset snapshot (counts, trend, anomalies,
    decision scores, forecasts, hotspot map) -- the same numbers shown on the
    Overview tab. Good first call for broad questions before drilling down.
    """
    from .analytics import compute_insights

    return compute_insights(df).to_dict()


# ---------------------------------------------------------------- Gemini tool schema

TOOL_DECLARATIONS = [
    types.FunctionDeclaration(
        name="get_summary_stats",
        description=(
            "Get the full dataset snapshot: totals, top area/category, weekly trend, "
            "severity mix, anomalies, decision scores (urgency/impact/confidence), "
            "7-day forecasts per area, and the hotspot map. Use this first for broad "
            "questions like 'what should we prioritize' before drilling down."
        ),
        parameters=types.Schema(type="OBJECT", properties={}, required=[]),
    ),
    types.FunctionDeclaration(
        name="filter_records",
        description=(
            "Query a filtered slice of the complaints dataset by area, category, "
            "complaint_type, severity, status, and/or a date range (start_date/end_date "
            "as YYYY-MM-DD). Returns counts and breakdowns for that slice. Call this "
            "twice with different filters to compare two areas, categories, or time "
            "periods against each other."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "area": types.Schema(type="STRING", description="Area/ward/neighborhood name, e.g. 'Koramangala'."),
                "category": types.Schema(type="STRING", description="Issue category, e.g. 'waste', 'water', 'roads'."),
                "complaint_type": types.Schema(type="STRING", description="Specific complaint subtype, if known."),
                "severity": types.Schema(type="STRING", description="One of: low, medium, high, critical."),
                "status": types.Schema(type="STRING", description="Case status, e.g. 'open', 'resolved'."),
                "start_date": types.Schema(type="STRING", description="ISO date YYYY-MM-DD, inclusive lower bound."),
                "end_date": types.Schema(type="STRING", description="ISO date YYYY-MM-DD, inclusive upper bound."),
            },
            required=[],
        ),
    ),
    types.FunctionDeclaration(
        name="get_top_complaints",
        description=(
            "Get the most severe/most recent individual complaint records, optionally "
            "filtered by area and/or category. Use this to cite specific real examples "
            "rather than only aggregate counts."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "area": types.Schema(type="STRING", description="Area/ward/neighborhood name."),
                "category": types.Schema(type="STRING", description="Issue category."),
                "n": types.Schema(type="INTEGER", description=f"How many records to return, 1-{MAX_TOP_N} (default {DEFAULT_TOP_N})."),
            },
            required=[],
        ),
    ),
]

_DISPATCH = {
    "get_summary_stats": get_summary_stats,
    "filter_records": filter_records,
    "get_top_complaints": get_top_complaints,
}


def dispatch_tool(df: pd.DataFrame, name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Execute a tool call by name. Unknown tool names are an error, not a no-op,
    so a hallucinated tool name surfaces to the model instead of being ignored."""
    fn = _DISPATCH.get(name)
    if fn is None:
        return {"error": f"Unknown tool '{name}'."}
    try:
        return fn(df, **(args or {}))
    except TypeError as exc:
        return {"error": f"Bad arguments for '{name}': {exc}"}
    except Exception as exc:  # defensive -- a tool bug must not crash the chat
        return {"error": f"Tool '{name}' failed: {exc}"}

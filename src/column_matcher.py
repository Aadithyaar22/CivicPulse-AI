"""Generalized column detection for messy, unseen datasets.

The old approach was a fixed alias table: a column matched only if its name
was an exact string in a hardcoded list. That breaks the moment a new
dataset uses a header we didn't anticipate (this is exactly what happened
with the real BBMP data's "Ward Name" / "Grievance Date" columns).

This module instead *scores* every column against every canonical field
using three signals, in order of trust:

  1. Exact match on a known alias       (score 1.0 -- highest confidence)
  2. Token/substring overlap            (e.g. "ward_name" contains "ward")
  3. Fuzzy string similarity            (typos, abbreviations: "catgory")

For "date" and "status" specifically -- the two fields analytics leans on
most -- it also falls back to sniffing the actual *values* when no column
name matches well enough (e.g. a column named "col_7" that's 95% parseable
as a date is still detected as the date column).

Every match is returned with its confidence and reasoning so the UI can
show the user what got mapped to what, instead of silently guessing.
"""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass
from difflib import SequenceMatcher

import pandas as pd

from .utils import COLUMN_ALIASES, normalize_text

# Below this score, a name-based match is not trusted at all.
MIN_MATCH_SCORE = 0.6

# Common status vocabulary used for content-sniffing when no column name
# gives it away. Deliberately broad -- covers civic/government datasets
# (registered, closed) as well as generic ticketing systems (open, resolved).
STATUS_VOCAB = {
    "open", "closed", "pending", "resolved", "unresolved", "in progress",
    "registered", "reopen", "re-open", "new", "assigned", "escalated",
    "completed", "cancelled", "canceled", "non relevant", "rejected",
    "under process", "field verification", "long term solution",
}


@dataclass
class ColumnMatch:
    source_column: str
    canonical: str
    score: float
    method: str  # "exact" | "token" | "fuzzy" | "content"


def _tokens(text: str) -> set[str]:
    # Split camelCase/PascalCase boundaries first (e.g. "IssueCategory" -> "Issue Category")
    # so token overlap can see "category" inside a column with no separator.
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", str(text))
    return set(re.split(r"[^a-z0-9]+", normalize_text(spaced))) - {""}


def _token_overlap_score(col_tokens: set[str], alias_tokens: set[str]) -> float:
    if not col_tokens or not alias_tokens:
        return 0.0
    overlap = col_tokens & alias_tokens
    if not overlap:
        return 0.0
    return len(overlap) / len(alias_tokens)


def _fuzzy_score(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _best_name_match(column: str, canonical: str, aliases: list[str]) -> tuple[float, str]:
    """Best score for one column against one canonical field's alias list."""
    norm_col = normalize_text(column)
    col_tokens = _tokens(column)
    best_score = 0.0
    best_method = "none"

    for alias in [canonical] + aliases:
        norm_alias = normalize_text(alias)

        if norm_col == norm_alias:
            return 1.0, "exact"

        token_score = _token_overlap_score(col_tokens, _tokens(alias))
        if token_score > best_score:
            best_score, best_method = token_score, "token"

        fuzzy = _fuzzy_score(norm_col, norm_alias)
        if fuzzy > best_score:
            best_score, best_method = fuzzy, "fuzzy"

    return best_score, best_method


def _sniff_date_column(df: pd.DataFrame, candidate_columns: list[str]) -> str | None:
    """Finds an unassigned column that's mostly parseable as dates."""
    best_col, best_rate = None, 0.0
    for col in candidate_columns:
        series = df[col]
        if pd.api.types.is_numeric_dtype(series):
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            parsed = pd.to_datetime(series, errors="coerce")
        rate = parsed.notna().mean() if len(series) else 0.0
        if rate > 0.8 and rate > best_rate:
            best_col, best_rate = col, rate
    return best_col


def _sniff_status_column(df: pd.DataFrame, candidate_columns: list[str]) -> str | None:
    """Finds an unassigned low-cardinality column whose values look like statuses."""
    best_col, best_overlap = None, 0.0
    for col in candidate_columns:
        series = df[col].dropna().astype(str).map(normalize_text)
        if series.empty:
            continue
        uniques = set(series.unique())
        if len(uniques) > 20:
            continue
        overlap = len(uniques & STATUS_VOCAB) / len(uniques)
        if overlap > 0.5 and overlap > best_overlap:
            best_col, best_overlap = col, overlap
    return best_col


def detect_columns(df: pd.DataFrame) -> tuple[dict[str, str], list[ColumnMatch]]:
    """Returns ({source_column: canonical}, [ColumnMatch, ...]) for a raw DataFrame."""
    candidates: list[ColumnMatch] = []
    for column in df.columns:
        for canonical, aliases in COLUMN_ALIASES.items():
            score, method = _best_name_match(str(column), canonical, aliases)
            if score >= MIN_MATCH_SCORE:
                candidates.append(ColumnMatch(str(column), canonical, round(score, 2), method))

    candidates.sort(key=lambda m: m.score, reverse=True)

    used_columns: set[str] = set()
    used_canonicals: set[str] = set()
    accepted: list[ColumnMatch] = []
    for match in candidates:
        if match.source_column in used_columns or match.canonical in used_canonicals:
            continue
        accepted.append(match)
        used_columns.add(match.source_column)
        used_canonicals.add(match.canonical)

    remaining = [c for c in df.columns if str(c) not in used_columns]
    if "date" not in used_canonicals and remaining:
        found = _sniff_date_column(df, remaining)
        if found:
            accepted.append(ColumnMatch(found, "date", 0.0, "content"))
            used_columns.add(found)
            remaining = [c for c in remaining if c != found]

    if "status" not in used_canonicals and remaining:
        found = _sniff_status_column(df, remaining)
        if found:
            accepted.append(ColumnMatch(found, "status", 0.0, "content"))

    mapping = {m.source_column: m.canonical for m in accepted}
    return mapping, accepted

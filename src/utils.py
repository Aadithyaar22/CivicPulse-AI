"""Small shared helpers used across CivicPulse AI."""

from __future__ import annotations

import json
import re
from typing import Any

# Canonical column names the analytics layer expects. The loader tries to
# map messy real-world headers onto these.
CANONICAL_COLUMNS = [
    "date",
    "area",
    "category",
    "complaint_type",
    "severity",
    "status",
    "department",
    "notes",
]

# Common aliases -> canonical name. Keeps the app forgiving about messy CSVs.
COLUMN_ALIASES = {
    "date": ["date", "reported_on", "created_at", "timestamp", "day", "logged_date",
             "grievance date", "complaint date", "reported date", "date reported"],
    "area": ["area", "neighborhood", "neighbourhood", "ward", "zone", "region", "locality",
             "district", "ward name", "ward_name"],
    "category": ["category", "type", "service", "domain", "service_type"],
    "complaint_type": ["complaint_type", "issue", "issue_type", "problem", "subtype",
                        "description_type", "sub category", "subcategory", "sub_category"],
    "severity": ["severity", "priority", "urgency", "level"],
    "status": ["status", "state", "resolution", "stage", "grievance status", "complaint status"],
    "department": ["department", "dept", "agency", "team", "owner"],
    "notes": ["notes", "note", "comment", "comments", "remark", "remarks", "details",
              "staff remarks", "staff_remarks"],
}

SEVERITY_ORDER = ["low", "medium", "high", "critical"]
SEVERITY_WEIGHTS = {"low": 1, "medium": 2, "high": 3, "critical": 4}

OPEN_STATUSES = {
    "open", "pending", "in progress", "in_progress", "new", "unresolved", "escalated",
    "registered", "reopen", "re-open", "re opened", "assigned", "under process",
    "long term solution", "field verification",
}


def normalize_text(value: Any) -> str:
    """Lowercase + strip for robust comparisons."""
    return str(value).strip().lower()


def slugify(value: str) -> str:
    value = normalize_text(value)
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def extract_json(text: str) -> dict | None:
    """Best-effort extraction of a JSON object from an LLM response.

    Handles ```json fences and stray prose around the object.
    """
    if not text:
        return None

    # Strip markdown code fences if present.
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text

    # Fall back to the first balanced-looking {...} block.
    if not fenced:
        brace = re.search(r"\{.*\}", candidate, re.DOTALL)
        if brace:
            candidate = brace.group(0)

    try:
        return json.loads(candidate)
    except (json.JSONDecodeError, TypeError):
        return None


def humanize(text: str) -> str:
    """Turn a slug/snake string into a readable Title Case label."""
    return re.sub(r"[_\-]+", " ", str(text)).strip().title()

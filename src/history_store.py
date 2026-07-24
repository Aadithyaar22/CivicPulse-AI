"""Optional Firestore-backed history for generated Executive Briefs.

Turns CivicPulse from a single-session snapshot tool into something a team
can trust across repeated uploads: every successfully generated (non-fallback)
brief is saved with its key numbers, so "how has Riverside trended over the
last month" has a real answer instead of only "what does today's upload say."

Entirely optional and additive: if Firestore isn't reachable (no ADC set up
locally, API not enabled, database missing), the app keeps working exactly as
it did before this module existed -- persistence is just silently disabled,
matching the same "never let infrastructure take down the demo" philosophy as
GeminiClient's offline fallback.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

COLLECTION = "civicpulse_briefs"
MAX_RECENT = 10


class HistoryStore:
    """Lazy-initialized client. Never raises on construction."""

    def __init__(self):
        self._client = None
        self._init_error: str | None = None
        try:
            from google.cloud import firestore

            project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCLOUD_PROJECT")
            self._client = firestore.Client(project=project) if project else firestore.Client()
        except Exception as exc:  # pragma: no cover - defensive, matches GeminiClient pattern
            self._init_error = str(exc)

    @property
    def available(self) -> bool:
        return self._client is not None

    @property
    def status_message(self) -> str:
        if self.available:
            return "Connected."
        return self._init_error or "Firestore unavailable."

    def save_brief(
        self,
        *,
        domain: str,
        source_type: str,
        insights: dict[str, Any],
        brief_data: dict[str, Any],
    ) -> str | None:
        """Save a generated brief's key numbers. Returns the doc id, or None
        if persistence isn't available -- callers should treat None as a
        no-op, never as an error to surface to the user."""
        if not self.available:
            return None
        try:
            doc = {
                "created_at": datetime.now(timezone.utc),
                "domain": domain,
                "source_type": source_type,
                "total_records": insights.get("total_records"),
                "hotspot_area": insights.get("hotspot_area"),
                "top_category": insights.get("top_category"),
                "trend_direction": insights.get("trend_direction"),
                "trend_change_pct": insights.get("trend_change_pct"),
                "open_rate_pct": insights.get("open_rate_pct"),
                "scores": insights.get("scores"),
                "brief_title": brief_data.get("title"),
                "brief_summary": brief_data.get("summary"),
                "recommended_actions": brief_data.get("recommended_actions"),
                "confidence": brief_data.get("confidence"),
            }
            _update_time, doc_ref = self._client.collection(COLLECTION).add(doc)
            return doc_ref.id
        except Exception:
            # Persistence is a bonus feature -- a Firestore hiccup must never
            # break the brief the user already has on screen.
            return None

    def list_recent(self, limit: int = MAX_RECENT) -> list[dict[str, Any]]:
        if not self.available:
            return []
        try:
            from google.cloud import firestore

            query = (
                self._client.collection(COLLECTION)
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            out = []
            for snap in query.stream():
                rec = snap.to_dict()
                rec["id"] = snap.id
                out.append(rec)
            return out
        except Exception:
            return []

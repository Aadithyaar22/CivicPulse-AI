"""Optional Firestore-backed session persistence, so reloading the page
doesn't silently wipe the loaded dataset and chat history.

Streamlit's st.session_state is an in-memory object tied to one browser
session -- a page reload opens a fresh session server-side, so without this
there is nothing to restore from. app.py pairs this with a session id kept
in the URL's query params (?sid=...), which DOES survive a reload, to know
which saved session to look up.

Same philosophy as history_store.py: entirely optional and additive. If
Firestore isn't reachable, or a given dataset is too large to persist,
the app keeps working exactly as it did before this module existed --
persistence (and therefore reload-survival) just silently doesn't apply.

Storage layout (two documents per session, each within Firestore's 1 MiB
per-document cap so a large chat history and a large dataset don't compete
for the same budget):
    civicpulse_sessions/{sid}              -- domain, chat history, brief
    civicpulse_sessions/{sid}/blobs/dataset -- the loaded dataframe as CSV text

Sessions expire on their own: every write refreshes an `expires_at` field,
and `load()` treats an already-past `expires_at` as a miss even before
Firestore's own TTL sweep (which runs asynchronously, not instantly) gets to
it. Enabling the native TTL policy (one-time, see README) is what actually
reclaims the storage; without it, stale docs still stop being served, they
just aren't deleted until you enable it.
"""

from __future__ import annotations

import io
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

COLLECTION = "civicpulse_sessions"
SESSION_TTL_HOURS = 24
# Firestore caps a document at 1 MiB; leave headroom for the rest of the
# metadata doc (chat history, brief) by capping the CSV blob well under that.
MAX_CSV_BYTES = 850_000
MAX_QA_TURNS_PERSISTED = 20


class SessionStore:
    """Lazy-initialized client. Never raises on construction."""

    def __init__(self):
        self._client = None
        self._init_error: str | None = None
        try:
            from google.cloud import firestore

            project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCLOUD_PROJECT")
            self._client = firestore.Client(project=project) if project else firestore.Client()
        except Exception as exc:  # pragma: no cover - defensive, matches HistoryStore pattern
            self._init_error = str(exc)

    @property
    def available(self) -> bool:
        return self._client is not None

    @property
    def status_message(self) -> str:
        if self.available:
            return "Connected."
        return self._init_error or "Firestore unavailable."

    def save(
        self,
        session_id: str,
        *,
        df: pd.DataFrame | None,
        source_type: str | None,
        raw_text: str | None,
        domain: str,
        qa_history: list[tuple[str, dict[str, Any]]],
        brief: dict[str, Any] | None,
    ) -> None:
        """Persist the current session. Best-effort: a Firestore hiccup, or a
        dataset too large to fit the per-document cap, must never break the
        live session the user already has on screen -- this only ever
        affects whether a future reload can restore it."""
        if not self.available:
            return
        try:
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(hours=SESSION_TTL_HOURS)
            doc_ref = self._client.collection(COLLECTION).document(session_id)

            doc_ref.set(
                {
                    "updated_at": now,
                    "expires_at": expires_at,
                    "source_type": source_type,
                    "domain": domain,
                    "raw_text": raw_text if (raw_text and len(raw_text) < MAX_CSV_BYTES) else None,
                    "has_dataset": df is not None and not df.empty,
                    "qa_history": [
                        {"question": q, "result": r} for q, r in qa_history[-MAX_QA_TURNS_PERSISTED:]
                    ],
                    "brief": brief,
                }
            )

            blob_ref = doc_ref.collection("blobs").document("dataset")
            if df is not None and not df.empty:
                csv_text = df.to_csv(index=False)
                if len(csv_text.encode("utf-8")) <= MAX_CSV_BYTES:
                    blob_ref.set({"csv": csv_text, "expires_at": expires_at})
                else:
                    # Too large to persist -- leave any previous blob alone
                    # (the metadata doc's has_dataset already reflects an
                    # unpersistable dataset via source_type, so load() won't
                    # promise a df it can't deliver) and skip, don't error.
                    blob_ref.delete()
            else:
                blob_ref.delete()
        except Exception:
            pass

    def load(self, session_id: str) -> dict[str, Any] | None:
        """Returns a dict of restorable fields, or None if there's nothing
        (or nothing still valid) to restore for this session id."""
        if not self.available:
            return None
        try:
            doc_ref = self._client.collection(COLLECTION).document(session_id)
            snap = doc_ref.get()
            if not snap.exists:
                return None
            data = snap.to_dict() or {}

            expires_at = data.get("expires_at")
            if expires_at is not None and expires_at < datetime.now(timezone.utc):
                return None

            df = None
            if data.get("has_dataset"):
                blob_snap = doc_ref.collection("blobs").document("dataset").get()
                if blob_snap.exists:
                    csv_text = (blob_snap.to_dict() or {}).get("csv")
                    if csv_text:
                        df = pd.read_csv(io.StringIO(csv_text))

            return {
                "df": df,
                "source_type": data.get("source_type"),
                "raw_text": data.get("raw_text"),
                "domain": data.get("domain"),
                "qa_history": data.get("qa_history") or [],
                "brief": data.get("brief"),
            }
        except Exception:
            return None

    def clear(self, session_id: str) -> None:
        """Best-effort delete, used when the user explicitly loads new data
        or starts a new conversation -- keeps a stale restore from resurfacing
        old data if a later save() is skipped (e.g. an oversized dataset)."""
        if not self.available:
            return
        try:
            doc_ref = self._client.collection(COLLECTION).document(session_id)
            doc_ref.collection("blobs").document("dataset").delete()
            doc_ref.delete()
        except Exception:
            pass

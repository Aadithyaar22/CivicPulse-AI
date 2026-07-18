"""Data ingestion: load and normalize CSV / JSON / PDF / pasted text.

The goal is to accept messy community datasets and coerce them into a tidy
DataFrame with canonical columns so the analytics layer can stay simple.
"""

from __future__ import annotations

import io
import json
from dataclasses import dataclass, field

import pandas as pd

from .utils import COLUMN_ALIASES, normalize_text


@dataclass
class LoadResult:
    """Outcome of a load attempt."""

    df: pd.DataFrame
    source_type: str
    warnings: list[str] = field(default_factory=list)
    raw_text: str | None = None  # for pasted text / PDF, keep the original


def _map_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Rename incoming columns onto canonical names using the alias table."""
    warnings: list[str] = []
    lower_map = {normalize_text(c): c for c in df.columns}
    rename: dict[str, str] = {}

    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower_map:
                rename[lower_map[alias]] = canonical
                break

    df = df.rename(columns=rename)

    # Ensure we at least have something to group on.
    if "area" not in df.columns and "category" not in df.columns:
        warnings.append(
            "No 'area' or 'category' column detected. Analytics will be limited."
        )
    return df, warnings


def _coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """Best-effort type coercion for known columns."""
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ("area", "category", "complaint_type", "severity", "status", "department"):
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()
    return df


def load_csv(file_or_buffer) -> LoadResult:
    df = pd.read_csv(file_or_buffer)
    df, warnings = _map_columns(df)
    df = _coerce_types(df)
    return LoadResult(df=df, source_type="csv", warnings=warnings)


def load_json(file_or_buffer) -> LoadResult:
    raw = file_or_buffer.read() if hasattr(file_or_buffer, "read") else file_or_buffer
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    data = json.loads(raw)

    # Accept either a list of records or {"records": [...]} style payloads.
    if isinstance(data, dict):
        for key in ("records", "data", "rows", "items"):
            if key in data and isinstance(data[key], list):
                data = data[key]
                break
    df = pd.json_normalize(data)
    df, warnings = _map_columns(df)
    df = _coerce_types(df)
    return LoadResult(df=df, source_type="json", warnings=warnings)


def load_pdf(file_or_buffer) -> LoadResult:
    """Extract plain text from a PDF. Text stays as raw_text for AI summary."""
    try:
        import pdfplumber
    except ImportError:  # pragma: no cover - dependency guaranteed in requirements
        return LoadResult(
            df=pd.DataFrame(),
            source_type="pdf",
            warnings=["pdfplumber not installed; cannot read PDF."],
            raw_text=None,
        )

    text_chunks: list[str] = []
    with pdfplumber.open(file_or_buffer) as pdf:
        for page in pdf.pages:
            text_chunks.append(page.extract_text() or "")
    text = "\n".join(text_chunks).strip()
    warnings = [] if text else ["No extractable text found in the PDF."]
    return LoadResult(df=pd.DataFrame(), source_type="pdf", warnings=warnings, raw_text=text)


def load_text(text: str) -> LoadResult:
    return LoadResult(df=pd.DataFrame(), source_type="text", warnings=[], raw_text=text)


def load_uploaded_file(uploaded_file) -> LoadResult:
    """Dispatch a Streamlit UploadedFile to the right loader by extension."""
    name = getattr(uploaded_file, "name", "").lower()
    if name.endswith(".csv"):
        return load_csv(uploaded_file)
    if name.endswith(".json"):
        return load_json(uploaded_file)
    if name.endswith(".pdf"):
        return load_pdf(uploaded_file)
    # Fallback: try CSV, then treat as plain text.
    try:
        uploaded_file.seek(0)
        return load_csv(uploaded_file)
    except Exception:
        uploaded_file.seek(0)
        raw = uploaded_file.read()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        return load_text(raw)


def load_sample(path: str) -> LoadResult:
    """Load a bundled sample CSV from disk."""
    with open(path, "rb") as fh:
        buffer = io.BytesIO(fh.read())
    return load_csv(buffer)

"""Deterministic analytics computed in pure Python before any AI call.

Everything the model sees comes from here, so numbers are never hallucinated.
The output is a compact, JSON-serializable dict passed to Gemini.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from .utils import (
    OPEN_STATUSES,
    SEVERITY_WEIGHTS,
    clamp,
    humanize,
    normalize_text,
)


@dataclass
class Anomaly:
    label: str
    dimension: str
    detail: str
    score: float  # z-score-like magnitude


@dataclass
class Insights:
    """Structured, model-ready snapshot of the dataset."""

    total_records: int = 0
    date_range: dict[str, str] = field(default_factory=dict)
    by_area: dict[str, int] = field(default_factory=dict)
    by_category: dict[str, int] = field(default_factory=dict)
    by_status: dict[str, int] = field(default_factory=dict)
    by_department: dict[str, int] = field(default_factory=dict)
    severity_distribution: dict[str, int] = field(default_factory=dict)
    top_complaint_types: dict[str, int] = field(default_factory=dict)
    weekly_trend: list[dict[str, Any]] = field(default_factory=list)
    trend_direction: str = "flat"
    trend_change_pct: float = 0.0
    open_rate_pct: float = 0.0
    hotspot_area: str | None = None
    top_category: str | None = None
    anomalies: list[dict[str, Any]] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _value_counts(df: pd.DataFrame, col: str, top: int = 10) -> dict[str, int]:
    if col not in df.columns:
        return {}
    counts = df[col].dropna().astype(str).value_counts().head(top)
    return {str(k): int(v) for k, v in counts.items()}


def _weekly_trend(df: pd.DataFrame) -> list[dict[str, Any]]:
    if "date" not in df.columns or df["date"].isna().all():
        return []
    series = (
        df.dropna(subset=["date"])
        .set_index("date")
        .assign(_n=1)["_n"]
        .resample("W")
        .sum()
    )
    return [
        {"week": idx.strftime("%Y-%m-%d"), "count": int(val)}
        for idx, val in series.items()
    ]


def _trend_summary(weekly: list[dict[str, Any]]) -> tuple[str, float]:
    """Compare the last two weeks with nonzero data to describe the trend."""
    nonzero = [w for w in weekly if w["count"] > 0]
    if len(nonzero) < 2:
        return "flat", 0.0
    prev, last = nonzero[-2]["count"], nonzero[-1]["count"]
    if prev == 0:
        return ("rising", 100.0) if last > 0 else ("flat", 0.0)
    change = (last - prev) / prev * 100.0
    if change > 10:
        return "rising", round(change, 1)
    if change < -10:
        return "falling", round(change, 1)
    return "flat", round(change, 1)


def _severity_distribution(df: pd.DataFrame) -> dict[str, int]:
    if "severity" not in df.columns:
        return {}
    normalized = df["severity"].dropna().map(normalize_text)
    return {str(k): int(v) for k, v in normalized.value_counts().items()}


def _open_rate(df: pd.DataFrame) -> float:
    if "status" not in df.columns or df.empty:
        return 0.0
    statuses = df["status"].dropna().map(normalize_text)
    if statuses.empty:
        return 0.0
    open_count = statuses.isin(OPEN_STATUSES).sum()
    return round(open_count / len(statuses) * 100.0, 1)


def _detect_anomalies(df: pd.DataFrame) -> list[Anomaly]:
    """Simple, explainable anomaly detection.

    1. Category volume spikes vs. the mean (z-score > 1.5).
    2. Area volume spikes vs. the mean.
    3. Week-over-week surge in total volume.
    """
    anomalies: list[Anomaly] = []

    def _spike(col: str, dimension: str) -> None:
        if col not in df.columns:
            return
        counts = df[col].dropna().astype(str).value_counts()
        if len(counts) < 3:
            return
        mean, std = counts.mean(), counts.std(ddof=0)
        if std == 0:
            return
        for label, count in counts.items():
            z = (count - mean) / std
            if z >= 1.5:
                anomalies.append(
                    Anomaly(
                        label=humanize(label),
                        dimension=dimension,
                        detail=f"{count} records ({z:.1f}σ above the {dimension} average).",
                        score=round(float(z), 2),
                    )
                )

    _spike("category", "category")
    _spike("area", "area")
    _spike("complaint_type", "complaint type")

    # Week-over-week surge.
    weekly = _weekly_trend(df)
    nonzero = [w for w in weekly if w["count"] > 0]
    if len(nonzero) >= 3:
        counts = np.array([w["count"] for w in nonzero], dtype=float)
        mean, std = counts[:-1].mean(), counts[:-1].std(ddof=0)
        last = counts[-1]
        if std > 0:
            z = (last - mean) / std
            if z >= 1.5:
                anomalies.append(
                    Anomaly(
                        label=f"Volume surge week of {nonzero[-1]['week']}",
                        dimension="time",
                        detail=f"{int(last)} records vs. ~{mean:.0f} typical ({z:.1f}σ).",
                        score=round(float(z), 2),
                    )
                )

    anomalies.sort(key=lambda a: a.score, reverse=True)
    return anomalies[:6]


def _severity_index(df: pd.DataFrame) -> float:
    """Mean severity weight normalized to 0-100."""
    if "severity" not in df.columns:
        return 40.0
    weights = df["severity"].dropna().map(
        lambda s: SEVERITY_WEIGHTS.get(normalize_text(s), 2)
    )
    if weights.empty:
        return 40.0
    return clamp((weights.mean() / 4.0) * 100.0)


def _scores(df: pd.DataFrame, anomalies: list[Anomaly], trend: str, open_rate: float) -> dict[str, float]:
    """Decision Scoreboard: urgency, impact, confidence (all 0-100)."""
    severity_index = _severity_index(df)
    anomaly_boost = min(len(anomalies) * 8.0, 30.0)
    trend_boost = 15.0 if trend == "rising" else (-10.0 if trend == "falling" else 0.0)

    urgency = clamp(0.5 * severity_index + 0.3 * open_rate + anomaly_boost + trend_boost)

    # Impact scales with volume and how concentrated the top area is.
    volume = len(df)
    volume_score = clamp(np.log1p(volume) / np.log1p(500) * 100.0)
    concentration = 0.0
    if "area" in df.columns and not df["area"].dropna().empty:
        top_share = df["area"].value_counts(normalize=True).iloc[0] * 100.0
        concentration = clamp(top_share)
    impact = clamp(0.6 * volume_score + 0.4 * concentration)

    # Confidence scales with data volume and field completeness.
    key_cols = [c for c in ("date", "area", "category", "severity") if c in df.columns]
    completeness = (len(key_cols) / 4.0) * 100.0
    confidence = clamp(0.5 * completeness + 0.5 * volume_score)

    return {
        "urgency": round(float(urgency), 1),
        "impact": round(float(impact), 1),
        "confidence": round(float(confidence), 1),
        "severity_index": round(float(severity_index), 1),
    }


def compute_insights(df: pd.DataFrame) -> Insights:
    """Main entry point: turn a tidy DataFrame into an Insights snapshot."""
    if df is None or df.empty:
        return Insights()

    weekly = _weekly_trend(df)
    trend_direction, trend_change = _trend_summary(weekly)
    open_rate = _open_rate(df)
    anomalies = _detect_anomalies(df)

    by_area = _value_counts(df, "area")
    by_category = _value_counts(df, "category")

    date_range = {}
    if "date" in df.columns and not df["date"].isna().all():
        valid = df["date"].dropna()
        date_range = {
            "start": valid.min().strftime("%Y-%m-%d"),
            "end": valid.max().strftime("%Y-%m-%d"),
        }

    return Insights(
        total_records=int(len(df)),
        date_range=date_range,
        by_area=by_area,
        by_category=by_category,
        by_status=_value_counts(df, "status"),
        by_department=_value_counts(df, "department"),
        severity_distribution=_severity_distribution(df),
        top_complaint_types=_value_counts(df, "complaint_type"),
        weekly_trend=weekly,
        trend_direction=trend_direction,
        trend_change_pct=trend_change,
        open_rate_pct=open_rate,
        hotspot_area=next(iter(by_area), None),
        top_category=next(iter(by_category), None),
        anomalies=[asdict(a) for a in anomalies],
        scores=_scores(df, anomalies, trend_direction, open_rate),
    )


def filter_dataframe(
    df: pd.DataFrame,
    area: str | None = None,
    category: str | None = None,
) -> pd.DataFrame:
    """Optional slicing used by the UI filters."""
    out = df
    if area and area != "All" and "area" in out.columns:
        out = out[out["area"].astype(str) == area]
    if category and category != "All" and "category" in out.columns:
        out = out[out["category"].astype(str) == category]
    return out

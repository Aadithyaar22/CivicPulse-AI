"""Geographic intelligence for CivicPulse AI.

Turns the "area" column into a hotspot map instead of a text label. Area
names in community datasets (ward names, neighborhoods) rarely come with
coordinates attached, so this module deterministically derives a stable
lat/lon per area name (placeholder positions arranged around a city
center) so the map renders consistently across runs.

In a real city deployment, replace `_placeholder_coords` with a lookup
against an actual ward/neighborhood geocoding table -- wards don't move,
so this is a one-time mapping to maintain, not a per-request geocode call.
"""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
import pandas as pd

DEFAULT_CENTER_LAT = 12.9716
DEFAULT_CENTER_LON = 77.5946
SPREAD_DEGREES = 0.09


def _placeholder_coords(area: str, center_lat: float, center_lon: float) -> tuple[float, float]:
    """Deterministically maps an area name to a stable point near the center."""
    h = int(hashlib.sha256(area.encode()).hexdigest(), 16)
    rng = np.random.RandomState(h % (2**32))
    dlat, dlon = rng.uniform(-1, 1, size=2) * SPREAD_DEGREES
    return center_lat + dlat, center_lon + dlon


def build_geo_summary(
    df: pd.DataFrame,
    area_coords: dict[str, tuple[float, float]] | None = None,
    center: tuple[float, float] = (DEFAULT_CENTER_LAT, DEFAULT_CENTER_LON),
) -> list[dict[str, Any]]:
    """Aggregates complaints per area into a hotspot score ready for a map layer."""
    if df is None or df.empty or "area" not in df.columns:
        return []

    area_coords = area_coords or {}
    counts_by_area = df["area"].dropna().astype(str).value_counts()
    max_count = counts_by_area.max() if not counts_by_area.empty else 1

    summary = []
    for area, group in df.groupby(df["area"].astype(str)):
        if area in area_coords:
            lat, lon = area_coords[area]
        else:
            lat, lon = _placeholder_coords(area, *center)

        total = len(group)
        if "status" in group.columns:
            open_rate = (~group["status"].astype(str).str.lower().isin(
                {"resolved", "closed", "completed"}
            )).mean()
        else:
            open_rate = 0.0
        if "severity" in group.columns:
            high_sev_rate = group["severity"].astype(str).str.lower().isin(
                {"high", "critical"}
            ).mean()
        else:
            high_sev_rate = 0.0

        volume_score = (total / max_count) * 40
        severity_score = high_sev_rate * 30
        backlog_score = open_rate * 30
        hotspot_score = round(float(volume_score + severity_score + backlog_score), 1)

        summary.append({
            "area": area,
            "lat": round(float(lat), 5),
            "lon": round(float(lon), 5),
            "total_complaints": int(total),
            "open_rate_pct": round(float(open_rate) * 100, 1),
            "high_severity_rate_pct": round(float(high_sev_rate) * 100, 1),
            "hotspot_score": hotspot_score,
        })

    return sorted(summary, key=lambda x: x["hotspot_score"], reverse=True)

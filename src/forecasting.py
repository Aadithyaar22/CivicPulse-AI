"""Short-horizon forecasting for CivicPulse AI.

Predicts near-term complaint volume per area instead of only flagging
anomalies after they've already happened. Uses Holt's linear trend method
(double exponential smoothing) -- lightweight enough to run per-request on
Cloud Run, but trend-aware enough to catch an accelerating spike, unlike
plain (single) exponential smoothing which only tracks level.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
import pandas as pd

MIN_DAYS_REQUIRED = 7


@dataclass
class AreaForecast:
    area: str
    status: str  # "ok" | "insufficient_data"
    last_7day_avg: float = 0.0
    forecast_7day_avg: float = 0.0
    pct_change: float = 0.0
    daily_forecast: list[float] = field(default_factory=list)
    will_likely_spike: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _daily_series(df: pd.DataFrame, area: str) -> pd.Series:
    area_df = df[df["area"].astype(str) == area]
    if "date" not in area_df.columns or area_df["date"].isna().all():
        return pd.Series(dtype=float)
    daily = (
        area_df.dropna(subset=["date"])
        .set_index("date")
        .assign(_n=1)["_n"]
        .resample("D")
        .sum()
    )
    return daily.astype(float)


def forecast_area(df: pd.DataFrame, area: str, horizon_days: int = 7) -> AreaForecast:
    """Forecasts daily complaint counts for one area over the next `horizon_days`."""
    daily = _daily_series(df, area)
    if len(daily) < MIN_DAYS_REQUIRED:
        return AreaForecast(area=area, status="insufficient_data")

    values = daily.values
    try:
        from statsmodels.tsa.holtwinters import Holt

        model = Holt(values, initialization_method="estimated").fit(
            optimized=True, damped_trend=False
        )
        forecast = model.forecast(horizon_days)
    except Exception:
        window = values[-14:] if len(values) >= 14 else values
        x = np.arange(len(window))
        slope, intercept = np.polyfit(x, window, 1)
        future_x = np.arange(len(window), len(window) + horizon_days)
        forecast = np.clip(slope * future_x + intercept, 0, None)

    forecast = np.clip(forecast, 0, None)
    recent_avg = float(values[-7:].mean())
    forecast_avg = float(forecast.mean())
    pct_change = ((forecast_avg - recent_avg) / recent_avg * 100.0) if recent_avg > 0 else (
        100.0 if forecast_avg > 0 else 0.0
    )

    return AreaForecast(
        area=area,
        status="ok",
        last_7day_avg=round(recent_avg, 1),
        forecast_7day_avg=round(forecast_avg, 1),
        pct_change=round(pct_change, 1),
        daily_forecast=[round(float(x), 1) for x in forecast],
        will_likely_spike=pct_change > 15,
    )


def forecast_all_areas(df: pd.DataFrame, horizon_days: int = 7, top: int = 5) -> list[dict[str, Any]]:
    """Forecasts every area present in the data, sorted by predicted risk (highest first)."""
    if df is None or df.empty or "area" not in df.columns:
        return []
    areas = df["area"].dropna().astype(str).unique()
    results = [forecast_area(df, area, horizon_days) for area in areas]
    ok = [r.to_dict() for r in results if r.status == "ok"]
    ok.sort(key=lambda r: r["pct_change"], reverse=True)
    return ok[:top]

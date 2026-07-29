"""CivicPulse AI - community decision intelligence dashboard.

Run locally:   streamlit run app.py
Deploy:        see deploy.sh / README.md (Cloud Run)

Philosophy: "Not just answers - better decisions."
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import compute_insights, filter_dataframe
from src.data_loader import LoadResult, _coerce_types, load_sample, load_text, load_uploaded_file
from src.gemini_client import MAX_CONVERSATION_QUESTIONS, GeminiClient, GeminiResult
from src.history_store import HistoryStore
from src.i18n import LANGUAGE_NAMES, LANGUAGES
from src.i18n import L as _L
from src.i18n import T as _T
from src.session_store import SessionStore
from src.utils import humanize

# Load .env if present (local dev convenience).
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

APP_DIR = Path(__file__).parent
SAMPLE_CSV = APP_DIR / "sample_data" / "citizen_complaints.csv"
# Fixed +5:30 offset rather than zoneinfo("Asia/Kolkata") -- IST has no DST,
# so this is exact, and it sidesteps python:3.12-slim not shipping the IANA
# tzdata the stdlib zoneinfo module needs (a real footgun on Cloud Run).
IST = timezone(timedelta(hours=5, minutes=30))
SCHEDULED_BRIEF_FUNCTION_URL = os.environ.get("SCHEDULED_BRIEF_FUNCTION_URL", "")
REALTIME_ALERT_FUNCTION_URL = os.environ.get("REALTIME_ALERT_FUNCTION_URL", "")

st.set_page_config(
    page_title="CivicPulse AI",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------- theme
# Two full palettes: "dark" is the futuristic neon/glass makeover, "light" is
# a clean professional theme (deliberately close to the pre-makeover look).
# Every color the CSS/charts need lives here so switching themes is just
# picking a different dict -- no separate stylesheet to keep in sync.
THEMES: dict[str, dict[str, str | list[str]]] = {
    "dark": {
        "void": "#05060f", "void2": "#0a0e20", "void3": "#131a3a",
        "panel": "rgba(13, 18, 38, 0.55)", "panel_solid": "#0c1024",
        "border": "rgba(0, 245, 255, 0.28)",
        "cyan": "#00f5ff", "violet": "#a742ff", "magenta": "#ff2fd0",
        "green": "#22c55e", "amber": "#f59e0b", "red": "#ef4444",
        "text": "#e8f6ff", "text_dim": "#90a4c4",
        "orb1": "rgba(0,245,255,0.20)", "orb2": "rgba(167,66,255,0.18)", "orb3": "rgba(255,47,208,0.15)",
        "grid_line": "rgba(0,245,255,0.06)",
        "hero_bg": "linear-gradient(135deg, rgba(0,245,255,0.10), rgba(167,66,255,0.10) 45%, rgba(255,47,208,0.08) 100%)",
        "hero_blur": "blur(18px) saturate(160%)",
        "hero_border": "1px solid rgba(0,245,255,0.28)",
        "hero_shadow": "0 0 40px rgba(0,245,255,0.12), 0 20px 50px rgba(0,0,0,0.5), inset 0 0 30px rgba(0,245,255,0.04)",
        "hero_text_bg": "linear-gradient(90deg, #00f5ff, #a742ff, #ff2fd0, #00f5ff)",
        "hero_text_shadow": "drop-shadow(0 0 20px rgba(0,245,255,.35))",
        "hero_emoji_shadow": "drop-shadow(0 0 12px rgba(0,245,255,.5))",
        "badge_bg": "rgba(0,245,255,.08)", "badge_border": "rgba(0,245,255,.4)", "badge_fg": "#00f5ff",
        "badge_bg_hover": "rgba(0,245,255,.18)", "badge_shadow_hover": "rgba(0,245,255,.4)",
        "val_shadow": "0 0 14px rgba(0,245,255,.35)",
        "section_shadow": "drop-shadow(0 0 6px rgba(0,245,255,.3))",
        "card_hover_shadow": "0 0 26px rgba(0,245,255,.30), 0 12px 34px rgba(0,0,0,.5)",
        "sheen": "rgba(0,245,255,.10)",
        "btn_bg": "linear-gradient(135deg, rgba(0,245,255,.14), rgba(167,66,255,.14))",
        "btn_shadow": "0 0 14px rgba(0,245,255,.15)", "btn_shadow_hover": "0 0 24px rgba(0,245,255,.5)",
        "btn_primary_bg": "linear-gradient(135deg, #00f5ff, #a742ff)", "btn_primary_fg": "#05060f",
        "btn_primary_shadow": "0 0 22px rgba(0,245,255,.45)", "btn_primary_shadow_hover": "0 0 34px rgba(0,245,255,.7)",
        "uploader_btn_bg": "rgba(0,245,255,.10)",
        "input_border": "rgba(0,245,255,.25)", "input_focus": "0 0 0 2px rgba(0,245,255,.25)",
        "expander_border": "rgba(0,245,255,.18)", "expander_shadow": "0 0 18px rgba(0,245,255,.15)",
        "alert_border": "rgba(0,245,255,.2)",
        "tab_border": "rgba(0,245,255,.15)", "tab_hover_bg": "rgba(0,245,255,0.08)",
        "tab_active_bg": "rgba(0,245,255,0.10)", "tab_text_shadow": "0 0 10px rgba(0,245,255,.5)",
        "chat_user_bg": "rgba(167,66,255,0.08)", "chat_user_border": "rgba(167,66,255,.3)",
        "chat_ai_bg": "rgba(0,245,255,0.05)", "chat_ai_border": "rgba(0,245,255,.28)",
        "chat_hover_shadow": "0 0 20px rgba(0,245,255,.18)",
        "sidebar_bg": "linear-gradient(180deg, #0a0e20 0%, #05060f 100%)", "sidebar_border": "rgba(0,245,255,.18)",
        "df_border": "rgba(0,245,255,.2)",
        "selection_bg": "rgba(0,245,255,.3)", "selection_fg": "#05060f",
        "map_style": "carto-darkmatter",
        "chart_paper": "rgba(13,18,38,0.35)",
        "axis_grid": "rgba(0,245,255,0.10)", "axis_zero": "rgba(0,245,255,0.18)",
        "bar_scale": ["#1a1f3a", "#00f5ff"],
        "area_line": "#00f5ff", "area_fill": "rgba(0,245,255,0.15)", "area_marker": "#a742ff",
        "pie_sequence": ["#00f5ff", "#a742ff", "#ff2fd0", "#39ff88", "#ffb84d", "#ff3860"],
        "pie_line": "#05060f",
        "geo_real": "#00f5ff", "geo_provided": "#a742ff", "geo_placeholder": "#ffb84d",
        "legend_bg": "rgba(13,18,38,0.7)",
        "font_display": "'Orbitron', sans-serif",
        "font_body": "'Rajdhani', sans-serif",
        "font_mono": "'Share Tech Mono', monospace",
        "ui_transform": "uppercase",
    },
    "light": {
        "void": "#f4f7fc", "void2": "#eaf1fa", "void3": "#eaf3fb",
        "panel": "rgba(255, 255, 255, 0.82)", "panel_solid": "#ffffff",
        "border": "rgba(14, 116, 144, 0.22)",
        "cyan": "#0e7490", "violet": "#1d4ed8", "magenta": "#be185d",
        "green": "#22c55e", "amber": "#f59e0b", "red": "#ef4444",
        "text": "#101828", "text_dim": "#475467",
        "orb1": "rgba(14,116,144,0.10)", "orb2": "rgba(29,78,216,0.09)", "orb3": "rgba(190,24,93,0.07)",
        "grid_line": "rgba(15,23,42,0.035)",
        "hero_bg": "linear-gradient(120deg, #0f766e 0%, #0e7490 45%, #1d4ed8 100%)",
        "hero_blur": "none",
        "hero_border": "none",
        "hero_shadow": "0 10px 30px rgba(13,110,110,0.22)",
        "hero_text_bg": "linear-gradient(90deg, #ffffff, #ffffff)",
        "hero_text_shadow": "none",
        "hero_emoji_shadow": "none",
        "badge_bg": "rgba(255,255,255,.18)", "badge_border": "rgba(255,255,255,.35)", "badge_fg": "#ffffff",
        "badge_bg_hover": "rgba(255,255,255,.30)", "badge_shadow_hover": "rgba(16,24,40,.18)",
        "val_shadow": "none",
        "section_shadow": "none",
        "card_hover_shadow": "0 10px 24px rgba(16,24,40,.12)",
        "sheen": "rgba(14,116,144,.08)",
        "btn_bg": "linear-gradient(135deg, rgba(14,116,144,.10), rgba(29,78,216,.08))",
        "btn_shadow": "0 2px 8px rgba(16,24,40,.08)", "btn_shadow_hover": "0 6px 18px rgba(16,24,40,.14)",
        "btn_primary_bg": "#0e7490", "btn_primary_fg": "#ffffff",
        "btn_primary_shadow": "0 4px 14px rgba(16,24,40,.18)", "btn_primary_shadow_hover": "0 8px 22px rgba(16,24,40,.24)",
        "uploader_btn_bg": "rgba(14,116,144,.08)",
        "input_border": "rgba(14,116,144,.22)", "input_focus": "0 0 0 2px rgba(14,116,144,.20)",
        "expander_border": "rgba(14,116,144,.18)", "expander_shadow": "0 4px 14px rgba(16,24,40,.08)",
        "alert_border": "rgba(14,116,144,.18)",
        "tab_border": "rgba(14,116,144,.18)", "tab_hover_bg": "rgba(14,116,144,.06)",
        "tab_active_bg": "rgba(14,116,144,.08)", "tab_text_shadow": "none",
        "chat_user_bg": "rgba(29,78,216,0.06)", "chat_user_border": "rgba(29,78,216,.22)",
        "chat_ai_bg": "rgba(14,116,144,0.05)", "chat_ai_border": "rgba(14,116,144,.20)",
        "chat_hover_shadow": "0 4px 14px rgba(16,24,40,.10)",
        "sidebar_bg": "linear-gradient(180deg, #ffffff 0%, #eef2f7 100%)", "sidebar_border": "rgba(14,116,144,.15)",
        "df_border": "rgba(14,116,144,.18)",
        "selection_bg": "rgba(14,116,144,.25)", "selection_fg": "#ffffff",
        "map_style": "carto-positron",
        "chart_paper": "rgba(255,255,255,0.6)",
        "axis_grid": "rgba(15,23,42,0.08)", "axis_zero": "rgba(15,23,42,0.15)",
        "bar_scale": ["#dbeafe", "#0e7490"],
        "area_line": "#0e7490", "area_fill": "rgba(14,116,144,0.12)", "area_marker": "#1d4ed8",
        "pie_sequence": ["#0e7490", "#1d4ed8", "#be185d", "#16a34a", "#d97706", "#334155"],
        "pie_line": "#ffffff",
        "geo_real": "#0e7490", "geo_provided": "#1d4ed8", "geo_placeholder": "#d97706",
        "legend_bg": "rgba(255,255,255,0.85)",
        "font_display": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        "font_body": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        "font_mono": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        "ui_transform": "none",
    },
}

theme: str = st.session_state.get("theme_mode", "dark")
t = THEMES[theme]

# ---------------------------------------------------------------- language
# UI chrome is pre-translated (src/i18n.py) and swapped by key -- no runtime
# translation calls. T() is for CivicPulse's own static text; L() is for
# categorical values that come from the uploaded dataset (area/category/
# severity/status/department), translated only for display -- the
# underlying dataframe stays untouched so analytics/filtering/Gemini's tool
# calls keep working on the original values. Numbers are never touched.
st.session_state.setdefault("lang", "en")
LANG: str = st.session_state.lang


def T(key: str, **kwargs) -> str:
    return _T(LANG, key, **kwargs)


def L(value):
    return _L(LANG, value)


def get_chart_layout(theme_name: str) -> dict:
    """Plotly layout so charts sit on the app background instead of clashing
    with default white chart chrome, in whichever theme is active."""
    ct = THEMES[theme_name]
    return dict(
        paper_bgcolor=ct["chart_paper"],
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Rajdhani, sans-serif", color=ct["text"], size=13),
        title_font=dict(family="Orbitron, sans-serif", color=ct["text"], size=15),
        legend=dict(font=dict(color=ct["text_dim"]), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor=ct["axis_grid"], zerolinecolor=ct["axis_zero"], color=ct["text_dim"]),
        yaxis=dict(gridcolor=ct["axis_grid"], zerolinecolor=ct["axis_zero"], color=ct["text_dim"]),
    )


CHART_LAYOUT = get_chart_layout(theme)

# ---------------------------------------------------------------- styling
CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;800;900&family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&display=swap');

    :root {
        --cp-void: @@void@@;
        --cp-void2: @@void2@@;
        --cp-void3: @@void3@@;
        --cp-panel: @@panel@@;
        --cp-panel-solid: @@panel_solid@@;
        --cp-border: @@border@@;
        --cp-cyan: @@cyan@@;
        --cp-violet: @@violet@@;
        --cp-magenta: @@magenta@@;
        --cp-green: @@green@@;
        --cp-amber: @@amber@@;
        --cp-red: @@red@@;
        --cp-text: @@text@@;
        --cp-text-dim: @@text_dim@@;
        --cp-orb1: @@orb1@@;
        --cp-orb2: @@orb2@@;
        --cp-orb3: @@orb3@@;
        --cp-grid-line: @@grid_line@@;
        --cp-hero-bg: @@hero_bg@@;
        --cp-hero-blur: @@hero_blur@@;
        --cp-hero-border: @@hero_border@@;
        --cp-hero-shadow: @@hero_shadow@@;
        --cp-hero-text-bg: @@hero_text_bg@@;
        --cp-hero-text-shadow: @@hero_text_shadow@@;
        --cp-hero-emoji-shadow: @@hero_emoji_shadow@@;
        --cp-badge-bg: @@badge_bg@@;
        --cp-badge-border: @@badge_border@@;
        --cp-badge-fg: @@badge_fg@@;
        --cp-badge-bg-hover: @@badge_bg_hover@@;
        --cp-badge-shadow-hover: @@badge_shadow_hover@@;
        --cp-val-shadow: @@val_shadow@@;
        --cp-section-shadow: @@section_shadow@@;
        --cp-card-hover-shadow: @@card_hover_shadow@@;
        --cp-sheen: @@sheen@@;
        --cp-btn-bg: @@btn_bg@@;
        --cp-btn-shadow: @@btn_shadow@@;
        --cp-btn-shadow-hover: @@btn_shadow_hover@@;
        --cp-btn-primary-bg: @@btn_primary_bg@@;
        --cp-btn-primary-fg: @@btn_primary_fg@@;
        --cp-btn-primary-shadow: @@btn_primary_shadow@@;
        --cp-btn-primary-shadow-hover: @@btn_primary_shadow_hover@@;
        --cp-uploader-btn-bg: @@uploader_btn_bg@@;
        --cp-input-border: @@input_border@@;
        --cp-input-focus: @@input_focus@@;
        --cp-expander-border: @@expander_border@@;
        --cp-expander-shadow: @@expander_shadow@@;
        --cp-alert-border: @@alert_border@@;
        --cp-tab-border: @@tab_border@@;
        --cp-tab-hover-bg: @@tab_hover_bg@@;
        --cp-tab-active-bg: @@tab_active_bg@@;
        --cp-tab-text-shadow: @@tab_text_shadow@@;
        --cp-chat-user-bg: @@chat_user_bg@@;
        --cp-chat-user-border: @@chat_user_border@@;
        --cp-chat-ai-bg: @@chat_ai_bg@@;
        --cp-chat-ai-border: @@chat_ai_border@@;
        --cp-chat-hover-shadow: @@chat_hover_shadow@@;
        --cp-sidebar-bg: @@sidebar_bg@@;
        --cp-sidebar-border: @@sidebar_border@@;
        --cp-df-border: @@df_border@@;
        --cp-selection-bg: @@selection_bg@@;
        --cp-selection-fg: @@selection_fg@@;
        --cp-ease: cubic-bezier(0.22, 1, 0.36, 1);
        --font-display: @@font_display@@;
        --font-body: @@font_body@@;
        --font-mono: @@font_mono@@;
        --cp-ui-transform: @@ui_transform@@;
    }

    @keyframes cpFadeUp {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes cpFadeIn {
        from { opacity: 0; }
        to   { opacity: 1; }
    }
    @keyframes cpGradientDrift {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes cpPulse {
        0%, 100% { opacity: 1; }
        50%      { opacity: .55; }
    }
    @keyframes cpSheen {
        from { background-position: -150% -150%; }
        to   { background-position: 150% 150%; }
    }
    html, body { background: var(--cp-void) !important; }

    /* ---- Animated background: drifting neon orbs + tech grid ----
       Painted as .stApp's own background (not a position:fixed pseudo-
       element) so ordinary content simply paints on top in normal
       document flow -- position:relative alone does NOT contain fixed-
       position descendants (only transform/filter/perspective do), so a
       fixed ::before here would escape .stApp's stacking context and can
       end up rendered above real content regardless of z-index. */
    .stApp {
        background-color: var(--cp-void) !important;
        background-image:
            radial-gradient(circle at 20% 25%, var(--cp-orb1) 0%, transparent 30%),
            radial-gradient(circle at 80% 18%, var(--cp-orb2) 0%, transparent 32%),
            radial-gradient(circle at 55% 82%, var(--cp-orb3) 0%, transparent 34%),
            repeating-linear-gradient(0deg, var(--cp-grid-line) 0px, var(--cp-grid-line) 1px, transparent 1px, transparent 56px),
            repeating-linear-gradient(90deg, var(--cp-grid-line) 0px, var(--cp-grid-line) 1px, transparent 1px, transparent 56px),
            radial-gradient(ellipse at 50% -10%, var(--cp-void3) 0%, var(--cp-void2) 45%, var(--cp-void) 100%) !important;
        background-attachment: fixed !important;
        animation: cpBgDrift 26s ease-in-out infinite;
    }
    @keyframes cpBgDrift {
        0%   { background-position: 0% 0%, 0% 0%, 0% 0%, 0px 0px, 0px 0px, 0 0; }
        50%  { background-position: 6% 8%, -7% -5%, 5% -6%, 0px 28px, 28px 0px, 0 0; }
        100% { background-position: 0% 0%, 0% 0%, 0% 0%, 0px 0px, 0px 0px, 0 0; }
    }
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }

    /* ---- Global typography ---- */
    html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, span, div, label,
    input, textarea, select, .stSelectbox, .stTextInput, .stTextArea {
        font-family: var(--font-body) !important;
        color: var(--cp-text);
    }
    h1, h2, h3, h4, h5, h6, .cp-hero h1, .cp-section-title, .stTabs [data-baseweb="tab"] p,
    [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4 {
        font-family: var(--font-display) !important;
        letter-spacing: .02em;
        color: var(--cp-text) !important;
    }
    button, .stButton > button, .stDownloadButton > button {
        font-family: var(--font-display) !important;
        letter-spacing: .04em;
    }
    code, .cp-card .val, .cp-pill .val, .cp-conf-value, [data-testid="stMetricValue"] {
        font-family: var(--font-mono) !important;
    }
    /* Streamlit's own chevron/collapse icons (sidebar collapse, expander
       arrows, etc.) are Material Symbols ligatures -- e.g. the text
       "keyboard_arrow_right" is substituted for an arrow glyph BY that
       specific icon font. The global font-family override above breaks
       that substitution, so the raw ligature name shows as literal text.
       Restore the icon font here so it wins (higher-specificity attribute
       selector, not just a bare tag). */
    [data-testid="stIconMaterial"], span[data-testid="stIconMaterial"],
    .material-symbols-rounded, [class*="material-symbols"], [class*="material-icons"] {
        font-family: 'Material Symbols Rounded', 'Material Icons' !important;
        color: var(--cp-cyan) !important;
    }

    /* ---- Hero ----
       Text color is a fixed near-white regardless of theme: the dark theme's
       hero is a translucent glass panel over the dark void (already reads as
       white), and the light theme's hero is an opaque solid banner (like the
       pre-makeover design), which also needs white text -- so this never
       needs to track the page's flipped --cp-text value. */
    .cp-hero {
        background: var(--cp-hero-bg);
        backdrop-filter: var(--cp-hero-blur);
        -webkit-backdrop-filter: var(--cp-hero-blur);
        border: var(--cp-hero-border);
        color: #f5f9ff; padding: 1.6rem 1.8rem; border-radius: 18px; margin-bottom: 1.2rem;
        box-shadow: var(--cp-hero-shadow);
        animation: cpFadeUp .6s var(--cp-ease) both;
        position: relative; overflow: hidden;
    }
    .cp-hero h1 { margin: 0; font-size: 2.2rem; font-weight: 900; letter-spacing: .03em; color: #f5f9ff; }
    .cp-hero-emoji { filter: var(--cp-hero-emoji-shadow); }
    .cp-hero-text {
        background: var(--cp-hero-text-bg);
        background-size: 300% auto;
        -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
        animation: cpGradientDrift 7s linear infinite;
        filter: var(--cp-hero-text-shadow);
    }
    .cp-hero p { margin: .5rem 0 0; opacity: .92; font-size: 1.02rem; color: #f5f9ff; font-weight: 500; }
    .cp-badge {
        display:inline-block; background: var(--cp-badge-bg); border:1px solid var(--cp-badge-border);
        color: var(--cp-badge-fg); padding: 3px 12px; border-radius: 999px; font-size:.72rem;
        font-family: var(--font-mono); letter-spacing: .06em; text-transform: var(--cp-ui-transform);
        margin-right:6px; margin-top:.6rem;
        transition: background .2s var(--cp-ease), transform .2s var(--cp-ease), box-shadow .2s var(--cp-ease);
    }
    .cp-badge:hover { background: var(--cp-badge-bg-hover); transform: translateY(-2px); box-shadow: 0 0 14px var(--cp-badge-shadow-hover); }

    /* ---- Cards (glassmorphic) ---- */
    .cp-card {
        background: var(--cp-panel);
        backdrop-filter: blur(16px) saturate(160%); -webkit-backdrop-filter: blur(16px) saturate(160%);
        border: 1px solid var(--cp-border); border-radius: 16px;
        padding: 1.05rem 1.2rem; height: 100%;
        box-shadow: 0 8px 32px rgba(0,0,0,0.45);
        animation: cpFadeUp .45s var(--cp-ease) both;
        transition: transform .25s var(--cp-ease), box-shadow .25s var(--cp-ease), border-color .25s var(--cp-ease);
        position: relative; overflow: hidden;
    }
    .cp-card::before {
        content: ""; position: absolute; inset: 0;
        background: linear-gradient(120deg, transparent 30%, var(--cp-sheen) 50%, transparent 70%);
        background-size: 250% 250%; background-position: -150% -150%; opacity: 0;
    }
    .cp-card:hover {
        transform: translateY(-5px);
        border-color: var(--cp-cyan);
        box-shadow: var(--cp-card-hover-shadow);
    }
    .cp-card:hover::before { opacity: 1; animation: cpSheen 1.1s ease; }
    div[data-testid="column"]:nth-of-type(1) .cp-card { animation-delay: .00s; }
    div[data-testid="column"]:nth-of-type(2) .cp-card { animation-delay: .06s; }
    div[data-testid="column"]:nth-of-type(3) .cp-card { animation-delay: .12s; }
    div[data-testid="column"]:nth-of-type(4) .cp-card { animation-delay: .18s; }

    .cp-card .lbl {
        font-family: var(--font-mono); font-size:.68rem; text-transform:uppercase; letter-spacing:.14em;
        color: var(--cp-cyan); margin:0; opacity: .85;
    }
    .cp-card .val { font-size:1.4rem; font-weight:700; color: var(--cp-text); margin:.2rem 0 0; text-shadow: var(--cp-val-shadow); }
    .cp-card .sub { font-size:.8rem; color: var(--cp-text-dim); margin:.25rem 0 0; }

    /* ---- Decision scoreboard pills ---- */
    .cp-pill {
        border-radius:14px; padding:1rem 1rem; text-align:center;
        background: var(--cp-panel) !important;
        backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
        animation: cpFadeUp .45s var(--cp-ease) both;
        transition: transform .22s var(--cp-ease), box-shadow .22s var(--cp-ease);
        position: relative;
    }
    .cp-pill:hover { transform: translateY(-4px) scale(1.02); }
    .cp-pill .cp-pill-label { font-family: var(--font-mono); letter-spacing: .1em; text-transform: var(--cp-ui-transform); }
    .cp-pill .cp-pill-value { font-family: var(--font-display); }
    div[data-testid="column"]:nth-of-type(1) .cp-pill { animation-delay: .00s; }
    div[data-testid="column"]:nth-of-type(2) .cp-pill { animation-delay: .06s; }
    div[data-testid="column"]:nth-of-type(3) .cp-pill { animation-delay: .12s; }
    div[data-testid="column"]:nth-of-type(4) .cp-pill { animation-delay: .18s; }

    .cp-section-title {
        font-weight:700; font-size:1.1rem; margin:.3rem 0 .7rem; color: var(--cp-text);
        animation: cpFadeIn .4s var(--cp-ease) both;
        padding-left: .7rem; border-left: 3px solid var(--cp-cyan);
        text-transform: var(--cp-ui-transform); letter-spacing: .06em;
        filter: var(--cp-section-shadow);
    }

    /* ---- Tabs ---- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px; border-bottom: 1px solid var(--cp-tab-border) !important;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px; border-radius: 10px 10px 0 0;
        background: rgba(255,255,255,.02);
        transition: color .2s var(--cp-ease), background-color .2s var(--cp-ease), box-shadow .2s var(--cp-ease);
        text-transform: var(--cp-ui-transform); font-size: .85rem; letter-spacing: .05em;
    }
    .stTabs [data-baseweb="tab"] p { color: var(--cp-text-dim) !important; }
    .stTabs [data-baseweb="tab"]:hover { background: var(--cp-tab-hover-bg); }
    .stTabs [aria-selected="true"] { background: var(--cp-tab-active-bg); box-shadow: inset 0 -2px 0 var(--cp-cyan); }
    .stTabs [aria-selected="true"] p { color: var(--cp-cyan) !important; text-shadow: var(--cp-tab-text-shadow); }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: var(--cp-cyan) !important; height: 3px !important;
        box-shadow: 0 0 10px var(--cp-cyan), 0 0 20px var(--cp-cyan);
        transition: left .25s var(--cp-ease), width .25s var(--cp-ease);
    }
    .stTabs [data-baseweb="tab-panel"] { animation: cpFadeIn .35s var(--cp-ease) both; }

    /* ---- Buttons ---- */
    .stButton > button, .stDownloadButton > button {
        background: var(--cp-btn-bg) !important;
        border: 1px solid var(--cp-cyan) !important;
        color: var(--cp-text) !important;
        border-radius: 10px !important;
        text-transform: var(--cp-ui-transform); font-size: .82rem !important;
        transition: transform .15s var(--cp-ease), box-shadow .15s var(--cp-ease), filter .15s var(--cp-ease);
        box-shadow: var(--cp-btn-shadow);
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--cp-btn-shadow-hover);
        border-color: var(--cp-cyan) !important;
    }
    .stButton > button:active, .stDownloadButton > button:active { transform: translateY(0) scale(.98); }
    .stButton > button[kind="primary"] {
        background: var(--cp-btn-primary-bg) !important;
        color: var(--cp-btn-primary-fg) !important; font-weight: 700 !important; border: none !important;
        box-shadow: var(--cp-btn-primary-shadow);
    }
    .stButton > button[kind="primary"]:hover { box-shadow: var(--cp-btn-primary-shadow-hover); }

    /* ---- Inputs, selects, file uploader ---- */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div,
    [data-testid="stChatInput"] textarea, [data-testid="stFileUploaderDropzone"] {
        background: var(--cp-panel-solid) !important;
        border: 1px solid var(--cp-input-border) !important;
        color: var(--cp-text) !important;
        caret-color: var(--cp-cyan) !important;
        border-radius: 10px !important;
    }
    /* [data-testid="stChatInput"] is its OWN wrapper around the textarea, not
       just a container -- it carries its own opaque white background
       (unrelated to the textarea's), which peeked through at the rounded
       corners since only the inner textarea was styled above. Typed text
       itself was never actually black; the white sliver around it just made
       everything read as washed out / hard to see against the dark page. */
    [data-testid="stChatInput"] {
        background: var(--cp-panel-solid) !important;
        border-radius: 10px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus, [data-testid="stChatInput"] textarea:focus {
        border-color: var(--cp-cyan) !important;
        box-shadow: var(--cp-input-focus) !important;
    }
    [data-testid="stFileUploaderDropzone"] { border-style: dashed !important; }
    [data-testid="stFileUploaderDropzone"] button {
        background: var(--cp-uploader-btn-bg) !important; border: 1px solid var(--cp-cyan) !important; color: var(--cp-text) !important;
    }
    /* Selectbox's OPEN dropdown list is rendered by BaseWeb in a portal
       appended to <body>, outside .stApp -- it still picks up the global
       `div, span { color: var(--cp-text) }` rule above (those selectors
       aren't scoped to .stApp), but keeps BaseWeb's own default WHITE
       background since nothing here targeted it, so option text went
       near-invisible (light text on white) in dark theme. Style the portal
       explicitly so it matches the current theme regardless of where in the
       DOM it's mounted. */
    div[data-baseweb="popover"], div[data-baseweb="popover"] ul {
        background: var(--cp-panel-solid) !important;
        border: 1px solid var(--cp-input-border) !important;
    }
    li[role="option"] {
        background: var(--cp-panel-solid) !important;
        color: var(--cp-text) !important;
    }
    li[role="option"]:hover, li[aria-selected="true"] {
        background: var(--cp-tab-active-bg) !important;
        color: var(--cp-cyan) !important;
    }
    /* The "⋮" main menu (Rerun/Settings/Print/...) is a separate, non-
       BaseWeb popover with its own wrapper divs -- same class of bug as
       above (an unstyled ancestor carrying a hardcoded light background
       that the dark theme never reached), different component. */
    .stMainMenuPopover {
        background: var(--cp-panel-solid) !important;
        border: 1px solid var(--cp-input-border) !important;
    }
    /* Defensive, not just reactive: any nested wrapper div inside these
       three containers that ISN'T explicitly styled above falls back to
       transparent instead of whatever default (often light) background
       Streamlit gave it -- so a hover/open/disabled sub-state introducing
       a new, unstyled wrapper can't reintroduce this bug. Safe because it
       has no !important: every element with an intentional background
       (the option/tab rules above, .cp-* components elsewhere) already
       wins via !important regardless of source order. */
    .stMainMenuPopover *, [data-testid="stExpander"] *, [data-testid="stChatInput"] * {
        background-color: transparent;
    }

    /* ---- Expanders, containers, alerts ---- */
    div[data-testid="stExpander"] {
        background: var(--cp-panel) !important; backdrop-filter: blur(12px);
        border: 1px solid var(--cp-expander-border) !important; border-radius: 12px !important;
        transition: box-shadow .2s var(--cp-ease), border-color .2s var(--cp-ease);
    }
    div[data-testid="stExpander"]:hover { box-shadow: var(--cp-expander-shadow); border-color: var(--cp-cyan) !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        animation: cpFadeIn .35s var(--cp-ease) both;
    }
    div[data-testid="stAlert"] {
        background: var(--cp-panel) !important; backdrop-filter: blur(12px);
        border: 1px solid var(--cp-alert-border); border-radius: 12px;
        animation: cpFadeUp .35s var(--cp-ease) both;
    }

    /* ---- Spinner ---- */
    div[data-testid="stSpinner"] { animation: cpPulse 1.6s ease-in-out infinite; }
    div[data-testid="stSpinner"] svg { filter: drop-shadow(0 0 6px var(--cp-cyan)); }
    div[data-testid="stSpinner"] p { color: var(--cp-cyan) !important; font-family: var(--font-mono) !important; }

    /* ---- Confidence badge ---- */
    .cp-confidence {
        display: inline-flex; flex-direction: column; align-items: flex-start;
        border-radius: 10px; padding: .5rem 1.1rem; margin: .3rem 0 .7rem;
        background: var(--cp-panel) !important; backdrop-filter: blur(12px);
        animation: cpFadeUp .35s var(--cp-ease) both;
        transition: transform .2s var(--cp-ease), box-shadow .2s var(--cp-ease);
    }
    .cp-confidence:hover { transform: translateY(-2px); }
    .cp-confidence .cp-conf-label {
        font-family: var(--font-mono); font-size: .64rem; text-transform: uppercase; letter-spacing: .12em; opacity: .8;
    }
    .cp-confidence .cp-conf-value { font-family: var(--font-display); font-size: 1.05rem; font-weight: 800; margin-top: .1rem; }
    .cp-conf-high   { border: 1px solid var(--cp-green); box-shadow: 0 0 18px rgba(34,197,94,.35); }
    .cp-conf-high .cp-conf-value   { color: var(--cp-green); text-shadow: 0 0 10px rgba(34,197,94,.6); }
    .cp-conf-medium { border: 1px solid var(--cp-amber); box-shadow: 0 0 18px rgba(245,158,11,.35); }
    .cp-conf-medium .cp-conf-value { color: var(--cp-amber); text-shadow: 0 0 10px rgba(245,158,11,.6); }
    .cp-conf-low    { border: 1px solid var(--cp-red); box-shadow: 0 0 18px rgba(239,68,68,.35); }
    .cp-conf-low .cp-conf-value    { color: var(--cp-red); text-shadow: 0 0 10px rgba(239,68,68,.6); }

    /* ---- Chat (Ask AI) ---- */
    [data-testid="stChatMessage"] {
        border-radius: 16px; margin-bottom: .6rem; padding: .4rem .3rem;
        backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
        animation: cpFadeUp .3s var(--cp-ease) both;
        transition: box-shadow .2s var(--cp-ease);
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        background: var(--cp-chat-user-bg); border: 1px solid var(--cp-chat-user-border);
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]),
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarCustom"]) {
        background: var(--cp-chat-ai-bg); border: 1px solid var(--cp-chat-ai-border);
    }
    [data-testid="stChatMessage"]:hover { box-shadow: var(--cp-chat-hover-shadow); }

    /* ---- Message meta row (sender + timestamp) ---- */
    .cp-msg-meta {
        display:flex; justify-content:space-between; align-items:baseline;
        font-family: var(--font-mono); font-size:.7rem; color: var(--cp-text-dim);
        margin-bottom:.35rem; letter-spacing:.02em;
    }
    .cp-msg-sender { font-weight:600; color: var(--cp-text); font-family: var(--font-body); }

    /* ---- Confidence progress bar ---- */
    .cp-conf-row { display:flex; align-items:center; gap:.4rem; }
    .cp-conf-track {
        width:100%; height:6px; border-radius:999px;
        background: rgba(120,130,140,.22); margin-top:.5rem; overflow:hidden;
    }
    .cp-conf-fill { height:100%; border-radius:999px; transition: width .4s var(--cp-ease); }

    /* ---- Small status/utility cards (sidebar, trust card) ---- */
    .cp-status-card {
        display:flex; align-items:center; gap:.6rem;
        padding:.6rem .8rem; border-radius:12px;
        background: var(--cp-panel); border:1px solid var(--cp-border);
        font-size:.82rem; margin:.4rem 0;
    }
    .cp-status-card .icon { font-size:1.05rem; }
    .cp-status-off { opacity:.65; }
    .cp-trust-card {
        display:flex; gap:.7rem; align-items:flex-start;
        padding:.9rem 1rem; border-radius:14px;
        background: var(--cp-panel); border:1px solid var(--cp-border);
        font-size:.8rem; color: var(--cp-text-dim); margin-top:.8rem;
    }
    .cp-trust-card .icon { font-size:1.3rem; line-height:1; }
    .cp-trust-card b { color: var(--cp-text); }

    /* ---- Chat history panel entries (Ask AI, right column) ---- */
    .cp-history-item {
        padding:.55rem .7rem; border-radius:10px;
        background: var(--cp-panel); border:1px solid var(--cp-border);
        margin-bottom:.5rem; font-size:.8rem;
        transition: border-color .2s var(--cp-ease);
    }
    .cp-history-item:hover { border-color: var(--cp-cyan); }
    .cp-history-time {
        font-family: var(--font-mono); font-size:.66rem; color: var(--cp-cyan);
        display:block; margin-bottom:.2rem; letter-spacing:.03em;
    }

    /* ---- Sidebar ---- */
    [data-testid="stSidebar"] {
        background: var(--cp-sidebar-bg) !important;
        border-right: 1px solid var(--cp-sidebar-border);
    }
    /* Streamlit sizes each stVerticalBlock as a flex item with flex-basis:0,
       relying on flex-grow to fill the remaining width. Kannada/Hindi text
       has far more line-break opportunities than English (no long
       unbreakable "words"), so its intrinsic min-content width can shrink
       to near zero -- and without an explicit flex-grow, native
       st.caption()/st.markdown() text blocks were collapsing to a ~60px
       sliver and wrapping one grapheme per line instead of using the
       available width. Applies app-wide (sidebar AND main content both use
       plain st.caption/markdown calls in Kannada/Hindi), excluding blocks
       inside an actual st.columns() row so their intentional proportions
       (like the theme switch) aren't overridden. */
    [data-testid="stVerticalBlock"]:not([data-testid="stHorizontalBlock"] [data-testid="stVerticalBlock"]) {
        flex-grow: 1 !important;
        min-width: 0 !important;
    }
    [data-testid="stSidebar"] * { color: var(--cp-text) !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 { font-family: var(--font-display) !important; }

    /* ---- Top header bar (the "⋮" menu / Deploy button strip) ----
       header[data-testid="stHeader"] carries its own hardcoded light
       background (rgb(247,249,252)) completely independent of app theme --
       it's Streamlit's own chrome, not part of .stApp -- so it stayed a
       bright white bar even in dark theme, and the menu button's icon
       (correctly light-colored already) went low-contrast against it. */
    header[data-testid="stHeader"], div[data-testid="stToolbar"] {
        background: var(--cp-void) !important;
    }
    [data-testid="stToolbarActions"] button, [data-testid="stMainMenu"] button {
        background: transparent !important;
        color: var(--cp-text) !important;
    }
    [data-testid="stToolbarActions"] button svg, [data-testid="stMainMenu"] button svg {
        fill: var(--cp-text) !important;
    }
    [data-testid="stToolbarActions"] button:hover, [data-testid="stMainMenu"] button:hover {
        background: var(--cp-tab-hover-bg) !important;
    }

    /* ---- Dataframe ---- */
    [data-testid="stDataFrame"] { border: 1px solid var(--cp-df-border); border-radius: 10px; overflow: hidden; }

    /* ---- Misc polish ---- */
    ::selection { background: var(--cp-selection-bg); color: var(--cp-selection-fg); }
    [data-testid="stMain"] { scroll-behavior: smooth; }
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(var(--cp-cyan), var(--cp-violet)); border-radius: 999px;
    }
    ::-webkit-scrollbar-thumb:hover { background: linear-gradient(var(--cp-violet), var(--cp-magenta)); }

    @media (prefers-reduced-motion: reduce) {
        .stApp, .cp-hero, .cp-hero h1, .cp-card, .cp-pill, .cp-section-title, .stTabs [data-baseweb="tab-panel"],
        div[data-testid="stVerticalBlockBorderWrapper"], div[data-testid="stAlert"], div[data-testid="stSpinner"],
        .cp-confidence, [data-testid="stChatMessage"] {
            animation: none !important;
        }
    }
</style>
"""
# Token-replace (not str.format/f-string) because the CSS body is full of
# literal `{`/`}` (keyframes, selectors) that would need constant escaping --
# `@@token@@` markers can't collide with real CSS syntax, so this stays safe
# no matter how the stylesheet above grows.
for _k, _v in t.items():
    CSS = CSS.replace(f"@@{_k}@@", str(_v))
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- state
def _init_state() -> None:
    st.session_state.setdefault("load_result", None)
    st.session_state.setdefault("insights", None)
    st.session_state.setdefault("brief", None)
    st.session_state.setdefault("qa_history", [])
    st.session_state.setdefault("qa_conversation", None)
    st.session_state.setdefault("domain", "citizen complaints")
    st.session_state.setdefault("trigger_result", None)
    st.session_state.setdefault("ocr_text", None)
    st.session_state.setdefault("ocr_brief", None)


_init_state()


@st.cache_resource(show_spinner=False)
def get_gemini() -> GeminiClient:
    return GeminiClient()


@st.cache_resource(show_spinner=False)
def get_history() -> HistoryStore:
    return HistoryStore()


@st.cache_resource(show_spinner=False)
def get_session_store() -> SessionStore:
    return SessionStore()


gemini = get_gemini()
history = get_history()
session_store = get_session_store()


# ---------------------------------------------------------------- session persistence
# st.session_state lives only in server memory for one browser session -- a
# page reload opens a fresh one, wiping it. A session id kept in the URL's
# query params DOES survive a reload, so it's what ties a reloaded page back
# to whatever was last saved to Firestore for that id. See src/session_store.py.
def _get_session_id() -> str:
    sid = st.query_params.get("sid")
    if not sid:
        sid = uuid.uuid4().hex[:16]
        st.query_params["sid"] = sid
    return sid


SESSION_ID = _get_session_id()


def _result_to_dict(result: GeminiResult) -> dict:
    return {
        "ok": result.ok,
        "data": result.data,
        "raw_text": result.raw_text,
        "used_fallback": result.used_fallback,
        "model": result.model,
        "error": result.error,
    }


def _dict_to_result(d: dict) -> GeminiResult:
    return GeminiResult(
        ok=d.get("ok", True),
        data=d.get("data") or {},
        raw_text=d.get("raw_text") or "",
        used_fallback=d.get("used_fallback", False),
        model=d.get("model") or "",
        error=d.get("error"),
    )


def _persist_session() -> None:
    """Best-effort save of the current session so a reload can restore it.
    Call after any state change worth surviving a reload (new data loaded,
    a Q&A turn answered, a brief generated). Silently a no-op if Firestore
    isn't reachable or the dataset is too large to persist -- never blocks
    or errors on the live session over it."""
    lr = st.session_state.load_result
    session_store.save(
        SESSION_ID,
        df=lr.df if lr is not None else None,
        source_type=lr.source_type if lr is not None else None,
        raw_text=lr.raw_text if lr is not None else None,
        domain=st.session_state.domain,
        qa_history=[(q, _result_to_dict(r), ts) for q, r, ts in st.session_state.qa_history],
        brief=_result_to_dict(st.session_state.brief) if st.session_state.brief is not None else None,
    )


def _rehydrate_session() -> None:
    """Once per browser session (guarded so a normal rerun doesn't hit
    Firestore every time), try to restore a previously saved dataset and
    chat history for this session id after a page reload."""
    if st.session_state.get("_rehydrate_attempted"):
        return
    st.session_state._rehydrate_attempted = True
    if st.session_state.load_result is not None:
        return
    restored = session_store.load(SESSION_ID)
    if not restored:
        return

    df = restored.get("df")
    if df is not None and not df.empty:
        # A CSV round-trip loses dtypes (dates/strings come back as plain
        # object columns) -- re-run the same coercion the original upload
        # went through so analytics.py's .dt accessor calls keep working.
        df = _coerce_types(df)
    st.session_state.load_result = LoadResult(
        df=df if df is not None else pd.DataFrame(),
        source_type=restored.get("source_type") or "csv",
        raw_text=restored.get("raw_text"),
    )
    st.session_state.domain = restored.get("domain") or st.session_state.domain
    st.session_state.insights = compute_insights(df) if df is not None and not df.empty else None

    st.session_state.qa_history = [
        (turn.get("question", ""), _dict_to_result(turn.get("result") or {}), turn.get("time", ""))
        for turn in restored.get("qa_history") or []
    ]
    # The Gemini SDK conversation object holds live google.genai types, not
    # plain data, so it can't be restored across a reload -- a follow-up
    # question after a reload just starts a fresh tool-calling conversation
    # instead of literally continuing the old one. The restored Q&A history
    # above still displays normally either way.
    st.session_state.qa_conversation = None

    brief_dict = restored.get("brief")
    st.session_state.brief = _dict_to_result(brief_dict) if brief_dict else None


_rehydrate_session()


def _set_data(load_result: LoadResult) -> None:
    st.session_state.load_result = load_result
    st.session_state.brief = None  # invalidate cached brief on new data
    st.session_state.qa_history = []
    st.session_state.qa_conversation = None
    if load_result.df is not None and not load_result.df.empty:
        st.session_state.insights = compute_insights(load_result.df)
    else:
        st.session_state.insights = None
    _persist_session()


# ---------------------------------------------------------------- sidebar
DOMAIN_OPTIONS = [
    "citizen complaints", "waste & sanitation", "water supply",
    "road & infrastructure", "public health access", "neighborhood wellness",
]
_DOMAIN_KEYS = {
    "citizen complaints": "domain_citizen_complaints",
    "waste & sanitation": "domain_waste_sanitation",
    "water supply": "domain_water_supply",
    "road & infrastructure": "domain_road_infra",
    "public health access": "domain_public_health",
    "neighborhood wellness": "domain_neighborhood_wellness",
}

with st.sidebar:
    st.markdown("### 🏙️ CivicPulse AI")
    st.caption(T("sidebar_tagline"))
    _theme_opts = ["dark", "light"]
    st.radio(
        "Theme", _theme_opts, horizontal=True,
        format_func=lambda v: T("theme_dark") if v == "dark" else T("theme_light"),
        label_visibility="collapsed", key="theme_mode",
        # Pin the displayed selection to the backend value on every render --
        # without this, switching language mid-session changes this radio's
        # option LABELS (via format_func/T()), and Streamlit's frontend
        # widget loses track of which option is selected and visually
        # snaps back to the first one ("Dark") even though session_state
        # still holds "light" for this run. The next rerun then reads that
        # now-wrong frontend selection back as if the user had picked
        # "Dark" -- so a language change silently flips the theme.
        index=_theme_opts.index(st.session_state.get("theme_mode", "dark")),
    )
    st.selectbox(
        T("language_label"), list(LANGUAGES.keys()), format_func=lambda code: LANGUAGES[code],
        key="lang", label_visibility="collapsed",
    )
    st.divider()

    st.markdown(f"#### {T('ocr_section_title')}")
    st.caption(T("ocr_section_caption"))
    ocr_file = st.file_uploader(
        T("ocr_upload_label"), type=["jpg", "jpeg", "png", "pdf"], key="ocr_upload",
        label_visibility="collapsed",
    )
    if ocr_file is not None and st.button(T("ocr_scan_btn"), key="ocr_scan_btn", type="primary", use_container_width=True):
        with st.spinner(T("ocr_extracting_spinner")):
            mime = ocr_file.type or "image/jpeg"
            ocr_result = gemini.ocr_extract_text(ocr_file.getvalue(), mime)
        if not ocr_result.ok:
            st.session_state.ocr_text = None
            st.session_state.ocr_brief = None
            st.error(T("ocr_failed", err=ocr_result.error or "—"))
        else:
            st.session_state.ocr_text = ocr_result.data["text"]
            with st.spinner(T("drafting_spinner")):
                st.session_state.ocr_brief = gemini.summarize_text(
                    st.session_state.ocr_text, st.session_state.domain, lang=LANGUAGE_NAMES[LANG],
                )
            st.success(T("ocr_scan_done_hint"))
    st.divider()

    st.markdown(f"#### {T('sidebar_load_data_heading')}")
    if st.button(T("load_demo_dataset_btn"), use_container_width=True, type="primary"):
        if SAMPLE_CSV.exists():
            _set_data(load_sample(str(SAMPLE_CSV)))
            st.success(T("demo_dataset_loaded"))
        else:
            st.error(T("sample_file_missing"))

    uploaded = st.file_uploader(
        T("upload_file_label"), type=["csv", "json", "pdf", "xlsx", "xls"], accept_multiple_files=False
    )
    if uploaded is not None:
        if st.button(T("analyze_uploaded_file_btn"), use_container_width=True):
            _set_data(load_uploaded_file(uploaded))
            st.success(T("loaded_file_msg", name=uploaded.name))

    with st.expander(T("paste_text_expander")):
        pasted = st.text_area(T("paste_text_placeholder"), height=120, label_visibility="collapsed")
        if st.button(T("analyze_pasted_text_btn"), use_container_width=True) and pasted.strip():
            _set_data(load_text(pasted))
            st.success(T("text_captured"))

    _lr = st.session_state.load_result
    if _lr is not None and getattr(_lr, "column_matches", None):
        with st.expander(T("detected_columns_expander")):
            for m in _lr.column_matches:
                icon = {"exact": "✅", "token": "🟢", "fuzzy": "🟡", "content": "🔵"}.get(m.method, "⚪")
                label = T("value_based") if m.method == "content" else T("pct_match", score=f"{m.score:.0%}")
                st.caption(f"{icon} **{m.source_column}** → `{m.canonical}` ({label})")

    st.markdown(f"#### {T('domain_framing_heading')}")
    st.session_state.domain = st.selectbox(
        "Domain", DOMAIN_OPTIONS, format_func=lambda v: T(_DOMAIN_KEYS[v]), label_visibility="collapsed",
    )

    st.markdown(f"#### {T('ai_status_heading')}")
    if gemini.available:
        st.success(gemini.status_message)
    else:
        st.warning(T("gemini_offline_warning"))
        st.caption(gemini.status_message)

    st.divider()
    st.caption(T("sidebar_footer"))


# ---------------------------------------------------------------- hero
st.markdown(
    f"""
    <div class="cp-hero">
        <h1><span class="cp-hero-emoji">🏙️</span> <span class="cp-hero-text">CivicPulse AI</span></h1>
        <p>{T('hero_tagline')}
        <b>{T('hero_tagline_bold')}</b></p>
        <span class="cp-badge">{T('badge_nlp')}</span>
        <span class="cp-badge">{T('badge_anomaly')}</span>
        <span class="cp-badge">{T('badge_action')}</span>
        <span class="cp-badge">{T('badge_gemini')}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

load_result: LoadResult | None = st.session_state.load_result
insights = st.session_state.insights

if load_result is None:
    st.info(T("empty_state_info"))
    c1, c2, c3 = st.columns(3)
    for col, (title_key, body_key) in zip(
        (c1, c2, c3),
        [
            ("feature_card_1_title", "feature_card_1_body"),
            ("feature_card_2_title", "feature_card_2_body"),
            ("feature_card_3_title", "feature_card_3_body"),
        ],
    ):
        with col:
            st.markdown(
                f"<div class='cp-card'><p class='val'>{T(title_key)}</p><p class='sub'>{T(body_key)}</p></div>",
                unsafe_allow_html=True,
            )
    st.stop()


# ---------------------------------------------------------------- helpers for rendering
def score_pill(label: str, value: float, color: str) -> str:
    return (
        f"<div class='cp-pill' style='border:1px solid {color};box-shadow:0 0 20px {color}59,inset 0 0 16px {color}14'>"
        f"<div class='cp-pill-label' style='font-size:.68rem;letter-spacing:.12em;opacity:.85;color:{color}'>{label}</div>"
        f"<div class='cp-pill-value' style='font-size:1.7rem;font-weight:800;color:{color};text-shadow:0 0 14px {color}99'>{value:.0f}</div>"
        f"<div style='font-size:.66rem;opacity:.7;font-family:var(--font-mono)'>/ 100</div></div>"
    )


def urgency_color(v: float) -> str:
    if v >= 70:
        return "#ef4444"
    if v >= 45:
        return "#f59e0b"
    return "#22c55e"


def confidence_badge(confidence: str | None) -> str:
    level = str(confidence or "").strip().lower()
    css_class = {"high": "cp-conf-high", "medium": "cp-conf-medium", "low": "cp-conf-low"}.get(
        level, "cp-conf-medium"
    )
    label = T(f"conf_{level}") if level in ("high", "medium", "low") else "—"
    return (
        f"<div class='cp-confidence {css_class}'>"
        f"<span class='cp-conf-label'>{T('confidence_label')}</span>"
        f"<span class='cp-conf-value'>{label}</span>"
        f"</div>"
    )


_CONF_COLOR_HEX = {"high": "#22c55e", "medium": "#f59e0b", "low": "#ef4444"}


def agentic_confidence_pct(trace: list[dict] | None) -> int:
    """Deterministic 0-100 confidence for one Ask AI answer, computed from
    the REAL tool-call results it's grounded in -- not an LLM self-report.
    Two real signals, same "compute first, explain second" philosophy as
    the rest of the app:
      - sample size (0-70): the strongest evidence any successful call
        provided. filter_records/get_top_complaints report an explicit
        record_count (saturating at 40 matching records; a confirmed zero
        still counts as real, if thin, evidence rather than scoring like an
        outright error). get_summary_stats has no record_count at all --
        it's a full-dataset snapshot (same numbers as the Overview tab), so
        its absence means "comprehensive", not "no evidence", and it scores
        at full sample credit.
      - reliability (0-30): the fraction of tool calls that succeeded
        without error (a partly-failed evidence base is less trustworthy)
    """
    trace = trace or []
    if not trace:
        return 35  # no tool calls at all (e.g. offline fallback) -- low, not zero
    calls = len(trace)
    errors = sum(1 for t in trace if t.get("error"))
    successes = calls - errors

    sample_scores = []
    for t in trace:
        if t.get("error"):
            continue
        if "record_count" in t:
            n = t.get("record_count") or 0
            sample_scores.append(25.0 if n == 0 else min(n / 40.0, 1.0) * 70.0)
        else:
            sample_scores.append(70.0)  # e.g. get_summary_stats: whole-dataset evidence

    sample_score = max(sample_scores) if sample_scores else 0.0
    reliability_score = (successes / calls) * 30.0
    return round(min(100.0, sample_score + reliability_score))


def confidence_bar(pct: int) -> str:
    if pct >= 75:
        label, color = T("conf_high"), _CONF_COLOR_HEX["high"]
    elif pct >= 45:
        label, color = T("conf_medium"), _CONF_COLOR_HEX["medium"]
    else:
        label, color = T("conf_low"), _CONF_COLOR_HEX["low"]
    return (
        f"<div class='cp-confidence'>"
        f"<div class='cp-conf-row'><span class='icon'>🛡️</span>"
        f"<span class='cp-conf-label'>{T('confidence_label')}</span>"
        f"<span class='cp-conf-value' style='color:{color}'>{label} · {pct}%</span></div>"
        f"<div class='cp-conf-track'><div class='cp-conf-fill' style='width:{pct}%;background:{color}'></div></div>"
        f"</div>"
    )


def render_qa_answer(result) -> None:
    """Shared renderer for one Ask AI answer -- used both for the freshly
    answered turn and for replaying prior turns in the chat history."""
    data = result.data
    if result.used_fallback:
        st.caption(T("offline_fallback_caption"))

    if "what_is_happening" in data:
        conf_pct = agentic_confidence_pct(data.get("_tool_trace"))
        st.markdown(confidence_bar(conf_pct), unsafe_allow_html=True)
        if data.get("explanation"):
            st.markdown(data["explanation"])
            st.write("")
        st.markdown(f"📊 **{T('field_whats_happening')}** {data.get('what_is_happening', '')}")
        st.markdown(f"🔷 **{T('field_why_it_matters')}** {data.get('why_it_matters', '')}")

        where = data.get("where")
        if isinstance(where, list) and where:
            where_str = "&nbsp;&nbsp;".join(f"{i}. {w}" for i, w in enumerate(where, 1))
        elif isinstance(where, str) and where.strip():
            where_str = where
        else:
            where_str = T("not_enough_data")
        st.markdown(f"📍 **{T('field_where')}** {where_str}", unsafe_allow_html=True)

        st.markdown(f"🎯 **{T('field_recommended_next_step')}** {data.get('recommended_next_step', '')}")
        st.info(f"🗣️ {data.get('executive_summary', '')}")
    else:
        st.write(data.get("summary", data))

    trace = data.get("_tool_trace")
    if trace:
        n = len(trace)
        with st.expander(T("tool_trace_expander", n=n, y="y" if n == 1 else "ies")):
            st.caption(T("tool_trace_caption"))
            for t in trace:
                args_str = ", ".join(f"{k}={v}" for k, v in (t.get("args") or {}).items()) or "—"
                if t.get("error"):
                    st.caption(f"❌ `{t['tool']}({args_str})` → {t['error']}")
                elif "record_count" in t:
                    rc = t.get("record_count")
                    st.caption(f"✅ `{t['tool']}({args_str})` → {T('tool_trace_matching_records', rc=rc, s='s' if rc != 1 else '')}")
                else:
                    st.caption(f"✅ `{t['tool']}({args_str})` → {T('tool_trace_full_snapshot')}")


_URGENCY_ICON = {"immediate": "🔴", "high": "🟠", "normal": "⚪"}

# Maps an anomaly's raw `dimension` (from analytics._detect_anomalies) to the
# i18n key for a plain-language sentence explaining what that KIND of spike
# generally implies -- deterministic and translated, not a per-anomaly Gemini
# call, matching the "compute/explain locally first" pattern used everywhere
# else in this app.
_ANOMALY_MEANING_KEYS = {
    "area": "anomaly_meaning_area",
    "category": "anomaly_meaning_category",
    "complaint type": "anomaly_meaning_complaint_type",
    "time": "anomaly_meaning_time",
}
_ANOMALY_DIM_LABEL_KEYS = {
    "area": "dim_area", "category": "dim_category", "time": "dim_time", "complaint type": "dim_complaint_type",
}


def _brief_to_markdown(data: dict) -> str:
    lines = [f"# {data.get('title', T('memo_default_title'))}", ""]
    if data.get("dataset_overview"):
        lines.append(f"## {T('dataset_overview_heading').replace('📖 ', '')}")
        lines.append(data["dataset_overview"])
        lines.append("")
    lines.append(f"_{data.get('summary', '')}_\n")
    if data.get("key_findings"):
        lines.append(f"## {T('key_findings_heading')}")
        lines += [f"- {f}" for f in data["key_findings"]]
        lines.append("")
    patterns = data.get("peculiar_patterns") or data.get("anomalies")
    if patterns:
        lines.append(f"## {T('peculiar_patterns_heading').replace('🔎 ', '')}")
        lines += [f"- {a}" for a in patterns]
        lines.append("")
    if data.get("recommended_actions"):
        lines.append(f"## {T('recommended_actions_heading')}")
        for i, act in enumerate(data["recommended_actions"], 1):
            if isinstance(act, dict):
                urgency = str(act.get("urgency", "")).lower()
                icon = _URGENCY_ICON.get(urgency, "")
                urgency_label = T(f"urgency_{urgency}") if urgency in ("immediate", "high", "normal") else urgency
                lines.append(
                    T(
                        "memo_action_line", i=i, icon=icon, action=act.get('action', ''),
                        owner=act.get('owner', '—'), timeframe=act.get('timeframe', '—'),
                        urgency_part=T("memo_urgency_part", u=urgency_label) if urgency else "",
                    )
                )
            else:
                lines.append(f"{i}. {act}")
        lines.append("")
    if data.get("explanation"):
        lines.append(f"## {T('why_this_recommendation')}")
        lines.append(data["explanation"])
        lines.append("")
    conf = str(data.get('confidence', '')).lower()
    conf_label = T(f"conf_{conf}") if conf in ("high", "medium", "low") else "—"
    lines.append(f"**{T('confidence_heading')}:** {conf_label}")
    lines.append(f"\n---\n_{T('memo_generated_by')}_")
    return "\n".join(lines)


def render_actions(actions: list) -> None:
    for i, act in enumerate(actions or [], 1):
        if isinstance(act, dict):
            owner = act.get("owner", "—")
            tf = act.get("timeframe", "—")
            urgency = str(act.get("urgency", "")).lower()
            icon = _URGENCY_ICON.get(urgency, "")
            st.markdown(f"**{i}. {icon} {act.get('action', '')}**")
            caption = T("action_owner_timeframe", owner=owner, tf=tf)
            if urgency:
                urgency_label = T(f"urgency_{urgency}") if urgency in ("immediate", "high", "normal") else urgency
                caption += T("action_urgency_suffix", u=urgency_label)
            st.caption(caption)
        else:
            st.markdown(f"**{i}.** {act}")


def trigger_scheduled_reports(url: str) -> dict:
    """Invoke the deployed civicpulse-scheduled-brief Cloud Function directly
    from the app, using the Cloud Run service account's identity -- the same
    trigger Cloud Scheduler fires every Monday, just on demand. Returns a
    dict with either the function's real JSON response or an "error" key;
    never raises, so a demo click can't crash the app.

    Note: the function pulls its own dataset (the bundled sample, or
    CIVICPULSE_DATA_GCS_URI if configured) -- independent of whatever file is
    loaded in this browser session.
    """
    if not url:
        return {"error": "SCHEDULED_BRIEF_FUNCTION_URL is not configured for this deployment."}
    try:
        import google.auth.transport.requests
        import google.oauth2.id_token
        import requests

        auth_req = google.auth.transport.requests.Request()
        id_token = google.oauth2.id_token.fetch_id_token(auth_req, url)
        resp = requests.post(
            url, headers={"Authorization": f"Bearer {id_token}"}, timeout=280
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # noqa: BLE001 - surface as a message, not a crash
        return {"error": str(exc)}


def _immediate_actions(data: dict) -> list[dict]:
    return [
        a for a in (data.get("recommended_actions") or [])
        if isinstance(a, dict) and str(a.get("urgency", "")).lower() == "immediate"
    ]


def _build_alert_email(data: dict, domain: str) -> tuple[str, str]:
    """Compose a short, urgent-only email from a brief's immediate-urgency
    action(s) -- deliberately narrower than the full weekly digest
    (_brief_to_email_body in main.py) since this fires the moment something
    needs a same-day response, not on a schedule."""
    title = data.get("title") or "Community Alert"
    subject = f"🚨 CivicPulse AI Real-Time Alert — {title}"
    lines = [f"Domain: {domain}", ""]
    if data.get("summary"):
        lines += [data["summary"], ""]
    lines.append("Action(s) needed TODAY:")
    for a in _immediate_actions(data):
        lines.append(
            f"- {a.get('action', '')} (owner: {a.get('owner', '—')}, timeframe: {a.get('timeframe', '—')})"
        )
    if data.get("explanation"):
        lines += ["", "Why:", data["explanation"]]
    lines += ["", "-- Sent on demand from CivicPulse AI (Recommendations tab)."]
    return subject, "\n".join(lines)


def trigger_realtime_alert(url: str, subject: str, body: str) -> dict:
    """Same authenticated-invoke pattern as trigger_scheduled_reports, but
    posts one ad-hoc alert (subject/body built from THIS session's live
    brief) to a separate, lighter Cloud Function instead of re-running the
    full citywide+department pipeline -- a demo click fires in a couple
    seconds, not the ~minute the full weekly job takes."""
    if not url:
        return {"error": "REALTIME_ALERT_FUNCTION_URL is not configured for this deployment."}
    try:
        import google.auth.transport.requests
        import google.oauth2.id_token
        import requests

        auth_req = google.auth.transport.requests.Request()
        id_token = google.oauth2.id_token.fetch_id_token(auth_req, url)
        resp = requests.post(
            url, headers={"Authorization": f"Bearer {id_token}"},
            json={"subject": subject, "body": body}, timeout=60,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # noqa: BLE001 - surface as a message, not a crash
        return {"error": str(exc)}


def _render_brief_block(brief, key_prefix: str) -> None:
    """Shared renderer for one generated brief -- used for both the
    dataset-wide Executive Brief and the OCR-derived single-form summary, so
    the two features (recommendations + real-time alert) don't need two
    parallel implementations. `key_prefix` keeps Streamlit widget keys
    (download button, alert button, cached alert result) unique when both
    briefs are rendered on the same page."""
    data = brief.data
    if brief.used_fallback:
        st.warning(T("brief_fallback_warning"))

    st.markdown(f"## 📝 {data.get('title', T('brief_default_title'))}")

    if data.get("dataset_overview"):
        st.markdown(f"#### {T('dataset_overview_heading')}")
        st.markdown(data["dataset_overview"])
        st.write("")

    st.markdown(f"> {data.get('summary', '')}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"#### {T('key_findings_heading')}")
        for f in data.get("key_findings", []):
            st.markdown(f"- {f}")
        patterns = data.get("peculiar_patterns") or data.get("anomalies")
        if patterns:
            st.markdown(f"#### {T('peculiar_patterns_heading')}")
            for a in patterns:
                st.markdown(f"- {a}")
    with col2:
        st.markdown(f"#### {T('recommended_actions_heading')}")
        st.caption(T("urgency_legend"))
        render_actions(data.get("recommended_actions", []))
        st.markdown(f"#### {T('confidence_heading')}")
        st.markdown(confidence_badge(data.get("confidence")), unsafe_allow_html=True)

    if data.get("explanation"):
        with st.expander(T("explainability_expander")):
            st.write(data["explanation"])

    memo = _brief_to_markdown(data)
    st.download_button(
        T("download_memo_btn"), memo, file_name="civicpulse_action_memo.md",
        mime="text/markdown", key=f"{key_prefix}_download_memo",
    )

    urgent = _immediate_actions(data)
    if urgent:
        st.write("")
        if not REALTIME_ALERT_FUNCTION_URL:
            st.warning(T("realtime_alert_needs_config", n=len(urgent)))
        elif st.button(T("send_realtime_alert_btn", n=len(urgent)), key=f"{key_prefix}_alert_btn", type="primary"):
            subject, body = _build_alert_email(data, st.session_state.domain)
            with st.spinner(T("realtime_alert_sending")):
                st.session_state[f"{key_prefix}_alert_result"] = trigger_realtime_alert(
                    REALTIME_ALERT_FUNCTION_URL, subject, body,
                )
        alert_result = st.session_state.get(f"{key_prefix}_alert_result")
        if alert_result:
            if alert_result.get("error"):
                st.error(T("realtime_alert_failed", err=alert_result["error"]))
            else:
                st.success(T("realtime_alert_sent", status=alert_result.get("email_status", "—")))


# ---------------------------------------------------------------- tabs
tab_overview, tab_ask, tab_anom, tab_reco, tab_about = st.tabs(
    [T("tab_overview"), T("tab_ask_ai"), T("tab_anomalies"), T("tab_recommendations"), T("tab_about")]
)


# ============================== OVERVIEW ==============================
with tab_overview:
    if insights is None:
        st.warning(T("unstructured_warning"))
    else:
        d = insights.to_dict()
        scores = d["scores"]

        st.markdown(f"<div class='cp-section-title'>{T('community_snapshot')}</div>", unsafe_allow_html=True)
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(
                f"<div class='cp-card'><p class='lbl'>{T('card_records')}</p><p class='val'>{d['total_records']}</p>"
                f"<p class='sub'>{d['date_range'].get('start','?')} → {d['date_range'].get('end','?')}</p></div>",
                unsafe_allow_html=True,
            )
        with k2:
            st.markdown(
                f"<div class='cp-card'><p class='lbl'>{T('card_top_hotspot')}</p><p class='val'>{L(humanize(d['hotspot_area'] or 'n/a'))}</p>"
                f"<p class='sub'>{T('card_most_affected')}</p></div>",
                unsafe_allow_html=True,
            )
        with k3:
            st.markdown(
                f"<div class='cp-card'><p class='lbl'>{T('card_leading_issue')}</p><p class='val'>{L(humanize(d['top_category'] or 'n/a'))}</p>"
                f"<p class='sub'>{T('card_top_category')}</p></div>",
                unsafe_allow_html=True,
            )
        with k4:
            arrow = {"rising": "▲", "falling": "▼", "flat": "▬"}[d["trend_direction"]]
            trend_label = T(f"trend_{d['trend_direction']}")
            trend_pct_str = f"{d['trend_change_pct']:+.1f}%"
            st.markdown(
                f"<div class='cp-card'><p class='lbl'>{T('card_weekly_trend')}</p><p class='val'>{arrow} {trend_label}</p>"
                f"<p class='sub'>{T('vs_prior_week', pct=trend_pct_str)}</p></div>",
                unsafe_allow_html=True,
            )

        st.write("")
        st.markdown(f"<div class='cp-section-title'>{T('decision_scoreboard')}</div>", unsafe_allow_html=True)
        s1, s2, s3, s4 = st.columns(4)
        s1.markdown(score_pill(T("pill_urgency"), scores["urgency"], urgency_color(scores["urgency"])), unsafe_allow_html=True)
        s2.markdown(score_pill(T("pill_impact"), scores["impact"], t["cyan"]), unsafe_allow_html=True)
        s3.markdown(score_pill(T("pill_confidence"), scores["confidence"], t["violet"]), unsafe_allow_html=True)
        s4.markdown(score_pill(T("pill_severity"), scores["severity_index"], t["magenta"]), unsafe_allow_html=True)
        st.caption(T("open_case_rate", pct=d["open_rate_pct"]))
        cb = scores.get("confidence_breakdown")
        if cb:
            with st.expander(T("why_confidence_expander")):
                st.caption(
                    T(
                        "confidence_breakdown_caption",
                        n=f"{cb['sample_size_score']:.0f}", r=f"{cb['recency_score']:.0f}", s=f"{cb['stability_score']:.0f}",
                    )
                )

        st.write("")
        map_title_col, map_toggle_col = st.columns([4, 1.4])
        with map_title_col:
            st.markdown(f"<div class='cp-section-title'>{T('hotspot_map_title')}</div>", unsafe_allow_html=True)
            st.caption(T("hotspot_map_caption"))
        if d.get("geo_summary"):
            geo_df = pd.DataFrame(d["geo_summary"])
            _coord_labels = {
                "real_ward": T("coord_real_ward"), "provided": T("coord_provided"), "placeholder": T("coord_placeholder"),
            }
            geo_df["coord_label"] = geo_df["coord_source"].map(_coord_labels)
            # A plain Streamlit control instead of Plotly's own in-chart
            # updatemenus buttons -- those used to sit top-right on the map
            # and collided with Plotly's built-in modebar (camera/pan/zoom/
            # fullscreen icons), which also lives top-right and can't be
            # moved. A separate widget above the chart can never overlap it.
            # Stored as a stable "dark"/"light" key (not translated text) so
            # the basemap-selection logic below never depends on which
            # language's label happens to be showing.
            _basemap_opts = ["dark", "light"]
            with map_toggle_col:
                st.radio(
                    "Basemap", _basemap_opts, horizontal=True,
                    format_func=lambda v: T("theme_dark") if v == "dark" else T("theme_light"),
                    label_visibility="collapsed", key="map_basemap",
                    # See the theme_mode radio above for why this is needed:
                    # translated option labels desync the frontend widget's
                    # displayed selection on a language change otherwise.
                    index=_basemap_opts.index(st.session_state.get("map_basemap", theme)),
                )
            mapbox_style = "carto-darkmatter" if st.session_state.map_basemap == "dark" else "carto-positron"
            map_is_dark = mapbox_style == "carto-darkmatter"

            fig_map = px.scatter_mapbox(
                geo_df, lat="lat", lon="lon", size="hotspot_score", color="coord_label",
                hover_name="area",
                hover_data={"total_complaints": True, "open_rate_pct": True, "high_severity_rate_pct": True,
                            "lat": False, "lon": False, "hotspot_score": ":.1f", "coord_label": False},
                color_discrete_map={
                    _coord_labels["real_ward"]: t["geo_real"],
                    _coord_labels["provided"]: t["geo_provided"],
                    _coord_labels["placeholder"]: t["geo_placeholder"],
                },
                size_max=32, zoom=10, mapbox_style=mapbox_style,
            )
            # Auto-fit the view to the actual data instead of a fixed zoom level.
            lat_span = geo_df["lat"].max() - geo_df["lat"].min()
            lon_span = geo_df["lon"].max() - geo_df["lon"].min()
            span = max(lat_span, lon_span, 0.01)
            auto_zoom = 12 if span < 0.05 else (10 if span < 0.15 else (8 if span < 0.5 else 6))
            # Legend styling follows the chosen BASEMAP (not the app theme)
            # so it stays readable against whichever map tiles are showing.
            legend_bg = "rgba(13,18,38,0.7)" if map_is_dark else "rgba(255,255,255,0.85)"
            legend_fg = "#e8f6ff" if map_is_dark else "#101828"
            fig_map.update_layout(
                height=520, margin=dict(l=0, r=0, t=10, b=0), legend_title_text="",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Rajdhani, sans-serif", color=legend_fg),
                legend=dict(
                    bgcolor=legend_bg, font=dict(color=legend_fg),
                    x=0.01, y=0.99, xanchor="left", yanchor="top",
                ),
                mapbox=dict(
                    center=dict(lat=float(geo_df["lat"].mean()), lon=float(geo_df["lon"].mean())),
                    zoom=auto_zoom,
                ),
            )
            st.plotly_chart(
                fig_map, use_container_width=True,
                config={"scrollZoom": True, "displayModeBar": True, "displaylogo": False},
            )
            st.caption(T("map_scroll_caption"))

            n_real = int((geo_df["coord_source"] == "real_ward").sum())
            n_placeholder = int((geo_df["coord_source"] == "placeholder").sum())
            n_total = len(geo_df)
            st.caption(T("map_coord_caption", n_real=n_real, n_total=n_total, n_placeholder=n_placeholder))
        else:
            st.info(T("map_insufficient_data"))

        st.write("")
        st.markdown(f"<div class='cp-section-title'>{T('forecast_title')}</div>", unsafe_allow_html=True)
        st.caption(T("forecast_caption"))
        if d.get("forecasts"):
            fc_df = pd.DataFrame(d["forecasts"])
            for _, row in fc_df.iterrows():
                icon = "🔴" if row["will_likely_spike"] else "🟢"
                fc1, fc2, fc3 = st.columns([2, 2, 1])
                with fc1:
                    st.markdown(f"{icon} **{L(humanize(row['area']))}**")
                with fc2:
                    st.caption(T("forecast_row_detail", last=f"{row['last_7day_avg']:.1f}", forecast=f"{row['forecast_7day_avg']:.1f}"))
                with fc3:
                    st.markdown(f"**{row['pct_change']:+.1f}%**")
        else:
            st.info(T("forecast_insufficient"))

        st.write("")
        df = load_result.df
        c_left, c_right = st.columns(2)
        with c_left:
            if d["by_area"]:
                fig = px.bar(
                    x=list(d["by_area"].values()),
                    y=[L(humanize(a)) for a in d["by_area"].keys()],
                    orientation="h",
                    labels={"x": T("chart_complaints_axis"), "y": ""},
                    title=T("chart_complaints_by_area"),
                    color=list(d["by_area"].values()),
                    color_continuous_scale=t["bar_scale"],
                )
                fig.update_layout(
                    showlegend=False, coloraxis_showscale=False, height=340, margin=dict(l=0, r=0, t=40, b=0),
                    **CHART_LAYOUT,
                )
                fig.update_yaxes(autorange="reversed")
                st.plotly_chart(fig, use_container_width=True)
        with c_right:
            if d["weekly_trend"]:
                tdf = pd.DataFrame(d["weekly_trend"])
                fig2 = px.area(
                    tdf, x="week", y="count", title=T("chart_weekly_trend"), markers=True,
                )
                fig2.update_traces(line_color=t["area_line"], fillcolor=t["area_fill"], marker=dict(color=t["area_marker"], size=7))
                fig2.update_layout(height=340, margin=dict(l=0, r=0, t=40, b=0), **CHART_LAYOUT)
                st.plotly_chart(fig2, use_container_width=True)

        c_a, c_b = st.columns(2)
        with c_a:
            if d["by_category"]:
                fig3 = px.pie(
                    names=[L(humanize(k)) for k in d["by_category"].keys()],
                    values=list(d["by_category"].values()),
                    title=T("chart_category_mix"), hole=0.5,
                    color_discrete_sequence=t["pie_sequence"],
                )
                fig3.update_traces(marker=dict(line=dict(color=t["pie_line"], width=2)))
                fig3.update_layout(height=340, margin=dict(l=0, r=0, t=40, b=0), **CHART_LAYOUT)
                st.plotly_chart(fig3, use_container_width=True)
        with c_b:
            if d["severity_distribution"]:
                order = ["low", "medium", "high", "critical"]
                sd = {k: d["severity_distribution"].get(k, 0) for k in order if k in d["severity_distribution"]}
                sev_colors = {"low": "#22c55e", "medium": "#f59e0b", "high": "#fb923c", "critical": "#ef4444"}
                sev_labels = [L(humanize(k)) for k in sd.keys()]
                fig4 = px.bar(
                    x=sev_labels, y=list(sd.values()),
                    title=T("chart_severity_distribution"), labels={"x": "", "y": T("chart_count_axis")},
                    color=sev_labels,
                    color_discrete_map={L(humanize(k)): v for k, v in sev_colors.items()},
                )
                fig4.update_layout(showlegend=False, height=340, margin=dict(l=0, r=0, t=40, b=0), **CHART_LAYOUT)
                st.plotly_chart(fig4, use_container_width=True)

        with st.expander(T("preview_raw_data")):
            st.dataframe(df.head(50), use_container_width=True)


# ============================== ASK AI ==============================
def _msg_meta(sender: str, ts: str) -> str:
    ts_html = f"<span>{ts}</span>" if ts else ""
    return f"<div class='cp-msg-meta'><span class='cp-msg-sender'>{sender}</span>{ts_html}</div>"


with tab_ask:
    STARTER_SUGGESTIONS = [T("starter_q1"), T("starter_q2"), T("starter_q3"), T("starter_q4")]
    picked = None

    col_suggest, col_chat, col_history = st.columns([1, 2.3, 1])

    # ---- Left: persistent suggested-questions panel -------------------
    with col_suggest:
        st.markdown(f"<div class='cp-section-title'>{T('ask_suggested_questions')}</div>", unsafe_allow_html=True)
        if st.session_state.qa_history:
            last_result = st.session_state.qa_history[-1][1]
            panel_questions = (last_result.data or {}).get("suggested_follow_ups") or []
            panel_questions = [q for q in panel_questions if isinstance(q, str) and q.strip()][:4]
            if not panel_questions:
                panel_questions = STARTER_SUGGESTIONS
        else:
            panel_questions = STARTER_SUGGESTIONS
        for i, s in enumerate(panel_questions):
            if st.button(s, use_container_width=True, key=f"suggest_{len(st.session_state.qa_history)}_{i}"):
                picked = s
        if st.session_state.qa_history:
            st.write("")
            if st.button(T("new_conversation_btn"), use_container_width=True):
                st.session_state.qa_history = []
                st.session_state.qa_conversation = None
                _persist_session()
                st.rerun()

    # ---- Middle: the live conversation ---------------------------------
    with col_chat:
        st.markdown(f"<div class='cp-section-title'>{T('conversation_title')}</div>", unsafe_allow_html=True)
        st.caption(T("ask_ai_caption"))

        # Render the full conversation BEFORE the input box, so the input
        # always ends up visually pinned below every message -- st.chat_input
        # renders inline exactly where it's called when used inside a
        # column/tab (it only auto-floats to the page bottom at the top
        # level), so code order here is what determines its on-screen
        # position.
        for q, result, ts in st.session_state.qa_history:
            with st.chat_message("user"):
                st.markdown(_msg_meta(T("sender_you"), ts), unsafe_allow_html=True)
                st.markdown(q)
            with st.chat_message("assistant", avatar="🏙️"):
                st.markdown(_msg_meta(T("sender_civicpulse"), ts), unsafe_allow_html=True)
                render_qa_answer(result)

        if not st.session_state.qa_history:
            st.caption(T("ask_ai_empty_hint"))

        typed_question = st.chat_input(T("chat_input_placeholder"))
        question = picked or typed_question

        if question and question.strip():
            if insights is not None:
                payload = insights.to_dict()
                # Keep the conversation going for follow-ups, but cap how long
                # one thread can grow before starting fresh (bounds token
                # cost/latency over a long session).
                prior_conv = (
                    st.session_state.qa_conversation
                    if len(st.session_state.qa_history) < MAX_CONVERSATION_QUESTIONS
                    else None
                )
                with st.spinner(T("gemini_querying_spinner")):
                    result, updated_conv = gemini.answer_question_agentic(
                        load_result.df, payload, question, st.session_state.domain,
                        conversation=prior_conv, lang=LANGUAGE_NAMES[LANG],
                    )
                st.session_state.qa_conversation = updated_conv
            else:
                raw = load_result.raw_text or ""
                with st.spinner(T("analyzing_spinner")):
                    result = gemini.summarize_text(raw, st.session_state.domain, lang=LANGUAGE_NAMES[LANG])
            st.session_state.qa_history.append((question, result, datetime.now(IST).strftime("%I:%M %p IST")))
            _persist_session()
            # Rerun so this turn renders through the history loop above (in
            # its natural position above the input) instead of appearing
            # transiently below the already-rendered input box for one frame.
            st.rerun()

    # ---- Right: chat history log + trust card --------------------------
    with col_history:
        st.markdown(f"<div class='cp-section-title'>{T('chat_history_title')}</div>", unsafe_allow_html=True)
        if st.session_state.qa_history:
            for q, _result, ts in reversed(st.session_state.qa_history):
                preview = q if len(q) <= 60 else q[:57] + "…"
                st.markdown(
                    f"<div class='cp-history-item'><span class='cp-history-time'>{ts}</span>{preview}</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption(T("chat_history_empty"))
        st.markdown(
            f"<div class='cp-trust-card'><span class='icon'>🛡️</span>"
            f"<span><b>{T('trust_card_title')}</b><br>"
            f"{T('trust_card_body')}</span></div>",
            unsafe_allow_html=True,
        )


# ============================== ANOMALIES ==============================
with tab_anom:
    st.markdown(f"<div class='cp-section-title'>{T('anomalies_title')}</div>", unsafe_allow_html=True)
    st.caption(T("anomalies_caption"))
    if insights is None:
        st.info(T("anomalies_needs_structured"))
    else:
        anomalies = insights.to_dict()["anomalies"]
        if not anomalies:
            st.success(T("anomalies_none"))
        else:
            for a in anomalies:
                sev = "🔴" if a["score"] >= 2.5 else ("🟠" if a["score"] >= 2.0 else "🟡")
                dim_label = T(_ANOMALY_DIM_LABEL_KEYS.get(a["dimension"], a["dimension"]))
                meaning_key = _ANOMALY_MEANING_KEYS.get(a["dimension"])
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"{sev} **{L(a['label'])}**  ·  _{dim_label}_")
                        # a["detail"] is a deterministically-assembled English
                        # sentence (counts + sigma + the dimension word), not a
                        # simple categorical value or static UI text -- left
                        # untranslated for now rather than partially translating
                        # a sentence built by string interpolation in analytics.py.
                        st.caption(a["detail"])
                        if meaning_key:
                            st.markdown(f"💡 {T(meaning_key)}")
                    with c2:
                        st.metric(T("sigma_score_label"), f"{a['score']:.1f}")


# ============================== RECOMMENDATIONS ==============================
with tab_reco:
    st.markdown(f"<div class='cp-section-title'>{T('brief_title')}</div>", unsafe_allow_html=True)
    st.caption(T("brief_caption"))

    if st.button(T("generate_brief_btn"), type="primary"):
        with st.spinner(T("drafting_spinner")):
            if insights is not None:
                st.session_state.brief = gemini.executive_brief(
                    insights.to_dict(), st.session_state.domain, lang=LANGUAGE_NAMES[LANG],
                )
            else:
                st.session_state.brief = gemini.summarize_text(
                    load_result.raw_text or "", st.session_state.domain, lang=LANGUAGE_NAMES[LANG],
                )
        _fresh_brief = st.session_state.brief
        if _fresh_brief.ok and insights is not None:
            history.save_brief(
                domain=st.session_state.domain,
                source_type=load_result.source_type,
                insights=insights.to_dict(),
                brief_data=_fresh_brief.data,
            )
        _persist_session()

    brief = st.session_state.brief
    if brief is not None:
        _render_brief_block(brief, key_prefix="main")
    else:
        st.info(T("brief_click_hint"))

    if history.available:
        recent = history.list_recent(limit=5)
        if recent:
            st.write("")
            with st.expander(T("recent_briefs_expander", n=len(recent))):
                st.caption(T("recent_briefs_caption"))
                for r in recent:
                    ts = r.get("created_at")
                    ts_str = ts.strftime("%b %d, %Y %H:%M UTC") if hasattr(ts, "strftime") else str(ts or "—")
                    st.markdown(f"**{r.get('brief_title') or T('untitled_brief')}** · {ts_str}")
                    st.caption(
                        T(
                            "brief_record_summary",
                            area=L(humanize(r.get('hotspot_area') or '—')),
                            category=L(humanize(r.get('top_category') or '—')),
                            records=r.get('total_records', '—'),
                            trend=T(f"trend_{r.get('trend_direction')}") if r.get('trend_direction') in ("rising", "falling", "flat") else r.get('trend_direction', '—'),
                        )
                    )
                    st.divider()

    st.write("")
    st.markdown(f"<div class='cp-section-title'>{T('automated_reports_title')}</div>", unsafe_allow_html=True)
    st.caption(T("automated_reports_caption"))
    if not SCHEDULED_BRIEF_FUNCTION_URL:
        st.info(T("scheduled_not_configured"))
    elif st.button(T("send_reports_btn")):
        with st.spinner(T("triggering_spinner")):
            st.session_state.trigger_result = trigger_scheduled_reports(SCHEDULED_BRIEF_FUNCTION_URL)

    trigger_result = st.session_state.get("trigger_result")
    if trigger_result:
        if trigger_result.get("error"):
            st.error(T("trigger_failed", err=trigger_result['error']))
        else:
            fallback_note = T("trigger_fallback_note") if trigger_result.get("gemini_used_fallback") else ""
            st.success(T("trigger_success", status=trigger_result.get('email_status', '—'), note=fallback_note))
            dept_reports = trigger_result.get("department_reports") or {}
            for dept, status in dept_reports.items():
                icon = "✅" if status.startswith("sent") else ("⏭️" if status.startswith("skipped") else "❌")
                st.caption(f"{icon} **{dept}** — {status}")

    if st.session_state.get("ocr_text") or st.session_state.get("ocr_brief") is not None:
        st.write("")
        st.markdown(f"<div class='cp-section-title'>{T('ocr_section_title')}</div>", unsafe_allow_html=True)
        st.caption(T("ocr_section_caption"))
        if st.session_state.get("ocr_text"):
            with st.expander(T("ocr_extracted_text_expander")):
                st.text(st.session_state.ocr_text)
        if st.session_state.get("ocr_brief") is not None:
            _render_brief_block(st.session_state.ocr_brief, key_prefix="ocr")


# ============================== ABOUT ==============================
with tab_about:
    st.markdown(f"<div class='cp-section-title'>{T('about_title')}</div>", unsafe_allow_html=True)
    st.markdown(T("about_intro_md"))
    st.markdown("")
    st.markdown(T("about_features_heading"))
    st.markdown(T("about_features_md"))
    st.markdown("")
    st.markdown(T("about_gcloud_heading"))
    st.markdown(T("about_gcloud_md"))
    st.markdown("")
    st.markdown(T("about_cost_heading"))
    st.markdown(T("about_cost_md"))
    st.markdown("---")
    st.markdown(f"#### {T('about_glossary_heading')}")

    _glossary_rows = [
        ("glossary_sigma_term", "glossary_sigma_meaning"),
        ("glossary_confidence_term", "glossary_confidence_meaning"),
        ("glossary_urgency_term", "glossary_urgency_meaning"),
        ("glossary_impact_term", "glossary_impact_meaning"),
        ("glossary_severity_term", "glossary_severity_meaning"),
        ("glossary_hotspot_term", "glossary_hotspot_meaning"),
    ]
    _glossary_md = f"| {T('glossary_term')} | {T('glossary_meaning')} |\n|---|---|\n"
    _glossary_md += "\n".join(f"| **{T(term_key)}** | {T(meaning_key)} |" for term_key, meaning_key in _glossary_rows)
    st.markdown(_glossary_md)

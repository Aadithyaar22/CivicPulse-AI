"""CivicPulse AI - community decision intelligence dashboard.

Run locally:   streamlit run app.py
Deploy:        see deploy.sh / README.md (Cloud Run)

Philosophy: "Not just answers - better decisions."
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import compute_insights, filter_dataframe
from src.data_loader import LoadResult, _coerce_types, load_sample, load_text, load_uploaded_file
from src.gemini_client import MAX_CONVERSATION_QUESTIONS, GeminiClient, GeminiResult
from src.history_store import HistoryStore
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
SCHEDULED_BRIEF_FUNCTION_URL = os.environ.get("SCHEDULED_BRIEF_FUNCTION_URL", "")

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

st.session_state.setdefault("dark_mode", True)
theme: str = "dark" if st.session_state.dark_mode else "light"
t = THEMES[theme]


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

    /* ---- Map bubble-size legend ---- */
    .cp-size-legend { display:flex; gap:1.3rem; align-items:center; flex-wrap:wrap; margin:.6rem 0 0; }
    .cp-size-legend .item { display:flex; align-items:center; gap:.45rem; font-size:.76rem; color: var(--cp-text-dim); }
    .cp-size-legend .dot { display:inline-block; border-radius:50%; background: var(--cp-cyan); flex:none; }

    /* ---- Sidebar ---- */
    [data-testid="stSidebar"] {
        background: var(--cp-sidebar-bg) !important;
        border-right: 1px solid var(--cp-sidebar-border);
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
with st.sidebar:
    st.markdown("### 🏙️ CivicPulse AI")
    st.caption("Community decision intelligence")
    theme_l, theme_switch, theme_d = st.columns([1, 1, 1])
    with theme_l:
        st.caption("☀️ Light")
    with theme_switch:
        st.toggle("Theme", key="dark_mode", label_visibility="collapsed")
    with theme_d:
        st.caption("🌙 Dark")
    st.divider()

    st.markdown("#### 1. Load data")
    if st.button("⚡ Load demo dataset", use_container_width=True, type="primary"):
        if SAMPLE_CSV.exists():
            _set_data(load_sample(str(SAMPLE_CSV)))
            st.success("Demo dataset loaded.")
        else:
            st.error("Sample file missing. Run sample_data/generate_sample.py.")

    uploaded = st.file_uploader(
        "Upload CSV / JSON / PDF / Excel", type=["csv", "json", "pdf", "xlsx", "xls"], accept_multiple_files=False
    )
    if uploaded is not None:
        if st.button("Analyze uploaded file", use_container_width=True):
            _set_data(load_uploaded_file(uploaded))
            st.success(f"Loaded {uploaded.name}")

    with st.expander("Or paste text / report"):
        pasted = st.text_area("Paste community report text", height=120, label_visibility="collapsed")
        if st.button("Analyze pasted text", use_container_width=True) and pasted.strip():
            _set_data(load_text(pasted))
            st.success("Text captured.")

    _lr = st.session_state.load_result
    if _lr is not None and getattr(_lr, "column_matches", None):
        with st.expander("🔍 Detected columns"):
            for m in _lr.column_matches:
                icon = {"exact": "✅", "token": "🟢", "fuzzy": "🟡", "content": "🔵"}.get(m.method, "⚪")
                label = "value-based" if m.method == "content" else f"{m.score:.0%} match"
                st.caption(f"{icon} **{m.source_column}** → `{m.canonical}` ({label})")

    st.markdown("#### 2. Domain framing")
    st.session_state.domain = st.selectbox(
        "Domain",
        [
            "citizen complaints",
            "waste & sanitation",
            "water supply",
            "road & infrastructure",
            "public health access",
            "neighborhood wellness",
        ],
        label_visibility="collapsed",
    )

    st.markdown("#### 3. AI status")
    if gemini.available:
        st.success(gemini.status_message)
    else:
        st.warning("Gemini offline — using local fallback.")
        st.caption(gemini.status_message)

    st.markdown("#### 4. Brief history")
    if history.available:
        _recent_count = len(history.list_recent(limit=50))
        _count_label = f"{_recent_count}+ briefs available" if _recent_count >= 50 else (
            f"{_recent_count} brief{'s' if _recent_count != 1 else ''} available"
        )
        st.markdown(
            f"<div class='cp-status-card'><span class='icon'>🗄️</span><span>{_count_label}</span></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='cp-status-card cp-status-off'><span class='icon'>🗄️</span>"
            "<span>Unavailable this session — briefs won't be saved</span></div>",
            unsafe_allow_html=True,
        )

    st.markdown("#### 5. Session")
    if session_store.available:
        st.markdown(
            "<div class='cp-status-card'><span class='icon'>🔄</span>"
            "<span>Reload-safe session active</span></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='cp-status-card cp-status-off'><span class='icon'>🔄</span>"
            "<span>Unavailable this session — a refresh will reset your data</span></div>",
            unsafe_allow_html=True,
        )

    st.divider()
    st.caption("Built with Streamlit + Gemini on Google Cloud Run.")


# ---------------------------------------------------------------- hero
st.markdown(
    """
    <div class="cp-hero">
        <h1><span class="cp-hero-emoji">🏙️</span> <span class="cp-hero-text">CivicPulse AI</span></h1>
        <p>Ask your community data anything — get patterns, anomalies, and decisions.
        <b>Not just answers — better decisions.</b></p>
        <span class="cp-badge">Natural-language analytics</span>
        <span class="cp-badge">Anomaly detection</span>
        <span class="cp-badge">Action generator</span>
        <span class="cp-badge">Gemini-powered</span>
    </div>
    """,
    unsafe_allow_html=True,
)

load_result: LoadResult | None = st.session_state.load_result
insights = st.session_state.insights

if load_result is None:
    st.info(
        "👈 Start by clicking **Load demo dataset** in the sidebar, or upload your own "
        "CSV/JSON/PDF. CivicPulse turns raw community data into a decision-ready snapshot."
    )
    c1, c2, c3 = st.columns(3)
    for col, (title, body) in zip(
        (c1, c2, c3),
        [
            ("📊 Deterministic first", "Python computes counts, trends & anomalies before any AI call — cheap and reliable."),
            ("🤖 Gemini explains", "A small, low-cost Gemini model turns numbers into plain-language decisions."),
            ("🎯 Decision Scoreboard", "Urgency, impact & confidence scores so teams know what to do next."),
        ],
    ):
        with col:
            st.markdown(
                f"<div class='cp-card'><p class='val'>{title}</p><p class='sub'>{body}</p></div>",
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
    label = level.title() or "—"
    return (
        f"<div class='cp-confidence {css_class}'>"
        f"<span class='cp-conf-label'>Confidence</span>"
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
        label, color = "High", _CONF_COLOR_HEX["high"]
    elif pct >= 45:
        label, color = "Medium", _CONF_COLOR_HEX["medium"]
    else:
        label, color = "Low", _CONF_COLOR_HEX["low"]
    return (
        f"<div class='cp-confidence'>"
        f"<div class='cp-conf-row'><span class='icon'>🛡️</span>"
        f"<span class='cp-conf-label'>Confidence</span>"
        f"<span class='cp-conf-value' style='color:{color}'>{label} · {pct}%</span></div>"
        f"<div class='cp-conf-track'><div class='cp-conf-fill' style='width:{pct}%;background:{color}'></div></div>"
        f"</div>"
    )


def render_qa_answer(result) -> None:
    """Shared renderer for one Ask AI answer -- used both for the freshly
    answered turn and for replaying prior turns in the chat history."""
    data = result.data
    if result.used_fallback:
        st.caption("⚠️ Offline fallback answer (Gemini not called).")

    if "what_is_happening" in data:
        conf_pct = agentic_confidence_pct(data.get("_tool_trace"))
        st.markdown(confidence_bar(conf_pct), unsafe_allow_html=True)
        if data.get("explanation"):
            st.markdown(data["explanation"])
            st.write("")
        st.markdown(f"📊 **What's happening.** {data.get('what_is_happening', '')}")
        st.markdown(f"🔷 **Why it matters.** {data.get('why_it_matters', '')}")

        where = data.get("where")
        if isinstance(where, list) and where:
            where_str = "&nbsp;&nbsp;".join(f"{i}. {w}" for i, w in enumerate(where, 1))
        elif isinstance(where, str) and where.strip():
            where_str = where
        else:
            where_str = "not enough data"
        st.markdown(f"📍 **Where.** {where_str}", unsafe_allow_html=True)

        st.markdown(f"🎯 **Recommended next step.** {data.get('recommended_next_step', '')}")
        st.info(f"🗣️ {data.get('executive_summary', '')}")
    else:
        st.write(data.get("summary", data))

    trace = data.get("_tool_trace")
    if trace:
        n = len(trace)
        with st.expander(f"🔧 How CivicPulse checked this ({n} data quer{'y' if n == 1 else 'ies'})"):
            st.caption(
                "Every number above came from one of these real queries against your "
                "dataset — Gemini chose what to look up, not what the numbers say."
            )
            for t in trace:
                args_str = ", ".join(f"{k}={v}" for k, v in (t.get("args") or {}).items()) or "—"
                if t.get("error"):
                    st.caption(f"❌ `{t['tool']}({args_str})` → {t['error']}")
                elif "record_count" in t:
                    rc = t.get("record_count")
                    st.caption(f"✅ `{t['tool']}({args_str})` → {rc} matching record{'s' if rc != 1 else ''}")
                else:
                    st.caption(f"✅ `{t['tool']}({args_str})` → full dataset snapshot")


_URGENCY_ICON = {"immediate": "🔴", "high": "🟠", "normal": "⚪"}


def _brief_to_markdown(data: dict) -> str:
    lines = [f"# {data.get('title', 'CivicPulse Action Memo')}", ""]
    if data.get("dataset_overview"):
        lines.append("## Dataset overview")
        lines.append(data["dataset_overview"])
        lines.append("")
    lines.append(f"_{data.get('summary', '')}_\n")
    if data.get("key_findings"):
        lines.append("## Key findings")
        lines += [f"- {f}" for f in data["key_findings"]]
        lines.append("")
    patterns = data.get("peculiar_patterns") or data.get("anomalies")
    if patterns:
        lines.append("## Peculiar patterns")
        lines += [f"- {a}" for a in patterns]
        lines.append("")
    if data.get("recommended_actions"):
        lines.append("## Recommended actions — respond by urgency")
        for i, act in enumerate(data["recommended_actions"], 1):
            if isinstance(act, dict):
                urgency = str(act.get("urgency", "")).lower()
                icon = _URGENCY_ICON.get(urgency, "")
                lines.append(
                    f"{i}. {icon} {act.get('action', '')} "
                    f"(owner: {act.get('owner', '—')}, timeframe: {act.get('timeframe', '—')}"
                    + (f", urgency: {urgency}" if urgency else "")
                    + ")"
                )
            else:
                lines.append(f"{i}. {act}")
        lines.append("")
    if data.get("explanation"):
        lines.append("## Why this recommendation")
        lines.append(data["explanation"])
        lines.append("")
    lines.append(f"**Confidence:** {str(data.get('confidence', '—')).title()}")
    lines.append("\n---\n_Generated by CivicPulse AI._")
    return "\n".join(lines)


def render_actions(actions: list) -> None:
    for i, act in enumerate(actions or [], 1):
        if isinstance(act, dict):
            owner = act.get("owner", "—")
            tf = act.get("timeframe", "—")
            urgency = str(act.get("urgency", "")).lower()
            icon = _URGENCY_ICON.get(urgency, "")
            st.markdown(f"**{i}. {icon} {act.get('action', '')}**")
            caption = f"Owner: {owner}  ·  Timeframe: {tf}"
            if urgency:
                caption += f"  ·  Urgency: {urgency}"
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


# ---------------------------------------------------------------- tabs
tab_overview, tab_ask, tab_anom, tab_reco, tab_about = st.tabs(
    ["📊 Overview", "💬 Ask AI", "🚨 Anomalies", "✅ Recommendations", "ℹ️ About"]
)


# ============================== OVERVIEW ==============================
with tab_overview:
    if insights is None:
        st.warning(
            "This source is unstructured (text/PDF). Head to **Ask AI** or "
            "**Recommendations** for an AI summary of the content."
        )
    else:
        d = insights.to_dict()
        scores = d["scores"]

        st.markdown("<div class='cp-section-title'>Community Snapshot</div>", unsafe_allow_html=True)
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(
                f"<div class='cp-card'><p class='lbl'>📄 Records</p><p class='val'>{d['total_records']}</p>"
                f"<p class='sub'>{d['date_range'].get('start','?')} → {d['date_range'].get('end','?')}</p></div>",
                unsafe_allow_html=True,
            )
        with k2:
            st.markdown(
                f"<div class='cp-card'><p class='lbl'>📍 Top hotspot</p><p class='val'>{humanize(d['hotspot_area'] or 'n/a')}</p>"
                f"<p class='sub'>Most-affected area</p></div>",
                unsafe_allow_html=True,
            )
        with k3:
            st.markdown(
                f"<div class='cp-card'><p class='lbl'>⚠️ Leading issue</p><p class='val'>{humanize(d['top_category'] or 'n/a')}</p>"
                f"<p class='sub'>Top category</p></div>",
                unsafe_allow_html=True,
            )
        with k4:
            arrow = {"rising": "▲", "falling": "▼", "flat": "▬"}[d["trend_direction"]]
            st.markdown(
                f"<div class='cp-card'><p class='lbl'>📈 Weekly trend</p><p class='val'>{arrow} {d['trend_direction'].title()}</p>"
                f"<p class='sub'>{d['trend_change_pct']:+.1f}% vs prior week</p></div>",
                unsafe_allow_html=True,
            )

        st.write("")
        st.markdown("<div class='cp-section-title'>Decision Scoreboard</div>", unsafe_allow_html=True)
        s1, s2, s3, s4 = st.columns(4)
        s1.markdown(score_pill("⚠️ Urgency", scores["urgency"], urgency_color(scores["urgency"])), unsafe_allow_html=True)
        s2.markdown(score_pill("📈 Impact", scores["impact"], t["cyan"]), unsafe_allow_html=True)
        s3.markdown(score_pill("🛡️ Confidence", scores["confidence"], t["violet"]), unsafe_allow_html=True)
        s4.markdown(score_pill("🌡️ Severity", scores["severity_index"], t["magenta"]), unsafe_allow_html=True)
        st.caption(f"Open/unresolved case rate: **{d['open_rate_pct']}%**")
        cb = scores.get("confidence_breakdown")
        if cb:
            with st.expander("Why this confidence score?"):
                st.caption(
                    f"Sample size: **{cb['sample_size_score']:.0f}**/40 · "
                    f"Recency: **{cb['recency_score']:.0f}**/30 · "
                    f"Stability: **{cb['stability_score']:.0f}**/30 "
                    "— more reports, more recent data, and a steadier day-to-day pattern "
                    "all raise confidence."
                )

        st.write("")
        map_title_col, map_toggle_col = st.columns([4, 1.4])
        with map_title_col:
            st.markdown("<div class='cp-section-title'>🗺️ Hotspot map</div>", unsafe_allow_html=True)
            st.caption("Blends volume, severity, and unresolved backlog into one score per area.")
        if d.get("geo_summary"):
            geo_df = pd.DataFrame(d["geo_summary"])
            geo_df["coord_label"] = geo_df["coord_source"].map({
                "real_ward": "Real BBMP ward location", "provided": "Provided coordinates",
                "placeholder": "Placeholder (unmatched)",
            })
            # A plain Streamlit control instead of Plotly's own in-chart
            # updatemenus buttons -- those used to sit top-right on the map
            # and collided with Plotly's built-in modebar (camera/pan/zoom/
            # fullscreen icons), which also lives top-right and can't be
            # moved. A separate widget above the chart can never overlap it.
            st.session_state.setdefault("map_basemap", "🌙 Dark" if theme == "dark" else "☀️ Light")
            with map_toggle_col:
                st.radio(
                    "Basemap", ["🌙 Dark", "☀️ Light"], horizontal=True,
                    label_visibility="collapsed", key="map_basemap",
                )
            mapbox_style = "carto-darkmatter" if "Dark" in st.session_state.map_basemap else "carto-positron"
            map_is_dark = mapbox_style == "carto-darkmatter"

            fig_map = px.scatter_mapbox(
                geo_df, lat="lat", lon="lon", size="hotspot_score", color="coord_label",
                hover_name="area",
                hover_data={"total_complaints": True, "open_rate_pct": True, "high_severity_rate_pct": True,
                            "lat": False, "lon": False, "hotspot_score": ":.1f", "coord_label": False},
                color_discrete_map={
                    "Real BBMP ward location": t["geo_real"],
                    "Provided coordinates": t["geo_provided"],
                    "Placeholder (unmatched)": t["geo_placeholder"],
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
            st.markdown(
                "<div class='cp-size-legend'>"
                "<span class='item'><span class='dot' style='width:20px;height:20px'></span>High hotspot score</span>"
                "<span class='item'><span class='dot' style='width:13px;height:13px'></span>Medium</span>"
                "<span class='item'><span class='dot' style='width:7px;height:7px'></span>Low</span>"
                "</div>",
                unsafe_allow_html=True,
            )
            st.caption("🖱️ Scroll or pinch to zoom, drag to pan, click a legend item to filter by coordinate source.")

            n_real = int((geo_df["coord_source"] == "real_ward").sum())
            n_placeholder = int((geo_df["coord_source"] == "placeholder").sum())
            n_total = len(geo_df)
            st.caption(
                f"📍 {n_real}/{n_total} areas use real BBMP ward coordinates "
                f"(OpenCity ward office dataset). {n_placeholder} unmatched area(s) use a "
                "deterministic placeholder position instead of a guess."
            )
        else:
            st.info("Not enough area data to build a hotspot map.")

        st.write("")
        st.markdown("<div class='cp-section-title'>📈 7-day forecast</div>", unsafe_allow_html=True)
        st.caption("Trend-aware forecasting (Holt's linear method) — predicts likely spikes before they happen, not just after.")
        if d.get("forecasts"):
            fc_df = pd.DataFrame(d["forecasts"])
            for _, row in fc_df.iterrows():
                icon = "🔴" if row["will_likely_spike"] else "🟢"
                fc1, fc2, fc3 = st.columns([2, 2, 1])
                with fc1:
                    st.markdown(f"{icon} **{humanize(row['area'])}**")
                with fc2:
                    st.caption(f"{row['last_7day_avg']:.1f}/day → {row['forecast_7day_avg']:.1f}/day predicted")
                with fc3:
                    st.markdown(f"**{row['pct_change']:+.1f}%**")
        else:
            st.info("Not enough daily history yet to forecast (needs 7+ days of dated records).")

        st.write("")
        df = load_result.df
        c_left, c_right = st.columns(2)
        with c_left:
            if d["by_area"]:
                fig = px.bar(
                    x=list(d["by_area"].values()),
                    y=[humanize(a) for a in d["by_area"].keys()],
                    orientation="h",
                    labels={"x": "Complaints", "y": ""},
                    title="Complaints by area",
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
                    tdf, x="week", y="count", title="Weekly volume trend", markers=True,
                )
                fig2.update_traces(line_color=t["area_line"], fillcolor=t["area_fill"], marker=dict(color=t["area_marker"], size=7))
                fig2.update_layout(height=340, margin=dict(l=0, r=0, t=40, b=0), **CHART_LAYOUT)
                st.plotly_chart(fig2, use_container_width=True)

        c_a, c_b = st.columns(2)
        with c_a:
            if d["by_category"]:
                fig3 = px.pie(
                    names=[humanize(k) for k in d["by_category"].keys()],
                    values=list(d["by_category"].values()),
                    title="Category mix", hole=0.5,
                    color_discrete_sequence=t["pie_sequence"],
                )
                fig3.update_traces(marker=dict(line=dict(color=t["pie_line"], width=2)))
                fig3.update_layout(height=340, margin=dict(l=0, r=0, t=40, b=0), **CHART_LAYOUT)
                st.plotly_chart(fig3, use_container_width=True)
        with c_b:
            if d["severity_distribution"]:
                order = ["low", "medium", "high", "critical"]
                sd = {k: d["severity_distribution"].get(k, 0) for k in order if k in d["severity_distribution"]}
                fig4 = px.bar(
                    x=[k.title() for k in sd.keys()], y=list(sd.values()),
                    title="Severity distribution", labels={"x": "", "y": "Count"},
                    color=[k.title() for k in sd.keys()],
                    color_discrete_map={"Low": "#22c55e", "Medium": "#f59e0b", "High": "#fb923c", "Critical": "#ef4444"},
                )
                fig4.update_layout(showlegend=False, height=340, margin=dict(l=0, r=0, t=40, b=0), **CHART_LAYOUT)
                st.plotly_chart(fig4, use_container_width=True)

        with st.expander("Preview raw data"):
            st.dataframe(df.head(50), use_container_width=True)


# ============================== ASK AI ==============================
def _msg_meta(sender: str, ts: str) -> str:
    ts_html = f"<span>{ts}</span>" if ts else ""
    return f"<div class='cp-msg-meta'><span class='cp-msg-sender'>{sender}</span>{ts_html}</div>"


with tab_ask:
    STARTER_SUGGESTIONS = [
        "Which area has the most urgent issues?",
        "What patterns are increasing this week?",
        "Compare the top two hotspot areas.",
        "What should we prioritize this week?",
    ]
    picked = None

    col_suggest, col_chat, col_history = st.columns([1, 2.3, 1])

    # ---- Left: persistent suggested-questions panel -------------------
    with col_suggest:
        st.markdown("<div class='cp-section-title'>💡 Suggested questions</div>", unsafe_allow_html=True)
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
            if st.button("🔄 Start a new conversation", use_container_width=True):
                st.session_state.qa_history = []
                st.session_state.qa_conversation = None
                _persist_session()
                st.rerun()

    # ---- Middle: the live conversation ---------------------------------
    with col_chat:
        st.markdown("<div class='cp-section-title'>Conversation</div>", unsafe_allow_html=True)
        st.caption(
            "Grounded strictly in your data — the model never invents numbers. "
            "Keep asking follow-ups; CivicPulse remembers the conversation."
        )

        # Render the full conversation BEFORE the input box, so the input
        # always ends up visually pinned below every message -- st.chat_input
        # renders inline exactly where it's called when used inside a
        # column/tab (it only auto-floats to the page bottom at the top
        # level), so code order here is what determines its on-screen
        # position.
        for q, result, ts in st.session_state.qa_history:
            with st.chat_message("user"):
                st.markdown(_msg_meta("You", ts), unsafe_allow_html=True)
                st.markdown(q)
            with st.chat_message("assistant", avatar="🏙️"):
                st.markdown(_msg_meta("CivicPulse AI (Gemini)", ts), unsafe_allow_html=True)
                render_qa_answer(result)

        if not st.session_state.qa_history:
            st.caption("💡 Tap a suggested question on the left, or type your own below.")

        typed_question = st.chat_input("Ask a question about your data...")
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
                with st.spinner("Gemini is querying the data..."):
                    result, updated_conv = gemini.answer_question_agentic(
                        load_result.df, payload, question, st.session_state.domain,
                        conversation=prior_conv,
                    )
                st.session_state.qa_conversation = updated_conv
            else:
                raw = load_result.raw_text or ""
                with st.spinner("Analyzing..."):
                    result = gemini.summarize_text(raw, st.session_state.domain)
            st.session_state.qa_history.append((question, result, datetime.now().strftime("%I:%M %p")))
            _persist_session()
            # Rerun so this turn renders through the history loop above (in
            # its natural position above the input) instead of appearing
            # transiently below the already-rendered input box for one frame.
            st.rerun()

    # ---- Right: chat history log + trust card --------------------------
    with col_history:
        st.markdown("<div class='cp-section-title'>🕘 Chat history</div>", unsafe_allow_html=True)
        if st.session_state.qa_history:
            for q, _result, ts in reversed(st.session_state.qa_history):
                preview = q if len(q) <= 60 else q[:57] + "…"
                st.markdown(
                    f"<div class='cp-history-item'><span class='cp-history-time'>{ts}</span>{preview}</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No questions yet this session.")
        st.markdown(
            "<div class='cp-trust-card'><span class='icon'>🛡️</span>"
            "<span><b>Ask AI, get grounded answers.</b><br>"
            "CivicPulse AI uses your data + real queries. No guessing. No made-up numbers.</span></div>",
            unsafe_allow_html=True,
        )


# ============================== ANOMALIES ==============================
with tab_anom:
    st.markdown("<div class='cp-section-title'>🚨 Emerging anomalies</div>", unsafe_allow_html=True)
    st.caption(
        "Flagged by simple statistical thresholds (σ, \"sigma\" ≥ 1.5) — transparent and cheap. "
        "**What's a σ score?** It's how far a number is from what's typical, measured in "
        "\"standard deviations.\" σ ≈ 1.5–2 is worth a look; above ~2.5–3 is a real outlier, "
        "not just normal day-to-day variation."
    )
    if insights is None:
        st.info("Anomaly detection needs structured (CSV/JSON) data.")
    else:
        anomalies = insights.to_dict()["anomalies"]
        if not anomalies:
            st.success("No significant anomalies detected in this dataset.")
        else:
            for a in anomalies:
                sev = "🔴" if a["score"] >= 2.5 else ("🟠" if a["score"] >= 2.0 else "🟡")
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"{sev} **{a['label']}**  ·  _{a['dimension']}_")
                        st.caption(a["detail"])
                    with c2:
                        st.metric("σ score", f"{a['score']:.1f}")


# ============================== RECOMMENDATIONS ==============================
with tab_reco:
    st.markdown("<div class='cp-section-title'>✅ One-click Executive Brief</div>", unsafe_allow_html=True)
    st.caption(
        "The wow feature: a complete, plain-language handoff memo — written for whoever has "
        "to act on this data, even if they've never seen it before. One Gemini call, fully grounded."
    )

    if st.button("🧠 Generate Executive Brief", type="primary"):
        with st.spinner("Gemini is drafting your decision memo..."):
            if insights is not None:
                st.session_state.brief = gemini.executive_brief(
                    insights.to_dict(), st.session_state.domain
                )
            else:
                st.session_state.brief = gemini.summarize_text(
                    load_result.raw_text or "", st.session_state.domain
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
        data = brief.data
        if brief.used_fallback:
            st.warning("Showing offline fallback brief (Gemini not called). Set a key for full AI output.")

        st.markdown(f"## 📝 {data.get('title', 'Executive Brief')}")

        if data.get("dataset_overview"):
            st.markdown("#### 📖 What this dataset is")
            st.markdown(data["dataset_overview"])
            st.write("")

        st.markdown(f"> {data.get('summary', '')}")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Key findings")
            for f in data.get("key_findings", []):
                st.markdown(f"- {f}")
            patterns = data.get("peculiar_patterns") or data.get("anomalies")
            if patterns:
                st.markdown("#### 🔎 Peculiar patterns")
                for a in patterns:
                    st.markdown(f"- {a}")
        with col2:
            st.markdown("#### Recommended actions — respond by urgency")
            st.caption("🔴 immediate (ASAP) · 🟠 high (this week) · ⚪ normal (this month)")
            render_actions(data.get("recommended_actions", []))
            st.markdown("#### Confidence")
            st.markdown(confidence_badge(data.get("confidence")), unsafe_allow_html=True)

        if data.get("explanation"):
            with st.expander("🔍 Explainability — why this recommendation?"):
                st.write(data["explanation"])

        # Downloadable memo.
        memo = _brief_to_markdown(data)
        st.download_button(
            "⬇️ Download memo (Markdown)",
            memo,
            file_name="civicpulse_action_memo.md",
            mime="text/markdown",
        )
    else:
        st.info("Click **Generate Executive Brief** to produce a decision-ready memo.")

    if history.available:
        recent = history.list_recent(limit=5)
        if recent:
            st.write("")
            with st.expander(f"📜 Recent briefs ({len(recent)}) — trend across past uploads"):
                st.caption(
                    "Every generated brief is saved automatically, so a team can see how a "
                    "location trends across sessions instead of only today's snapshot."
                )
                for r in recent:
                    ts = r.get("created_at")
                    ts_str = ts.strftime("%b %d, %Y %H:%M UTC") if hasattr(ts, "strftime") else str(ts or "—")
                    st.markdown(f"**{r.get('brief_title') or 'Untitled brief'}** · {ts_str}")
                    st.caption(
                        f"{humanize(r.get('hotspot_area') or '—')} · {humanize(r.get('top_category') or '—')} · "
                        f"{r.get('total_records', '—')} records · trend: {r.get('trend_direction', '—')}"
                    )
                    st.divider()

    st.write("")
    st.markdown("<div class='cp-section-title'>🔔 Automated Weekly Reports</div>", unsafe_allow_html=True)
    st.caption(
        "Every Monday, a Cloud Scheduler job runs this same pipeline automatically and emails "
        "a citywide brief plus one department-scoped report to each configured department "
        "contact — nobody has to open this dashboard. Trigger it now to see it live."
    )
    if not SCHEDULED_BRIEF_FUNCTION_URL:
        st.info("Scheduled-report trigger isn't configured for this deployment.")
    elif st.button("📨 Send scheduled reports now"):
        with st.spinner("Triggering the scheduled job — generating and emailing citywide + department reports..."):
            st.session_state.trigger_result = trigger_scheduled_reports(SCHEDULED_BRIEF_FUNCTION_URL)

    trigger_result = st.session_state.get("trigger_result")
    if trigger_result:
        if trigger_result.get("error"):
            st.error(f"Trigger failed: {trigger_result['error']}")
        else:
            fallback_note = " (offline fallback used)" if trigger_result.get("gemini_used_fallback") else ""
            st.success(f"✅ Citywide brief: {trigger_result.get('email_status', '—')}{fallback_note}")
            dept_reports = trigger_result.get("department_reports") or {}
            for dept, status in dept_reports.items():
                icon = "✅" if status.startswith("sent") else ("⏭️" if status.startswith("skipped") else "❌")
                st.caption(f"{icon} **{dept}** — {status}")


# ============================== ABOUT ==============================
with tab_about:
    st.markdown("<div class='cp-section-title'>ℹ️ About CivicPulse AI</div>", unsafe_allow_html=True)
    st.markdown(
        """
**CivicPulse AI** is a decision intelligence dashboard for cities and communities.
It combines **deterministic Python analytics** (counts, trends, anomaly detection,
forecasting) with a **small, low-cost Gemini model** that explains the numbers and
recommends concrete next steps — and a set of Google Cloud services that turn it
from a one-off dashboard into an automated service.

**Why it's different from a chatbot**
- Numbers are computed locally first, so the AI never hallucinates statistics.
- Every answer maps to a decision: *what / why / where / next step / confidence*.
- A Decision Scoreboard (urgency · impact · confidence) tells teams what to act on.

**What's in here**
- 🎨 **Light/dark app theme** — toggle at the top of the sidebar switches the
  whole dashboard between a clean professional light theme and the futuristic
  neon theme, for whichever reads best on your screen.
- 💬 **Agentic, multi-turn chat** — Ask AI calls real query tools against your live
  data (not one static snapshot) and remembers the conversation, so follow-ups like
  *"what about the second one?"* just work. Every answer shows exactly which
  queries ran, and suggests grounded next questions to tap.
- 🗺️ **Real hotspot mapping** — actual BBMP ward coordinates (OpenCity's Bengaluru
  ward dataset), with its own dark/light basemap toggle above the map.
- 📈 **7-day forecasting** — Holt's linear trend method flags likely spikes per
  area before they happen, not just after.
- 📝 **One-click Executive Brief** — a complete, plain-language handoff memo
  (dataset overview, every notable pattern, urgency-tagged next steps) from a
  single grounded Gemini call.
- 🗄️ **Persistent brief history** — every generated brief saves to Firestore, so
  a team can see trends across sessions, not just today's upload.
- 🔄 **Reload-safe sessions** — your loaded data and chat history survive a page
  refresh, restored from Firestore via a session id kept in the URL; stale
  sessions auto-expire after 24h.
- 🔔 **Automated, department-routed email** — a Cloud Scheduler job runs the same
  pipeline on a cron and emails a citywide brief *plus* a separate brief per
  department, scoped to only that department's data, to that department's own
  contacts — with an in-app button to trigger it on demand.

**Google Cloud stack**
- 🤖 **Vertex AI / Gemini** (`gemini-2.5-flash-lite` by default) — explanations,
  agentic function calling, brief generation
- 🚀 **Cloud Run** — hosts the app, scale-to-zero so idle cost is ~$0
- ⚡ **Cloud Functions (2nd gen)** — the scheduled brief job
- ⏰ **Cloud Scheduler** — triggers the weekly automated run
- 🗄️ **Firestore** — brief history + reload-safe session persistence
- 🔐 **Secret Manager** — stores the Gmail app password, never in code
- 🛠️ **Cloud Build**, **Artifact Registry**, **IAM**, **Cloud Logging**, **`gcloud` CLI**
  — builds, image storage, least-privilege service accounts, and one-command deploys

**Cost design**
- One Gemini call per meaningful action (not per keystroke)
- Cheap flash-lite model tier
- Cloud Run and Cloud Functions both scale to zero when idle
- Firestore/Secret Manager/Scheduler all stay within their free tiers at this scale

---

#### 📖 Key terms, in plain language

| Term | What it means |
|---|---|
| **σ score (sigma / standard deviation)** | A measure of "how unusual is this compared to normal?" A σ score of 2 means a value is about twice as far from the typical/average value as most others ever get — the higher the number, the more it stands out. CivicPulse flags anything ≥ 1.5σ as worth a second look; anything above ~2.5–3σ is a genuine outlier, not just normal day-to-day variation. |
| **Confidence score** | How much CivicPulse trusts its own numbers, based on three real signals: how much data there is, how recent it is, and how steady (vs. erratic) the daily pattern is — *not* a guess about whether the underlying problem is real. |
| **Urgency** | How pressing the situation looks right now, blending severity, how many cases are still unresolved, and whether volume is trending up. |
| **Impact** | How large-scale the issue is — driven by total volume and how concentrated it is in one area. |
| **Severity index** | The average severity level (low/medium/high/critical) across all records, scaled 0–100. |
| **Hotspot score** (on the map) | One combined score per area blending complaint volume, severity, and how many cases are still open — the number behind each map marker's size. |
        """
    )

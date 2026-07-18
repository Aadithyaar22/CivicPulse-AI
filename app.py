"""CivicPulse AI - community decision intelligence dashboard.

Run locally:   streamlit run app.py
Deploy:        see deploy.sh / README.md (Cloud Run)

Philosophy: "Not just answers - better decisions."
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import compute_insights, filter_dataframe
from src.data_loader import LoadResult, load_sample, load_text, load_uploaded_file
from src.gemini_client import GeminiClient
from src.utils import humanize

# Load .env if present (local dev convenience).
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

APP_DIR = Path(__file__).parent
SAMPLE_CSV = APP_DIR / "sample_data" / "citizen_complaints.csv"

st.set_page_config(
    page_title="CivicPulse AI",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------- styling
CSS = """
<style>
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }
    .cp-hero {
        background: linear-gradient(120deg, #0f766e 0%, #0e7490 55%, #1d4ed8 100%);
        color: #fff; padding: 1.4rem 1.6rem; border-radius: 16px; margin-bottom: 1.2rem;
        box-shadow: 0 10px 30px rgba(13,110,110,0.25);
    }
    .cp-hero h1 { margin: 0; font-size: 1.9rem; letter-spacing: -0.5px; }
    .cp-hero p { margin: .3rem 0 0; opacity: .92; font-size: .98rem; }
    .cp-badge {
        display:inline-block; background: rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.35);
        padding: 2px 10px; border-radius: 999px; font-size:.72rem; margin-right:6px; margin-top:.5rem;
    }
    .cp-card {
        background: #ffffff; border: 1px solid #e6e9ef; border-radius: 14px;
        padding: 1rem 1.1rem; height: 100%;
        box-shadow: 0 2px 10px rgba(16,24,40,0.04);
    }
    .cp-card .lbl { font-size:.72rem; text-transform:uppercase; letter-spacing:.06em; color:#667085; margin:0; }
    .cp-card .val { font-size:1.35rem; font-weight:700; color:#101828; margin:.15rem 0 0; }
    .cp-card .sub { font-size:.8rem; color:#475467; margin:.2rem 0 0; }
    .cp-pill { border-radius:12px; padding:.9rem 1rem; color:#fff; text-align:center; }
    .cp-section-title { font-weight:700; font-size:1.05rem; margin:.2rem 0 .6rem; color:#101828; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] { padding: 8px 16px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- state
def _init_state() -> None:
    st.session_state.setdefault("load_result", None)
    st.session_state.setdefault("insights", None)
    st.session_state.setdefault("brief", None)
    st.session_state.setdefault("qa_history", [])
    st.session_state.setdefault("domain", "citizen complaints")


_init_state()


@st.cache_resource(show_spinner=False)
def get_gemini() -> GeminiClient:
    return GeminiClient()


gemini = get_gemini()


def _set_data(load_result: LoadResult) -> None:
    st.session_state.load_result = load_result
    st.session_state.brief = None  # invalidate cached brief on new data
    st.session_state.qa_history = []
    if load_result.df is not None and not load_result.df.empty:
        st.session_state.insights = compute_insights(load_result.df)
    else:
        st.session_state.insights = None


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("### 🏙️ CivicPulse AI")
    st.caption("Community decision intelligence")

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

    st.divider()
    st.caption("Built with Streamlit + Gemini on Google Cloud Run.")


# ---------------------------------------------------------------- hero
st.markdown(
    """
    <div class="cp-hero">
        <h1>🏙️ CivicPulse AI</h1>
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
        f"<div class='cp-pill' style='background:{color}'>"
        f"<div style='font-size:.72rem;opacity:.9'>{label}</div>"
        f"<div style='font-size:1.6rem;font-weight:800'>{value:.0f}</div>"
        f"<div style='font-size:.68rem;opacity:.85'>/ 100</div></div>"
    )


def urgency_color(v: float) -> str:
    if v >= 70:
        return "#dc2626"
    if v >= 45:
        return "#d97706"
    return "#059669"


def _brief_to_markdown(data: dict) -> str:
    lines = [f"# {data.get('title', 'CivicPulse Action Memo')}", ""]
    lines.append(f"_{data.get('summary', '')}_\n")
    if data.get("key_findings"):
        lines.append("## Key findings")
        lines += [f"- {f}" for f in data["key_findings"]]
        lines.append("")
    if data.get("anomalies"):
        lines.append("## Anomalies")
        lines += [f"- {a}" for a in data["anomalies"]]
        lines.append("")
    if data.get("recommended_actions"):
        lines.append("## Recommended actions")
        for i, act in enumerate(data["recommended_actions"], 1):
            if isinstance(act, dict):
                lines.append(
                    f"{i}. {act.get('action', '')} "
                    f"(owner: {act.get('owner', '—')}, timeframe: {act.get('timeframe', '—')})"
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
            st.markdown(f"**{i}. {act.get('action', '')}**")
            st.caption(f"Owner: {owner}  ·  Timeframe: {tf}")
        else:
            st.markdown(f"**{i}.** {act}")


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
                f"<div class='cp-card'><p class='lbl'>Records</p><p class='val'>{d['total_records']}</p>"
                f"<p class='sub'>{d['date_range'].get('start','?')} → {d['date_range'].get('end','?')}</p></div>",
                unsafe_allow_html=True,
            )
        with k2:
            st.markdown(
                f"<div class='cp-card'><p class='lbl'>Top hotspot</p><p class='val'>{humanize(d['hotspot_area'] or 'n/a')}</p>"
                f"<p class='sub'>Most-affected area</p></div>",
                unsafe_allow_html=True,
            )
        with k3:
            st.markdown(
                f"<div class='cp-card'><p class='lbl'>Leading issue</p><p class='val'>{humanize(d['top_category'] or 'n/a')}</p>"
                f"<p class='sub'>Top category</p></div>",
                unsafe_allow_html=True,
            )
        with k4:
            arrow = {"rising": "▲", "falling": "▼", "flat": "▬"}[d["trend_direction"]]
            st.markdown(
                f"<div class='cp-card'><p class='lbl'>Weekly trend</p><p class='val'>{arrow} {d['trend_direction'].title()}</p>"
                f"<p class='sub'>{d['trend_change_pct']:+.1f}% vs prior week</p></div>",
                unsafe_allow_html=True,
            )

        st.write("")
        st.markdown("<div class='cp-section-title'>Decision Scoreboard</div>", unsafe_allow_html=True)
        s1, s2, s3, s4 = st.columns(4)
        s1.markdown(score_pill("Urgency", scores["urgency"], urgency_color(scores["urgency"])), unsafe_allow_html=True)
        s2.markdown(score_pill("Impact", scores["impact"], "#1d4ed8"), unsafe_allow_html=True)
        s3.markdown(score_pill("Confidence", scores["confidence"], "#0e7490"), unsafe_allow_html=True)
        s4.markdown(score_pill("Severity", scores["severity_index"], "#7c3aed"), unsafe_allow_html=True)
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
        st.markdown("<div class='cp-section-title'>🗺️ Hotspot map</div>", unsafe_allow_html=True)
        st.caption("Blends volume, severity, and unresolved backlog into one score per area.")
        if d.get("geo_summary"):
            geo_df = pd.DataFrame(d["geo_summary"])
            geo_df["coord_label"] = geo_df["coord_source"].map({
                "real_ward": "Real BBMP ward location", "provided": "Provided coordinates",
                "placeholder": "Placeholder (unmatched)",
            })
            fig_map = px.scatter_mapbox(
                geo_df, lat="lat", lon="lon", size="hotspot_score", color="coord_label",
                hover_name="area",
                hover_data={"total_complaints": True, "open_rate_pct": True, "high_severity_rate_pct": True,
                            "lat": False, "lon": False, "hotspot_score": ":.1f", "coord_label": False},
                color_discrete_map={
                    "Real BBMP ward location": "#0e7490",
                    "Provided coordinates": "#1d4ed8",
                    "Placeholder (unmatched)": "#d97706",
                },
                size_max=32, zoom=10, mapbox_style="carto-positron",
            )
            # Auto-fit the view to the actual data instead of a fixed zoom level.
            lat_span = geo_df["lat"].max() - geo_df["lat"].min()
            lon_span = geo_df["lon"].max() - geo_df["lon"].min()
            span = max(lat_span, lon_span, 0.01)
            auto_zoom = 12 if span < 0.05 else (10 if span < 0.15 else (8 if span < 0.5 else 6))
            fig_map.update_layout(
                height=520, margin=dict(l=0, r=0, t=10, b=0), legend_title_text="",
                mapbox=dict(
                    center=dict(lat=float(geo_df["lat"].mean()), lon=float(geo_df["lon"].mean())),
                    zoom=auto_zoom,
                ),
            )
            st.plotly_chart(
                fig_map, use_container_width=True,
                config={"scrollZoom": True, "displayModeBar": True, "displaylogo": False},
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
                    color_continuous_scale="Teal",
                )
                fig.update_layout(showlegend=False, coloraxis_showscale=False, height=340, margin=dict(l=0, r=0, t=40, b=0))
                fig.update_yaxes(autorange="reversed")
                st.plotly_chart(fig, use_container_width=True)
        with c_right:
            if d["weekly_trend"]:
                tdf = pd.DataFrame(d["weekly_trend"])
                fig2 = px.area(
                    tdf, x="week", y="count", title="Weekly volume trend", markers=True,
                )
                fig2.update_traces(line_color="#0e7490", fillcolor="rgba(14,116,144,0.15)")
                fig2.update_layout(height=340, margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig2, use_container_width=True)

        c_a, c_b = st.columns(2)
        with c_a:
            if d["by_category"]:
                fig3 = px.pie(
                    names=[humanize(k) for k in d["by_category"].keys()],
                    values=list(d["by_category"].values()),
                    title="Category mix", hole=0.5,
                )
                fig3.update_layout(height=340, margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig3, use_container_width=True)
        with c_b:
            if d["severity_distribution"]:
                order = ["low", "medium", "high", "critical"]
                sd = {k: d["severity_distribution"].get(k, 0) for k in order if k in d["severity_distribution"]}
                fig4 = px.bar(
                    x=[k.title() for k in sd.keys()], y=list(sd.values()),
                    title="Severity distribution", labels={"x": "", "y": "Count"},
                    color=[k.title() for k in sd.keys()],
                    color_discrete_map={"Low": "#22c55e", "Medium": "#eab308", "High": "#f97316", "Critical": "#dc2626"},
                )
                fig4.update_layout(showlegend=False, height=340, margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig4, use_container_width=True)

        with st.expander("Preview raw data"):
            st.dataframe(df.head(50), use_container_width=True)


# ============================== ASK AI ==============================
with tab_ask:
    st.markdown("<div class='cp-section-title'>Ask in natural language</div>", unsafe_allow_html=True)
    st.caption("Grounded strictly in your data — the model never invents numbers.")

    suggestions = [
        "Which area has the most urgent issues?",
        "What patterns are increasing this week?",
        "Summarize the top community risks.",
        "What should we prioritize this week?",
    ]
    cols = st.columns(len(suggestions))
    picked = None
    for col, s in zip(cols, suggestions):
        if col.button(s, use_container_width=True):
            picked = s

    question = st.text_input("Your question", value=picked or "", placeholder="e.g. Where are waste complaints spiking?")
    ask = st.button("Ask CivicPulse", type="primary")

    if (ask or picked) and question.strip():
        if insights is not None:
            payload = insights.to_dict()
            with st.spinner("Analyzing..."):
                result = gemini.answer_question(payload, question, st.session_state.domain)
        else:
            raw = load_result.raw_text or ""
            with st.spinner("Analyzing..."):
                result = gemini.summarize_text(raw, st.session_state.domain)
        st.session_state.qa_history.insert(0, (question, result))

    for q, result in st.session_state.qa_history:
        with st.container(border=True):
            st.markdown(f"**Q: {q}**")
            if result.used_fallback:
                st.caption("⚠️ Offline fallback answer (Gemini not called).")
            data = result.data
            if "what_is_happening" in data:
                a, b = st.columns([3, 1])
                with a:
                    st.markdown(f"**What's happening.** {data.get('what_is_happening','')}")
                    st.markdown(f"**Why it matters.** {data.get('why_it_matters','')}")
                    st.markdown(f"**Where.** {data.get('where','')}")
                    st.markdown(f"**Recommended next step.** {data.get('recommended_next_step','')}")
                    st.info(f"🗣️ {data.get('executive_summary','')}")
                with b:
                    conf = str(data.get("confidence", "—")).title()
                    st.metric("Confidence", conf)
            else:
                st.write(data.get("summary", data))


# ============================== ANOMALIES ==============================
with tab_anom:
    st.markdown("<div class='cp-section-title'>🚨 Emerging anomalies</div>", unsafe_allow_html=True)
    st.caption("Flagged by simple statistical thresholds (z-score ≥ 1.5) — transparent and cheap.")
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
    st.caption("The wow feature: an auto-generated city action memo — one Gemini call, fully grounded.")

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

    brief = st.session_state.brief
    if brief is not None:
        data = brief.data
        if brief.used_fallback:
            st.warning("Showing offline fallback brief (Gemini not called). Set a key for full AI output.")

        st.markdown(f"## 📝 {data.get('title', 'Executive Brief')}")
        st.markdown(f"> {data.get('summary', '')}")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Key findings")
            for f in data.get("key_findings", []):
                st.markdown(f"- {f}")
            if data.get("anomalies"):
                st.markdown("#### Anomalies")
                for a in data["anomalies"]:
                    st.markdown(f"- {a}")
        with col2:
            st.markdown("#### Recommended actions")
            render_actions(data.get("recommended_actions", []))
            st.markdown("#### Confidence")
            st.info(str(data.get("confidence", "—")).title())

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


# ============================== ABOUT ==============================
with tab_about:
    st.markdown("<div class='cp-section-title'>ℹ️ About CivicPulse AI</div>", unsafe_allow_html=True)
    st.markdown(
        """
**CivicPulse AI** is a decision intelligence dashboard for cities and communities.
It combines **deterministic Python analytics** (counts, trends, anomaly detection)
with a **small, low-cost Gemini model** that explains the numbers and recommends
concrete next steps.

**Why it's different from a chatbot**
- Numbers are computed locally first, so the AI never hallucinates statistics.
- Every answer maps to a decision: *what / why / where / next step / confidence*.
- A Decision Scoreboard (urgency · impact · confidence) tells teams what to act on.

**Google Cloud stack**
- 🤖 **Gemini** (`gemini-2.5-flash-lite` by default) via Vertex AI or Gemini API
- 🚀 **Cloud Run** for serverless, scale-to-zero hosting (very low cost)
- 🛠️ **`gcloud` CLI** + Cloud Build for one-command deploys

**Cost design**
- One Gemini call per meaningful action (not per keystroke)
- Cheap flash-lite model tier
- Local sample data — no database required
- Cloud Run scales to zero when idle
        """
    )

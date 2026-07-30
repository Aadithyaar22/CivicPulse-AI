"""UI-chrome and categorical-value translations for English/Kannada/Hindi.

Two different translation surfaces, kept deliberately separate:

- UI_STRINGS: static text CivicPulse itself writes -- labels, buttons,
  captions, the About tab. Translated once, here, and swapped at render
  time by key. No runtime translation calls, no added latency or cost.

- VALUE_TRANSLATIONS: categorical values that come from the UPLOADED
  DATASET (area, category, severity, status, department) -- translated
  only for DISPLAY. The underlying dataframe stays in its original
  language, so analytics, filtering, and Gemini's tool calls keep working
  on the raw values unchanged; only what's rendered on screen is swapped.
  A value not found here (e.g. an uploaded dataset with different area
  names) falls back to the original text rather than showing blank.

Numbers, dates, and percentages are never touched by either -- they don't
need translating and doing so would risk misrepresenting the data.

Gemini-generated content (Ask AI answers, the Executive Brief) is NOT
translated here at all -- Gemini is simply asked to write directly in the
selected language (see LANGUAGE_NAMES + the lang param threaded through
gemini_client.py), which is more fluent than machine-translating its
English output after the fact.
"""

from __future__ import annotations

from typing import Any

LANGUAGES: dict[str, str] = {"en": "English", "kn": "ಕನ್ನಡ", "hi": "हिन्दी"}

# Full language names for Gemini prompts ("respond entirely in <name>").
LANGUAGE_NAMES: dict[str, str] = {"en": "English", "kn": "Kannada", "hi": "Hindi"}


UI_STRINGS: dict[str, dict[str, str]] = {
    # ---------------------------------------------------------------- sidebar
    "sidebar_tagline": {
        "en": "Community decision intelligence",
        "kn": "ಸಮುದಾಯ ನಿರ್ಧಾರ ಬುದ್ಧಿಮತ್ತೆ",
        "hi": "सामुदायिक निर्णय बुद्धिमत्ता",
    },
    # Hindi uses the common tech loanwords "डार्क"/"लाइट" rather than a
    # literal translation (गहरा/हल्का reads as "heavy/light in WEIGHT" to a
    # reader, not "dark/light in brightness" -- ambiguous for a theme toggle).
    "theme_light": {"en": "☀️ Light", "kn": "☀️ ಬೆಳಕು", "hi": "☀️ लाइट"},
    "theme_dark": {"en": "🌙 Dark", "kn": "🌙 ಕತ್ತಲೆ", "hi": "🌙 डार्क"},
    "sidebar_load_data_heading": {"en": "1. Load data", "kn": "1. ಡೇಟಾ ಲೋಡ್ ಮಾಡಿ", "hi": "1. डेटा लोड करें"},
    "load_demo_dataset_btn": {
        "en": "⚡ Load demo dataset", "kn": "⚡ ಡೆಮೊ ಡೇಟಾಸೆಟ್ ಲೋಡ್ ಮಾಡಿ", "hi": "⚡ डेमो डेटासेट लोड करें",
    },
    "demo_dataset_loaded": {"en": "Demo dataset loaded.", "kn": "ಡೆಮೊ ಡೇಟಾಸೆಟ್ ಲೋಡ್ ಆಗಿದೆ.", "hi": "डेमो डेटासेट लोड हो गया।"},
    "sample_file_missing": {
        "en": "Sample file missing. Run sample_data/generate_sample.py.",
        "kn": "ಮಾದರಿ ಫೈಲ್ ಕಾಣೆಯಾಗಿದೆ. sample_data/generate_sample.py ಅನ್ನು ಚಲಾಯಿಸಿ.",
        "hi": "नमूना फ़ाइल गायब है। sample_data/generate_sample.py चलाएँ।",
    },
    "upload_file_label": {
        "en": "Upload CSV / JSON / PDF / Excel",
        "kn": "CSV / JSON / PDF / Excel ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
        "hi": "CSV / JSON / PDF / Excel अपलोड करें",
    },
    "analyze_uploaded_file_btn": {"en": "Analyze uploaded file", "kn": "ಅಪ್‌ಲೋಡ್ ಮಾಡಿದ ಫೈಲ್ ವಿಶ್ಲೇಷಿಸಿ", "hi": "अपलोड की गई फ़ाइल का विश्लेषण करें"},
    "loaded_file_msg": {"en": "Loaded {name}", "kn": "{name} ಲೋಡ್ ಆಗಿದೆ", "hi": "{name} लोड हो गई"},
    "paste_text_expander": {"en": "Or paste text / report", "kn": "ಅಥವಾ ಪಠ್ಯ / ವರದಿ ಅಂಟಿಸಿ", "hi": "या टेक्स्ट / रिपोर्ट पेस्ट करें"},
    "paste_text_placeholder": {
        "en": "Paste community report text", "kn": "ಸಮುದಾಯ ವರದಿ ಪಠ್ಯವನ್ನು ಅಂಟಿಸಿ", "hi": "सामुदायिक रिपोर्ट टेक्स्ट पेस्ट करें",
    },
    "analyze_pasted_text_btn": {"en": "Analyze pasted text", "kn": "ಅಂಟಿಸಿದ ಪಠ್ಯ ವಿಶ್ಲೇಷಿಸಿ", "hi": "पेस्ट किए गए टेक्स्ट का विश्लेषण करें"},
    "text_captured": {"en": "Text captured.", "kn": "ಪಠ್ಯ ಸೆರೆಹಿಡಿಯಲಾಗಿದೆ.", "hi": "टेक्स्ट कैप्चर हो गया।"},
    "detected_columns_expander": {"en": "🔍 Detected columns", "kn": "🔍 ಪತ್ತೆಯಾದ ಕಾಲಮ್‌ಗಳು", "hi": "🔍 पहचाने गए कॉलम"},
    "value_based": {"en": "value-based", "kn": "ಮೌಲ್ಯ-ಆಧಾರಿತ", "hi": "मान-आधारित"},
    "pct_match": {"en": "{score} match", "kn": "{score} ಹೊಂದಾಣಿಕೆ", "hi": "{score} मिलान"},
    "domain_framing_heading": {"en": "2. Domain framing", "kn": "2. ಡೊಮೇನ್ ಚೌಕಟ್ಟು", "hi": "2. डोमेन फ़्रेमिंग"},
    "ai_status_heading": {"en": "3. AI status", "kn": "3. AI ಸ್ಥಿತಿ", "hi": "3. AI स्थिति"},
    "gemini_offline_warning": {
        "en": "Gemini offline — using local fallback.",
        "kn": "Gemini ಆಫ್‌ಲೈನ್ ಆಗಿದೆ — ಸ್ಥಳೀಯ ಫಾಲ್‌ಬ್ಯಾಕ್ ಬಳಸಲಾಗುತ್ತಿದೆ.",
        "hi": "Gemini ऑफ़लाइन है — स्थानीय फ़ॉलबैक का उपयोग किया जा रहा है।",
    },
    "brief_history_heading": {"en": "4. Brief history", "kn": "4. ಸಂಕ್ಷಿಪ್ತ ಇತಿಹಾಸ", "hi": "4. ब्रीफ़ इतिहास"},
    "briefs_available": {
        "en": "{count} brief{s} available", "kn": "{count} ಸಂಕ್ಷಿಪ್ತ ವರದಿಗಳು ಲಭ್ಯ", "hi": "{count} ब्रीफ़ उपलब्ध",
    },
    "briefs_available_capped": {
        "en": "{count}+ briefs available", "kn": "{count}+ ಸಂಕ್ಷಿಪ್ತ ವರದಿಗಳು ಲಭ್ಯ", "hi": "{count}+ ब्रीफ़ उपलब्ध",
    },
    "brief_history_unavailable": {
        "en": "Unavailable this session — briefs won't be saved",
        "kn": "ಈ ಸೆಶನ್‌ನಲ್ಲಿ ಲಭ್ಯವಿಲ್ಲ — ಸಂಕ್ಷಿಪ್ತ ವರದಿಗಳನ್ನು ಉಳಿಸಲಾಗುವುದಿಲ್ಲ",
        "hi": "इस सत्र में अनुपलब्ध — ब्रीफ़ सहेजे नहीं जाएँगे",
    },
    "session_heading": {"en": "5. Session", "kn": "5. ಸೆಶನ್", "hi": "5. सत्र"},
    "session_active": {
        "en": "Reload-safe session active", "kn": "ಮರುಲೋಡ್-ಸುರಕ್ಷಿತ ಸೆಶನ್ ಸಕ್ರಿಯವಾಗಿದೆ", "hi": "रीलोड-सुरक्षित सत्र सक्रिय है",
    },
    "session_unavailable": {
        "en": "Unavailable this session — a refresh will reset your data",
        "kn": "ಈ ಸೆಶನ್‌ನಲ್ಲಿ ಲಭ್ಯವಿಲ್ಲ — ರಿಫ್ರೆಶ್ ಮಾಡಿದರೆ ನಿಮ್ಮ ಡೇಟಾ ಮರುಹೊಂದಿಸಲ್ಪಡುತ್ತದೆ",
        "hi": "इस सत्र में अनुपलब्ध — रीफ़्रेश करने पर आपका डेटा रीसेट हो जाएगा",
    },
    "sidebar_footer": {
        "en": "Built with Streamlit + Gemini on Google Cloud Run.",
        "kn": "Google Cloud Run ನಲ್ಲಿ Streamlit + Gemini ಬಳಸಿ ನಿರ್ಮಿಸಲಾಗಿದೆ.",
        "hi": "Google Cloud Run पर Streamlit + Gemini से बनाया गया।",
    },
    "language_label": {"en": "Language", "kn": "ಭಾಷೆ", "hi": "भाषा"},

    # ---------------------------------------------------------------- domain options
    "domain_citizen_complaints": {"en": "citizen complaints", "kn": "ನಾಗರಿಕ ದೂರುಗಳು", "hi": "नागरिक शिकायतें"},
    "domain_waste_sanitation": {"en": "waste & sanitation", "kn": "ತ್ಯಾಜ್ಯ ಮತ್ತು ನೈರ್ಮಲ್ಯ", "hi": "कचरा और स्वच्छता"},
    "domain_water_supply": {"en": "water supply", "kn": "ನೀರು ಸರಬರಾಜು", "hi": "जल आपूर्ति"},
    "domain_road_infra": {"en": "road & infrastructure", "kn": "ರಸ್ತೆ ಮತ್ತು ಮೂಲಸೌಕರ್ಯ", "hi": "सड़क और बुनियादी ढांचा"},
    "domain_public_health": {"en": "public health access", "kn": "ಸಾರ್ವಜನಿಕ ಆರೋಗ್ಯ ಪ್ರವೇಶ", "hi": "सार्वजनिक स्वास्थ्य पहुँच"},
    "domain_neighborhood_wellness": {"en": "neighborhood wellness", "kn": "ನೆರೆಹೊರೆಯ ಯೋಗಕ್ಷೇಮ", "hi": "मोहल्ला कल्याण"},

    # ---------------------------------------------------------------- hero
    "hero_tagline": {
        "en": "Ask your community data anything — get patterns, anomalies, and decisions.",
        "kn": "ನಿಮ್ಮ ಸಮುದಾಯ ಡೇಟಾದ ಬಗ್ಗೆ ಏನು ಬೇಕಾದರೂ ಕೇಳಿ — ಮಾದರಿಗಳು, ಅಸಂಗತತೆಗಳು ಮತ್ತು ನಿರ್ಧಾರಗಳನ್ನು ಪಡೆಯಿರಿ.",
        "hi": "अपने सामुदायिक डेटा से कुछ भी पूछें — पैटर्न, विसंगतियाँ और निर्णय पाएँ।",
    },
    "hero_tagline_bold": {
        "en": "Not just answers — better decisions.",
        "kn": "ಕೇವಲ ಉತ್ತರಗಳಲ್ಲ — ಉತ್ತಮ ನಿರ್ಧಾರಗಳು.",
        "hi": "सिर्फ़ जवाब नहीं — बेहतर फ़ैसले।",
    },
    "badge_nlp": {"en": "Natural-language analytics", "kn": "ಸ್ವಾಭಾವಿಕ-ಭಾಷೆ ವಿಶ್ಲೇಷಣೆ", "hi": "प्राकृतिक-भाषा विश्लेषण"},
    "badge_anomaly": {"en": "Anomaly detection", "kn": "ಅಸಂಗತತೆ ಪತ್ತೆ", "hi": "विसंगति पहचान"},
    "badge_action": {"en": "Action generator", "kn": "ಕ್ರಿಯಾ ಜನರೇಟರ್", "hi": "कार्रवाई जनरेटर"},
    "badge_gemini": {"en": "Gemini-powered", "kn": "Gemini-ಚಾಲಿತ", "hi": "Gemini-संचालित"},
    "empty_state_info": {
        "en": "👈 Start by clicking **Load demo dataset** in the sidebar, or upload your own "
              "CSV/JSON/PDF. CivicPulse turns raw community data into a decision-ready snapshot.",
        "kn": "👈 ಸೈಡ್‌ಬಾರ್‌ನಲ್ಲಿ **ಡೆಮೊ ಡೇಟಾಸೆಟ್ ಲೋಡ್ ಮಾಡಿ** ಕ್ಲಿಕ್ ಮಾಡುವ ಮೂಲಕ ಪ್ರಾರಂಭಿಸಿ, ಅಥವಾ ನಿಮ್ಮ ಸ್ವಂತ "
              "CSV/JSON/PDF ಅಪ್‌ಲೋಡ್ ಮಾಡಿ. CivicPulse ಕಚ್ಚಾ ಸಮುದಾಯ ಡೇಟಾವನ್ನು ನಿರ್ಧಾರ-ಸಿದ್ಧ ಸ್ನ್ಯಾಪ್‌ಶಾಟ್ ಆಗಿ ಪರಿವರ್ತಿಸುತ್ತದೆ.",
        "hi": "👈 साइडबार में **डेमो डेटासेट लोड करें** पर क्लिक करके शुरू करें, या अपनी खुद की "
              "CSV/JSON/PDF अपलोड करें। CivicPulse कच्चे सामुदायिक डेटा को निर्णय-तैयार स्नैपशॉट में बदल देता है।",
    },
    "feature_card_1_title": {"en": "📊 Deterministic first", "kn": "📊 ನಿರ್ಣಾಯಕ ಮೊದಲು", "hi": "📊 निर्धारक पहले"},
    "feature_card_1_body": {
        "en": "Python computes counts, trends & anomalies before any AI call — cheap and reliable.",
        "kn": "ಯಾವುದೇ AI ಕರೆಗಿಂತ ಮೊದಲು Python ಎಣಿಕೆಗಳು, ಪ್ರವೃತ್ತಿಗಳು ಮತ್ತು ಅಸಂಗತತೆಗಳನ್ನು ಲೆಕ್ಕಿಸುತ್ತದೆ — ಅಗ್ಗ ಮತ್ತು ವಿಶ್ವಾಸಾರ್ಹ.",
        "hi": "किसी भी AI कॉल से पहले Python गिनती, रुझान और विसंगतियों की गणना करता है — सस्ता और विश्वसनीय।",
    },
    "feature_card_2_title": {"en": "🤖 Gemini explains", "kn": "🤖 Gemini ವಿವರಿಸುತ್ತದೆ", "hi": "🤖 Gemini समझाता है"},
    "feature_card_2_body": {
        "en": "Gemini turns numbers into plain-language decisions.",
        "kn": "Gemini ಸಂಖ್ಯೆಗಳನ್ನು ಸರಳ-ಭಾಷೆಯ ನಿರ್ಧಾರಗಳಾಗಿ ಪರಿವರ್ತಿಸುತ್ತದೆ.",
        "hi": "Gemini संख्याओं को सरल-भाषा के निर्णयों में बदल देता है।",
    },
    "feature_card_3_title": {"en": "🎯 Decision Scoreboard", "kn": "🎯 ನಿರ್ಧಾರ ಸ್ಕೋರ್‌ಬೋರ್ಡ್", "hi": "🎯 निर्णय स्कोरबोर्ड"},
    "feature_card_3_body": {
        "en": "Urgency, impact & confidence scores so teams know what to do next.",
        "kn": "ತುರ್ತು, ಪರಿಣಾಮ ಮತ್ತು ವಿಶ್ವಾಸ ಸ್ಕೋರ್‌ಗಳು ತಂಡಗಳಿಗೆ ಮುಂದೆ ಏನು ಮಾಡಬೇಕೆಂದು ತಿಳಿಸುತ್ತವೆ.",
        "hi": "तात्कालिकता, प्रभाव और विश्वास स्कोर ताकि टीमों को पता चले कि आगे क्या करना है।",
    },

    # ---------------------------------------------------------------- tabs
    "tab_overview": {"en": "📊 Overview", "kn": "📊 ಅವಲೋಕನ", "hi": "📊 अवलोकन"},
    "tab_ask_ai": {"en": "💬 Ask AI", "kn": "💬 AI ಕೇಳಿ", "hi": "💬 AI से पूछें"},
    "tab_anomalies": {"en": "🚨 Anomalies", "kn": "🚨 ಅಸಂಗತತೆಗಳು", "hi": "🚨 विसंगतियाँ"},
    "tab_recommendations": {"en": "✅ Recommendations", "kn": "✅ ಶಿಫಾರಸುಗಳು", "hi": "✅ सिफ़ारिशें"},
    "tab_about": {"en": "ℹ️ About", "kn": "ℹ️ ಬಗ್ಗೆ", "hi": "ℹ️ जानकारी"},

    # ---------------------------------------------------------------- overview
    "unstructured_warning": {
        "en": "This source is unstructured (text/PDF). Head to **Ask AI** or **Recommendations** for an AI summary of the content.",
        "kn": "ಈ ಮೂಲವು ರಚನೆಯಿಲ್ಲದ್ದಾಗಿದೆ (ಪಠ್ಯ/PDF). ವಿಷಯದ AI ಸಾರಾಂಶಕ್ಕಾಗಿ **AI ಕೇಳಿ** ಅಥವಾ **ಶಿಫಾರಸುಗಳು** ಗೆ ಹೋಗಿ.",
        "hi": "यह स्रोत असंरचित है (टेक्स्ट/PDF)। सामग्री के AI सारांश के लिए **AI से पूछें** या **सिफ़ारिशें** पर जाएँ।",
    },
    "community_snapshot": {"en": "Community Snapshot", "kn": "ಸಮುದಾಯ ಸ್ನ್ಯಾಪ್‌ಶಾಟ್", "hi": "सामुदायिक स्नैपशॉट"},
    "card_records": {"en": "📄 Records", "kn": "📄 ದಾಖಲೆಗಳು", "hi": "📄 रिकॉर्ड"},
    "card_top_hotspot": {"en": "📍 Top hotspot", "kn": "📍 ಟಾಪ್ ಹಾಟ್‌ಸ್ಪಾಟ್", "hi": "📍 शीर्ष हॉटस्पॉट"},
    "card_most_affected": {"en": "Most-affected area", "kn": "ಅತಿ ಹೆಚ್ಚು ಬಾಧಿತ ಪ್ರದೇಶ", "hi": "सबसे प्रभावित क्षेत्र"},
    "card_leading_issue": {"en": "⚠️ Leading issue", "kn": "⚠️ ಪ್ರಮುಖ ಸಮಸ್ಯೆ", "hi": "⚠️ प्रमुख समस्या"},
    "card_top_category": {"en": "Top category", "kn": "ಟಾಪ್ ವರ್ಗ", "hi": "शीर्ष श्रेणी"},
    "card_weekly_trend": {"en": "📈 Weekly trend", "kn": "📈 ಸಾಪ್ತಾಹಿಕ ಪ್ರವೃತ್ತಿ", "hi": "📈 साप्ताहिक रुझान"},
    "vs_prior_week": {"en": "{pct} vs prior week", "kn": "ಹಿಂದಿನ ವಾರಕ್ಕೆ ಹೋಲಿಸಿದರೆ {pct}", "hi": "पिछले सप्ताह की तुलना में {pct}"},
    "trend_rising": {"en": "Rising", "kn": "ಏರುತ್ತಿದೆ", "hi": "बढ़ रहा है"},
    "trend_falling": {"en": "Falling", "kn": "ಇಳಿಯುತ್ತಿದೆ", "hi": "घट रहा है"},
    "trend_flat": {"en": "Flat", "kn": "ಸ್ಥಿರ", "hi": "स्थिर"},
    "decision_scoreboard": {"en": "Decision Scoreboard", "kn": "ನಿರ್ಧಾರ ಸ್ಕೋರ್‌ಬೋರ್ಡ್", "hi": "निर्णय स्कोरबोर्ड"},
    "pill_urgency": {"en": "⚠️ Urgency", "kn": "⚠️ ತುರ್ತು", "hi": "⚠️ तात्कालिकता"},
    "pill_impact": {"en": "📈 Impact", "kn": "📈 ಪರಿಣಾಮ", "hi": "📈 प्रभाव"},
    "pill_confidence": {"en": "🛡️ Confidence", "kn": "🛡️ ವಿಶ್ವಾಸ", "hi": "🛡️ विश्वास"},
    "pill_severity": {"en": "🌡️ Severity", "kn": "🌡️ ತೀವ್ರತೆ", "hi": "🌡️ गंभीरता"},
    "open_case_rate": {
        "en": "Open/unresolved case rate: **{pct}%**",
        "kn": "ತೆರೆದ/ಬಗೆಹರಿಯದ ಪ್ರಕರಣ ದರ: **{pct}%**",
        "hi": "खुले/अनसुलझे मामलों की दर: **{pct}%**",
    },
    "why_confidence_expander": {"en": "Why this confidence score?", "kn": "ಈ ವಿಶ್ವಾಸ ಸ್ಕೋರ್ ಏಕೆ?", "hi": "यह विश्वास स्कोर क्यों?"},
    "confidence_breakdown_caption": {
        "en": "Sample size: **{n}**/40 · Recency: **{r}**/30 · Stability: **{s}**/30 "
              "— more reports, more recent data, and a steadier day-to-day pattern all raise confidence.",
        "kn": "ಮಾದರಿ ಗಾತ್ರ: **{n}**/40 · ಇತ್ತೀಚಿನತೆ: **{r}**/30 · ಸ್ಥಿರತೆ: **{s}**/30 "
              "— ಹೆಚ್ಚು ವರದಿಗಳು, ಹೆಚ್ಚು ಇತ್ತೀಚಿನ ಡೇಟಾ, ಮತ್ತು ಸ್ಥಿರವಾದ ದೈನಂದಿನ ಮಾದರಿ ಎಲ್ಲವೂ ವಿಶ್ವಾಸವನ್ನು ಹೆಚ್ಚಿಸುತ್ತವೆ.",
        "hi": "नमूना आकार: **{n}**/40 · हालिया: **{r}**/30 · स्थिरता: **{s}**/30 "
              "— अधिक रिपोर्ट, अधिक हालिया डेटा, और स्थिर दैनिक पैटर्न — सभी विश्वास बढ़ाते हैं।",
    },
    "hotspot_map_title": {"en": "🗺️ Hotspot map", "kn": "🗺️ ಹಾಟ್‌ಸ್ಪಾಟ್ ನಕ್ಷೆ", "hi": "🗺️ हॉटस्पॉट मानचित्र"},
    "hotspot_map_caption": {
        "en": "Blends volume, severity, and unresolved backlog into one score per area.",
        "kn": "ಪ್ರಮಾಣ, ತೀವ್ರತೆ ಮತ್ತು ಬಗೆಹರಿಯದ ಬಾಕಿಯನ್ನು ಪ್ರತಿ ಪ್ರದೇಶಕ್ಕೆ ಒಂದು ಸ್ಕೋರ್‌ಗೆ ಸಂಯೋಜಿಸುತ್ತದೆ.",
        "hi": "मात्रा, गंभीरता, और अनसुलझे बैकलॉग को प्रति क्षेत्र एक स्कोर में मिलाता है।",
    },
    "map_scroll_caption": {
        "en": "🖱️ Scroll or pinch to zoom, drag to pan, click a legend item to filter by coordinate source.",
        "kn": "🖱️ ಝೂಮ್ ಮಾಡಲು ಸ್ಕ್ರಾಲ್ ಅಥವಾ ಪಿಂಚ್ ಮಾಡಿ, ಪ್ಯಾನ್ ಮಾಡಲು ಡ್ರ್ಯಾಗ್ ಮಾಡಿ, ನಿರ್ದೇಶಾಂಕ ಮೂಲದ ಪ್ರಕಾರ ಫಿಲ್ಟರ್ ಮಾಡಲು ಲೆಜೆಂಡ್ ಐಟಂ ಕ್ಲಿಕ್ ಮಾಡಿ.",
        "hi": "🖱️ ज़ूम करने के लिए स्क्रॉल या पिंच करें, पैन करने के लिए खींचें, निर्देशांक स्रोत के अनुसार फ़िल्टर करने के लिए लेजेंड आइटम पर क्लिक करें।",
    },
    "map_coord_caption": {
        "en": "📍 {n_real}/{n_total} areas use real BBMP ward coordinates (OpenCity ward office dataset). "
              "{n_placeholder} unmatched area(s) use a deterministic placeholder position instead of a guess.",
        "kn": "📍 {n_real}/{n_total} ಪ್ರದೇಶಗಳು ನಿಜವಾದ BBMP ವಾರ್ಡ್ ನಿರ್ದೇಶಾಂಕಗಳನ್ನು ಬಳಸುತ್ತವೆ (OpenCity ವಾರ್ಡ್ ಕಚೇರಿ ಡೇಟಾಸೆಟ್). "
              "{n_placeholder} ಹೊಂದಾಣಿಕೆಯಾಗದ ಪ್ರದೇಶ(ಗಳು) ಊಹೆಯ ಬದಲು ನಿರ್ಣಾಯಕ ಪ್ಲೇಸ್‌ಹೋಲ್ಡರ್ ಸ್ಥಾನವನ್ನು ಬಳಸುತ್ತವೆ.",
        "hi": "📍 {n_real}/{n_total} क्षेत्र वास्तविक BBMP वार्ड निर्देशांक का उपयोग करते हैं (OpenCity वार्ड कार्यालय डेटासेट)। "
              "{n_placeholder} बेमेल क्षेत्र अनुमान के बजाय एक निर्धारक प्लेसहोल्डर स्थिति का उपयोग करते हैं।",
    },
    "map_insufficient_data": {
        "en": "Not enough area data to build a hotspot map.",
        "kn": "ಹಾಟ್‌ಸ್ಪಾಟ್ ನಕ್ಷೆ ನಿರ್ಮಿಸಲು ಸಾಕಷ್ಟು ಪ್ರದೇಶ ಡೇಟಾ ಇಲ್ಲ.",
        "hi": "हॉटस्पॉट मानचित्र बनाने के लिए पर्याप्त क्षेत्र डेटा नहीं है।",
    },
    "coord_real_ward": {"en": "Real BBMP ward location", "kn": "ನಿಜವಾದ BBMP ವಾರ್ಡ್ ಸ್ಥಳ", "hi": "वास्तविक BBMP वार्ड स्थान"},
    "coord_provided": {"en": "Provided coordinates", "kn": "ಒದಗಿಸಿದ ನಿರ್ದೇಶಾಂಕಗಳು", "hi": "प्रदत्त निर्देशांक"},
    "coord_placeholder": {"en": "Placeholder (unmatched)", "kn": "ಪ್ಲೇಸ್‌ಹೋಲ್ಡರ್ (ಹೊಂದಾಣಿಕೆಯಾಗದ)", "hi": "प्लेसहोल्डर (बेमेल)"},
    "forecast_title": {"en": "📈 7-day forecast", "kn": "📈 7-ದಿನದ ಮುನ್ಸೂಚನೆ", "hi": "📈 7-दिन का पूर्वानुमान"},
    "forecast_caption": {
        "en": "Trend-aware forecasting (Holt's linear method) — predicts likely spikes before they happen, not just after.",
        "kn": "ಪ್ರವೃತ್ತಿ-ಜಾಗೃತ ಮುನ್ಸೂಚನೆ (Holt's ರೇಖೀಯ ವಿಧಾನ) — ಸಂಭವನೀಯ ಏರಿಕೆಗಳನ್ನು ಸಂಭವಿಸುವ ಮೊದಲೇ ಊಹಿಸುತ್ತದೆ, ನಂತರವಲ್ಲ.",
        "hi": "रुझान-जागरूक पूर्वानुमान (Holt की रैखिक विधि) — संभावित उछाल को होने से पहले ही बताता है, बाद में नहीं।",
    },
    "forecast_row_detail": {
        "en": "{last}/day → {forecast}/day predicted",
        "kn": "{last}/ದಿನ → {forecast}/ದಿನ ಮುನ್ಸೂಚಿಸಲಾಗಿದೆ",
        "hi": "{last}/दिन → {forecast}/दिन अनुमानित",
    },
    "forecast_insufficient": {
        "en": "Not enough daily history yet to forecast (needs 7+ days of dated records).",
        "kn": "ಮುನ್ಸೂಚಿಸಲು ಇನ್ನೂ ಸಾಕಷ್ಟು ದೈನಂದಿನ ಇತಿಹಾಸವಿಲ್ಲ (7+ ದಿನಗಳ ದಿನಾಂಕ ದಾಖಲೆಗಳು ಬೇಕು).",
        "hi": "पूर्वानुमान के लिए अभी पर्याप्त दैनिक इतिहास नहीं है (7+ दिनों के दिनांकित रिकॉर्ड चाहिए)।",
    },
    "chart_complaints_by_area": {"en": "Complaints by area", "kn": "ಪ್ರದೇಶವಾರು ದೂರುಗಳು", "hi": "क्षेत्र अनुसार शिकायतें"},
    "chart_complaints_axis": {"en": "Complaints", "kn": "ದೂರುಗಳು", "hi": "शिकायतें"},
    "chart_weekly_trend": {"en": "Weekly volume trend", "kn": "ಸಾಪ್ತಾಹಿಕ ಪ್ರಮಾಣ ಪ್ರವೃತ್ತಿ", "hi": "साप्ताहिक मात्रा रुझान"},
    "chart_category_mix": {"en": "Category mix", "kn": "ವರ್ಗ ಮಿಶ್ರಣ", "hi": "श्रेणी मिश्रण"},
    "chart_severity_distribution": {"en": "Severity distribution", "kn": "ತೀವ್ರತೆ ವಿತರಣೆ", "hi": "गंभीरता वितरण"},
    "chart_count_axis": {"en": "Count", "kn": "ಎಣಿಕೆ", "hi": "गणना"},
    "preview_raw_data": {"en": "Preview raw data", "kn": "ಕಚ್ಚಾ ಡೇಟಾ ಪೂರ್ವವೀಕ್ಷಿಸಿ", "hi": "कच्चा डेटा पूर्वावलोकन करें"},

    # ---------------------------------------------------------------- ask AI
    "ask_suggested_questions": {"en": "💡 Suggested questions", "kn": "💡 ಸೂಚಿಸಿದ ಪ್ರಶ್ನೆಗಳು", "hi": "💡 सुझाए गए प्रश्न"},
    "starter_q1": {
        "en": "Which area has the most urgent issues?",
        "kn": "ಯಾವ ಪ್ರದೇಶದಲ್ಲಿ ಅತಿ ಹೆಚ್ಚು ತುರ್ತು ಸಮಸ್ಯೆಗಳಿವೆ?",
        "hi": "किस क्षेत्र में सबसे अधिक तात्कालिक समस्याएँ हैं?",
    },
    "starter_q2": {
        "en": "What patterns are increasing this week?",
        "kn": "ಈ ವಾರ ಯಾವ ಮಾದರಿಗಳು ಹೆಚ್ಚುತ್ತಿವೆ?",
        "hi": "इस सप्ताह कौन से पैटर्न बढ़ रहे हैं?",
    },
    "starter_q3": {
        "en": "Compare the top two hotspot areas.",
        "kn": "ಟಾಪ್ ಎರಡು ಹಾಟ್‌ಸ್ಪಾಟ್ ಪ್ರದೇಶಗಳನ್ನು ಹೋಲಿಸಿ.",
        "hi": "शीर्ष दो हॉटस्पॉट क्षेत्रों की तुलना करें।",
    },
    "starter_q4": {
        "en": "What should we prioritize this week?",
        "kn": "ಈ ವಾರ ನಾವು ಯಾವುದಕ್ಕೆ ಆದ್ಯತೆ ನೀಡಬೇಕು?",
        "hi": "इस सप्ताह हमें किसे प्राथमिकता देनी चाहिए?",
    },
    "new_conversation_btn": {"en": "🔄 Start a new conversation", "kn": "🔄 ಹೊಸ ಸಂಭಾಷಣೆ ಆರಂಭಿಸಿ", "hi": "🔄 नई बातचीत शुरू करें"},
    "conversation_title": {"en": "Conversation", "kn": "ಸಂಭಾಷಣೆ", "hi": "बातचीत"},
    "ask_ai_caption": {
        "en": "Grounded strictly in your data — the model never invents numbers. "
              "Keep asking follow-ups; CivicPulse remembers the conversation.",
        "kn": "ಕಟ್ಟುನಿಟ್ಟಾಗಿ ನಿಮ್ಮ ಡೇಟಾದಲ್ಲಿ ಆಧಾರಿತವಾಗಿದೆ — ಮಾದರಿಯು ಎಂದಿಗೂ ಸಂಖ್ಯೆಗಳನ್ನು ಸೃಷ್ಟಿಸುವುದಿಲ್ಲ. "
              "ಮುಂದುವರಿದ ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳುತ್ತಿರಿ; CivicPulse ಸಂಭಾಷಣೆಯನ್ನು ನೆನಪಿಟ್ಟುಕೊಳ್ಳುತ್ತದೆ.",
        "hi": "पूरी तरह से आपके डेटा पर आधारित — मॉडल कभी भी संख्याएँ नहीं गढ़ता। "
              "फ़ॉलो-अप सवाल पूछते रहें; CivicPulse बातचीत को याद रखता है।",
    },
    "ask_ai_empty_hint": {
        "en": "💡 Tap a suggested question on the left, or type your own below.",
        "kn": "💡 ಎಡಭಾಗದಲ್ಲಿ ಸೂಚಿಸಿದ ಪ್ರಶ್ನೆಯನ್ನು ಟ್ಯಾಪ್ ಮಾಡಿ, ಅಥವಾ ಕೆಳಗೆ ನಿಮ್ಮದೇ ಆದದ್ದನ್ನು ಟೈಪ್ ಮಾಡಿ.",
        "hi": "💡 बाईं ओर सुझाया गया प्रश्न टैप करें, या नीचे अपना खुद का टाइप करें।",
    },
    "chat_input_placeholder": {
        "en": "Ask a question about your data...", "kn": "ನಿಮ್ಮ ಡೇಟಾದ ಬಗ್ಗೆ ಪ್ರಶ್ನೆ ಕೇಳಿ...", "hi": "अपने डेटा के बारे में प्रश्न पूछें...",
    },
    "gemini_querying_spinner": {
        "en": "Gemini is querying the data...", "kn": "Gemini ಡೇಟಾವನ್ನು ಪ್ರಶ್ನಿಸುತ್ತಿದೆ...", "hi": "Gemini डेटा से प्रश्न कर रहा है...",
    },
    "analyzing_spinner": {"en": "Analyzing...", "kn": "ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...", "hi": "विश्लेषण किया जा रहा है..."},
    "sender_you": {"en": "You", "kn": "ನೀವು", "hi": "आप"},
    "sender_civicpulse": {
        "en": "CivicPulse AI (Gemini)", "kn": "CivicPulse AI (Gemini)", "hi": "CivicPulse AI (Gemini)",
    },
    "chat_history_title": {"en": "🕘 Chat history", "kn": "🕘 ಚಾಟ್ ಇತಿಹಾಸ", "hi": "🕘 चैट इतिहास"},
    "chat_history_empty": {"en": "No questions yet this session.", "kn": "ಈ ಸೆಶನ್‌ನಲ್ಲಿ ಇನ್ನೂ ಪ್ರಶ್ನೆಗಳಿಲ್ಲ.", "hi": "इस सत्र में अभी तक कोई प्रश्न नहीं।"},
    "trust_card_title": {"en": "Ask AI, get grounded answers.", "kn": "AI ಅನ್ನು ಕೇಳಿ, ಆಧಾರಿತ ಉತ್ತರಗಳನ್ನು ಪಡೆಯಿರಿ.", "hi": "AI से पूछें, प्रमाणित उत्तर पाएँ।"},
    "trust_card_body": {
        "en": "CivicPulse AI uses your data + real queries. No guessing. No made-up numbers.",
        "kn": "CivicPulse AI ನಿಮ್ಮ ಡೇಟಾ + ನೈಜ ಪ್ರಶ್ನೆಗಳನ್ನು ಬಳಸುತ್ತದೆ. ಊಹೆ ಇಲ್ಲ. ಕಟ್ಟುಕಥೆಯ ಸಂಖ್ಯೆಗಳಿಲ್ಲ.",
        "hi": "CivicPulse AI आपके डेटा + वास्तविक प्रश्नों का उपयोग करता है। कोई अनुमान नहीं। कोई गढ़ी हुई संख्या नहीं।",
    },
    "offline_fallback_caption": {
        "en": "⚠️ Offline fallback answer (Gemini not called).",
        "kn": "⚠️ ಆಫ್‌ಲೈನ್ ಫಾಲ್‌ಬ್ಯಾಕ್ ಉತ್ತರ (Gemini ಕರೆ ಮಾಡಲಾಗಿಲ್ಲ).",
        "hi": "⚠️ ऑफ़लाइन फ़ॉलबैक उत्तर (Gemini को कॉल नहीं किया गया)।",
    },
    "field_whats_happening": {"en": "What's happening.", "kn": "ಏನಾಗುತ್ತಿದೆ.", "hi": "क्या हो रहा है।"},
    "field_why_it_matters": {"en": "Why it matters.", "kn": "ಇದು ಏಕೆ ಮುಖ್ಯ.", "hi": "यह क्यों मायने रखता है।"},
    "field_where": {"en": "Where.", "kn": "ಎಲ್ಲಿ.", "hi": "कहाँ।"},
    "field_recommended_next_step": {
        "en": "Recommended next step.", "kn": "ಶಿಫಾರಸು ಮಾಡಿದ ಮುಂದಿನ ಹಂತ.", "hi": "अनुशंसित अगला कदम।",
    },
    "not_enough_data": {"en": "not enough data", "kn": "ಸಾಕಷ್ಟು ಡೇಟಾ ಇಲ್ಲ", "hi": "पर्याप्त डेटा नहीं"},
    "tool_trace_expander": {
        "en": "🔧 How CivicPulse checked this ({n} data quer{y})",
        "kn": "🔧 CivicPulse ಇದನ್ನು ಹೇಗೆ ಪರಿಶೀಲಿಸಿತು ({n} ಡೇಟಾ ಪ್ರಶ್ನೆಗಳು)",
        "hi": "🔧 CivicPulse ने इसे कैसे जाँचा ({n} डेटा क्वेरी)",
    },
    "tool_trace_caption": {
        "en": "Every number above came from one of these real queries against your dataset — "
              "Gemini chose what to look up, not what the numbers say.",
        "kn": "ಮೇಲಿನ ಪ್ರತಿಯೊಂದು ಸಂಖ್ಯೆಯೂ ನಿಮ್ಮ ಡೇಟಾಸೆಟ್ ವಿರುದ್ಧದ ಈ ನೈಜ ಪ್ರಶ್ನೆಗಳಲ್ಲಿ ಒಂದರಿಂದ ಬಂದಿದೆ — "
              "Gemini ಏನನ್ನು ಹುಡುಕಬೇಕೆಂದು ಆರಿಸಿತು, ಸಂಖ್ಯೆಗಳು ಏನು ಹೇಳುತ್ತವೆ ಎಂಬುದನ್ನಲ್ಲ.",
        "hi": "ऊपर की हर संख्या आपके डेटासेट पर चलाई गई इन वास्तविक क्वेरी में से किसी एक से आई है — "
              "Gemini ने चुना कि क्या देखना है, संख्याएँ क्या कहती हैं यह नहीं।",
    },
    "tool_trace_matching_records": {
        "en": "{rc} matching record{s}", "kn": "{rc} ಹೊಂದಾಣಿಕೆಯ ದಾಖಲೆಗಳು", "hi": "{rc} मिलान रिकॉर्ड",
    },
    "tool_trace_full_snapshot": {
        "en": "full dataset snapshot", "kn": "ಪೂರ್ಣ ಡೇಟಾಸೆಟ್ ಸ್ನ್ಯಾಪ್‌ಶಾಟ್", "hi": "पूर्ण डेटासेट स्नैपशॉट",
    },

    # ---------------------------------------------------------------- anomalies
    "anomalies_title": {"en": "🚨 Emerging anomalies", "kn": "🚨 ಉದಯೋನ್ಮುಖ ಅಸಂಗತತೆಗಳು", "hi": "🚨 उभरती विसंगतियाँ"},
    "anomalies_caption": {
        "en": "Flagged by simple statistical thresholds (σ, \"sigma\" ≥ 1.5) — transparent and cheap. "
              "**What's a σ score?** It's how far a number is from what's typical, measured in "
              "\"standard deviations.\" σ ≈ 1.5–2 is worth a look; above ~2.5–3 is a real outlier, "
              "not just normal day-to-day variation.",
        "kn": "ಸರಳ ಸಂಖ್ಯಾಶಾಸ್ತ್ರೀಯ ಮಿತಿಗಳಿಂದ ಗುರುತಿಸಲಾಗಿದೆ (σ, \"ಸಿಗ್ಮಾ\" ≥ 1.5) — ಪಾರದರ್ಶಕ ಮತ್ತು ಅಗ್ಗ. "
              "**σ ಸ್ಕೋರ್ ಎಂದರೇನು?** ಒಂದು ಸಂಖ್ಯೆಯು ಸಾಮಾನ್ಯದಿಂದ ಎಷ್ಟು ದೂರವಿದೆ ಎಂಬುದನ್ನು ಇದು \"ಸ್ಟ್ಯಾಂಡರ್ಡ್ ಡಿವಿಯೇಶನ್\"ಗಳಲ್ಲಿ "
              "ಅಳೆಯುತ್ತದೆ. σ ≈ 1.5–2 ಗಮನಿಸಬೇಕಾದದ್ದು; ~2.5–3 ಗಿಂತ ಹೆಚ್ಚಿನದು ನಿಜವಾದ ಹೊರಬೆಲೆ, ಸಾಮಾನ್ಯ ದೈನಂದಿನ ವ್ಯತ್ಯಾಸವಲ್ಲ.",
        "hi": "सरल सांख्यिकीय सीमाओं द्वारा चिह्नित (σ, \"सिग्मा\" ≥ 1.5) — पारदर्शी और सस्ता। "
              "**σ स्कोर क्या है?** यह मापता है कि कोई संख्या सामान्य से कितनी दूर है, \"स्टैंडर्ड डिविएशन\" में। "
              "σ ≈ 1.5–2 देखने लायक है; ~2.5–3 से ऊपर एक वास्तविक आउटलायर है, सामान्य दैनिक बदलाव नहीं।",
    },
    "anomalies_needs_structured": {
        "en": "Anomaly detection needs structured (CSV/JSON) data.",
        "kn": "ಅಸಂಗತತೆ ಪತ್ತೆಗೆ ರಚನಾತ್ಮಕ (CSV/JSON) ಡೇಟಾ ಬೇಕು.",
        "hi": "विसंगति पहचान के लिए संरचित (CSV/JSON) डेटा चाहिए।",
    },
    "anomalies_none": {
        "en": "No significant anomalies detected in this dataset.",
        "kn": "ಈ ಡೇಟಾಸೆಟ್‌ನಲ್ಲಿ ಯಾವುದೇ ಗಮನಾರ್ಹ ಅಸಂಗತತೆಗಳು ಪತ್ತೆಯಾಗಿಲ್ಲ.",
        "hi": "इस डेटासेट में कोई महत्वपूर्ण विसंगति नहीं मिली।",
    },
    "sigma_score_label": {"en": "σ score", "kn": "σ ಸ್ಕೋರ್", "hi": "σ स्कोर"},
    "dim_area": {"en": "area", "kn": "ಪ್ರದೇಶ", "hi": "क्षेत्र"},
    "dim_category": {"en": "category", "kn": "ವರ್ಗ", "hi": "श्रेणी"},
    "dim_time": {"en": "time", "kn": "ಸಮಯ", "hi": "समय"},
    "dim_complaint_type": {"en": "complaint type", "kn": "ದೂರು ಪ್ರಕಾರ", "hi": "शिकायत प्रकार"},
    "anomaly_meaning_area": {
        "en": "This area is drawing a disproportionate share of complaints — worth prioritizing a rapid-response team or a targeted infrastructure review there.",
        "kn": "ಈ ಪ್ರದೇಶವು ಅಸಮಾನ ಪ್ರಮಾಣದ ದೂರುಗಳನ್ನು ಪಡೆಯುತ್ತಿದೆ — ಅಲ್ಲಿ ತ್ವರಿತ-ಪ್ರತಿಕ್ರಿಯೆ ತಂಡ ಅಥವಾ ಗುರಿಪಡಿಸಿದ ಮೂಲಸೌಕರ್ಯ ಪರಿಶೀಲನೆಗೆ ಆದ್ಯತೆ ನೀಡುವುದು ಯೋಗ್ಯ.",
        "hi": "इस क्षेत्र में शिकायतों का असमान हिस्सा आ रहा है — वहाँ त्वरित-प्रतिक्रिया टीम या लक्षित बुनियादी ढांचा समीक्षा को प्राथमिकता देना उचित है।",
    },
    "anomaly_meaning_category": {
        "en": "This category is spiking well beyond its usual share — often points to a systemic issue in that service line, not scattered one-off incidents.",
        "kn": "ಈ ವರ್ಗವು ತನ್ನ ಸಾಮಾನ್ಯ ಪಾಲಿಗಿಂತ ಹೆಚ್ಚು ಏರುತ್ತಿದೆ — ಇದು ಸಾಮಾನ್ಯವಾಗಿ ಆ ಸೇವಾ ವಿಭಾಗದಲ್ಲಿ ವ್ಯವಸ್ಥಿತ ಸಮಸ್ಯೆಯನ್ನು ಸೂಚಿಸುತ್ತದೆ, ಚದುರಿದ ಒಂಟಿ ಘಟನೆಗಳಲ್ಲ.",
        "hi": "यह श्रेणी अपने सामान्य हिस्से से कहीं अधिक बढ़ रही है — यह अक्सर उस सेवा क्षेत्र में एक व्यवस्थित समस्या की ओर इशारा करता है, न कि बिखरी हुई अलग-अलग घटनाओं की।",
    },
    "anomaly_meaning_complaint_type": {
        "en": "This specific issue keeps recurring more than expected — worth investigating a shared root cause, like one faulty process, location, or vendor.",
        "kn": "ಈ ನಿರ್ದಿಷ್ಟ ಸಮಸ್ಯೆ ನಿರೀಕ್ಷೆಗಿಂತ ಹೆಚ್ಚಾಗಿ ಮರುಕಳಿಸುತ್ತಿದೆ — ಒಂದು ಹಂಚಿಕೆಯ ಮೂಲ ಕಾರಣವನ್ನು (ಒಂದು ದೋಷಪೂರ್ಣ ಪ್ರಕ್ರಿಯೆ, ಸ್ಥಳ, ಅಥವಾ ಮಾರಾಟಗಾರ) ತನಿಖೆ ಮಾಡುವುದು ಯೋಗ್ಯ.",
        "hi": "यह विशिष्ट समस्या अपेक्षा से अधिक बार दोहराई जा रही है — एक साझा मूल कारण (जैसे एक दोषपूर्ण प्रक्रिया, स्थान, या विक्रेता) की जांच करना उचित है।",
    },
    "anomaly_meaning_time": {
        "en": "Total complaint volume jumped sharply in this window — check for a trigger event (weather, an outage, a policy change) before assuming it's the new normal.",
        "kn": "ಈ ಅವಧಿಯಲ್ಲಿ ಒಟ್ಟು ದೂರುಗಳ ಪ್ರಮಾಣ ತೀವ್ರವಾಗಿ ಏರಿತು — ಇದನ್ನು ಹೊಸ ಸಾಮಾನ್ಯ ಎಂದು ಭಾವಿಸುವ ಮೊದಲು ಒಂದು ಪ್ರಚೋದಕ ಘಟನೆಗಾಗಿ (ಹವಾಮಾನ, ಸ್ಥಗಿತ, ನೀತಿ ಬದಲಾವಣೆ) ಪರಿಶೀಲಿಸಿ.",
        "hi": "इस अवधि में कुल शिकायत मात्रा तेज़ी से बढ़ी — इसे नया सामान्य मान लेने से पहले किसी ट्रिगर घटना (मौसम, आउटेज, नीति परिवर्तन) की जांच करें।",
    },
    "conf_high": {"en": "High", "kn": "ಹೆಚ್ಚು", "hi": "उच्च"},
    "conf_medium": {"en": "Medium", "kn": "ಮಧ್ಯಮ", "hi": "मध्यम"},
    "conf_low": {"en": "Low", "kn": "ಕಡಿಮೆ", "hi": "कम"},
    "confidence_label": {"en": "Confidence", "kn": "ವಿಶ್ವಾಸ", "hi": "विश्वास"},
    "memo_default_title": {"en": "CivicPulse Action Memo", "kn": "CivicPulse ಕ್ರಿಯಾ ಮೆಮೊ", "hi": "CivicPulse कार्रवाई मेमो"},
    "memo_generated_by": {"en": "Generated by CivicPulse AI.", "kn": "CivicPulse AI ನಿಂದ ರಚಿಸಲಾಗಿದೆ.", "hi": "CivicPulse AI द्वारा तैयार।"},
    "memo_action_line": {
        "en": "{i}. {icon} {action} (owner: {owner}, timeframe: {timeframe}{urgency_part})",
        "kn": "{i}. {icon} {action} (ಮಾಲೀಕ: {owner}, ಕಾಲಮಿತಿ: {timeframe}{urgency_part})",
        "hi": "{i}. {icon} {action} (स्वामी: {owner}, समयसीमा: {timeframe}{urgency_part})",
    },
    "memo_urgency_part": {"en": ", urgency: {u}", "kn": ", ತುರ್ತು: {u}", "hi": ", तात्कालिकता: {u}"},
    "why_this_recommendation": {"en": "Why this recommendation", "kn": "ಈ ಶಿಫಾರಸು ಏಕೆ", "hi": "यह सिफ़ारिश क्यों"},

    # ---------------------------------------------------------------- recommendations
    "brief_title": {"en": "✅ One-click Executive Brief", "kn": "✅ ಒನ್-ಕ್ಲಿಕ್ ಕಾರ್ಯಕಾರಿ ಸಂಕ್ಷಿಪ್ತ", "hi": "✅ वन-क्लिक कार्यकारी ब्रीफ़"},
    "brief_caption": {
        "en": "The wow feature: a complete, plain-language handoff memo — written for whoever has "
              "to act on this data, even if they've never seen it before. One Gemini call, fully grounded.",
        "kn": "ವಾವ್ ವೈಶಿಷ್ಟ್ಯ: ಸಂಪೂರ್ಣ, ಸರಳ-ಭಾಷೆಯ ಹಸ್ತಾಂತರ ಮೆಮೊ — ಈ ಡೇಟಾದ ಮೇಲೆ ಕಾರ್ಯನಿರ್ವಹಿಸಬೇಕಾದ ಯಾರಿಗಾದರೂ ಬರೆಯಲಾಗಿದೆ, "
              "ಅವರು ಅದನ್ನು ಮೊದಲು ನೋಡದಿದ್ದರೂ ಸಹ. ಒಂದು Gemini ಕರೆ, ಸಂಪೂರ್ಣವಾಗಿ ಆಧಾರಿತ.",
        "hi": "वाह वाला फ़ीचर: एक पूर्ण, सरल-भाषा हैंडऑफ़ मेमो — उस किसी के लिए लिखा गया जिसे इस डेटा पर कार्रवाई करनी है, "
              "भले ही उसने इसे पहले कभी न देखा हो। एक Gemini कॉल, पूरी तरह प्रमाणित।",
    },
    "generate_brief_btn": {
        "en": "🧠 Generate Executive Brief", "kn": "🧠 ಕಾರ್ಯಕಾರಿ ಸಂಕ್ಷಿಪ್ತ ರಚಿಸಿ", "hi": "🧠 कार्यकारी ब्रीफ़ बनाएँ",
    },
    "drafting_spinner": {
        "en": "Gemini is drafting your decision memo...",
        "kn": "Gemini ನಿಮ್ಮ ನಿರ್ಧಾರ ಮೆಮೊವನ್ನು ರಚಿಸುತ್ತಿದೆ...",
        "hi": "Gemini आपका निर्णय मेमो तैयार कर रहा है...",
    },
    "brief_fallback_warning": {
        "en": "Showing offline fallback brief (Gemini not called). Set a key for full AI output.",
        "kn": "ಆಫ್‌ಲೈನ್ ಫಾಲ್‌ಬ್ಯಾಕ್ ಸಂಕ್ಷಿಪ್ತ ತೋರಿಸಲಾಗುತ್ತಿದೆ (Gemini ಕರೆ ಮಾಡಲಾಗಿಲ್ಲ). ಪೂರ್ಣ AI ಔಟ್‌ಪುಟ್‌ಗಾಗಿ ಕೀ ಹೊಂದಿಸಿ.",
        "hi": "ऑफ़लाइन फ़ॉलबैक ब्रीफ़ दिखाया जा रहा है (Gemini को कॉल नहीं किया गया)। पूर्ण AI आउटपुट के लिए एक कुंजी सेट करें।",
    },
    "brief_default_title": {"en": "Executive Brief", "kn": "ಕಾರ್ಯಕಾರಿ ಸಂಕ್ಷಿಪ್ತ", "hi": "कार्यकारी ब्रीफ़"},
    "dataset_overview_heading": {"en": "📖 What this dataset is", "kn": "📖 ಈ ಡೇಟಾಸೆಟ್ ಏನು", "hi": "📖 यह डेटासेट क्या है"},
    "key_findings_heading": {"en": "Key findings", "kn": "ಪ್ರಮುಖ ಸಂಶೋಧನೆಗಳು", "hi": "मुख्य निष्कर्ष"},
    "peculiar_patterns_heading": {"en": "🔎 Peculiar patterns", "kn": "🔎 ವಿಶಿಷ್ಟ ಮಾದರಿಗಳು", "hi": "🔎 असामान्य पैटर्न"},
    "recommended_actions_heading": {
        "en": "Recommended actions — respond by urgency", "kn": "ಶಿಫಾರಸು ಮಾಡಿದ ಕ್ರಮಗಳು — ತುರ್ತಿಗೆ ಅನುಗುಣವಾಗಿ ಪ್ರತಿಕ್ರಿಯಿಸಿ",
        "hi": "अनुशंसित कार्रवाइयाँ — तात्कालिकता के अनुसार प्रतिक्रिया दें",
    },
    "urgency_legend": {
        "en": "🔴 immediate (ASAP) · 🟠 high (this week) · ⚪ normal (this month)",
        "kn": "🔴 ತಕ್ಷಣ (ASAP) · 🟠 ಹೆಚ್ಚು (ಈ ವಾರ) · ⚪ ಸಾಮಾನ್ಯ (ಈ ತಿಂಗಳು)",
        "hi": "🔴 तत्काल (ASAP) · 🟠 उच्च (इस सप्ताह) · ⚪ सामान्य (इस महीने)",
    },
    "urgency_immediate": {"en": "immediate", "kn": "ತಕ್ಷಣ", "hi": "तत्काल"},
    "urgency_high": {"en": "high", "kn": "ಹೆಚ್ಚು", "hi": "उच्च"},
    "urgency_normal": {"en": "normal", "kn": "ಸಾಮಾನ್ಯ", "hi": "सामान्य"},
    "action_owner_timeframe": {
        "en": "Owner: {owner}  ·  Timeframe: {tf}", "kn": "ಮಾಲೀಕ: {owner}  ·  ಕಾಲಮಿತಿ: {tf}", "hi": "स्वामी: {owner}  ·  समयसीमा: {tf}",
    },
    "action_urgency_suffix": {"en": "  ·  Urgency: {u}", "kn": "  ·  ತುರ್ತು: {u}", "hi": "  ·  तात्कालिकता: {u}"},
    "confidence_heading": {"en": "Confidence", "kn": "ವಿಶ್ವಾಸ", "hi": "विश्वास"},
    "explainability_expander": {
        "en": "🔍 Explainability — why this recommendation?",
        "kn": "🔍 ವಿವರಣೆ — ಈ ಶಿಫಾರಸು ಏಕೆ?",
        "hi": "🔍 व्याख्या — यह सिफ़ारिश क्यों?",
    },
    "download_memo_btn": {
        "en": "⬇️ Download memo (Markdown)", "kn": "⬇️ ಮೆಮೊ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ (Markdown)", "hi": "⬇️ मेमो डाउनलोड करें (Markdown)",
    },
    "brief_click_hint": {
        "en": "Click **Generate Executive Brief** to produce a decision-ready memo.",
        "kn": "ನಿರ್ಧಾರ-ಸಿದ್ಧ ಮೆಮೊ ರಚಿಸಲು **ಕಾರ್ಯಕಾರಿ ಸಂಕ್ಷಿಪ್ತ ರಚಿಸಿ** ಕ್ಲಿಕ್ ಮಾಡಿ.",
        "hi": "निर्णय-तैयार मेमो बनाने के लिए **कार्यकारी ब्रीफ़ बनाएँ** पर क्लिक करें।",
    },
    "recent_briefs_expander": {
        "en": "📜 Recent briefs ({n}) — trend across past uploads",
        "kn": "📜 ಇತ್ತೀಚಿನ ಸಂಕ್ಷಿಪ್ತಗಳು ({n}) — ಹಿಂದಿನ ಅಪ್‌ಲೋಡ್‌ಗಳಾದ್ಯಂತ ಪ್ರವೃತ್ತಿ",
        "hi": "📜 हालिया ब्रीफ़ ({n}) — पिछले अपलोड में रुझान",
    },
    "recent_briefs_caption": {
        "en": "Every generated brief is saved automatically, so a team can see how a "
              "location trends across sessions instead of only today's snapshot.",
        "kn": "ಪ್ರತಿ ರಚಿತ ಸಂಕ್ಷಿಪ್ತವನ್ನು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಉಳಿಸಲಾಗುತ್ತದೆ, ಆದ್ದರಿಂದ ಒಂದು ತಂಡವು ಇಂದಿನ ಸ್ನ್ಯಾಪ್‌ಶಾಟ್ ಮಾತ್ರವಲ್ಲದೆ "
              "ಸೆಶನ್‌ಗಳಾದ್ಯಂತ ಒಂದು ಸ್ಥಳ ಹೇಗೆ ಪ್ರವೃತ್ತಿಸುತ್ತದೆ ಎಂಬುದನ್ನು ನೋಡಬಹುದು.",
        "hi": "हर तैयार ब्रीफ़ स्वचालित रूप से सहेजा जाता है, ताकि एक टीम देख सके कि कोई स्थान सत्रों में "
              "कैसे बदलता है, न कि केवल आज के स्नैपशॉट में।",
    },
    "untitled_brief": {"en": "Untitled brief", "kn": "ಶೀರ್ಷಿಕೆಯಿಲ್ಲದ ಸಂಕ್ಷಿಪ್ತ", "hi": "बिना शीर्षक ब्रीफ़"},
    "brief_record_summary": {
        "en": "{area} · {category} · {records} records · trend: {trend}",
        "kn": "{area} · {category} · {records} ದಾಖಲೆಗಳು · ಪ್ರವೃತ್ತಿ: {trend}",
        "hi": "{area} · {category} · {records} रिकॉर्ड · रुझान: {trend}",
    },
    "automated_reports_title": {
        "en": "🔔 Automated Weekly Reports", "kn": "🔔 ಸ್ವಯಂಚಾಲಿತ ಸಾಪ್ತಾಹಿಕ ವರದಿಗಳು", "hi": "🔔 स्वचालित साप्ताहिक रिपोर्ट",
    },
    "automated_reports_caption": {
        "en": "Every Monday, a Cloud Scheduler job runs this same pipeline automatically and emails "
              "a citywide brief plus one department-scoped report to each configured department "
              "contact — nobody has to open this dashboard. Trigger it now to see it live.",
        "kn": "ಪ್ರತಿ ಸೋಮವಾರ, ಒಂದು Cloud Scheduler ಕೆಲಸವು ಇದೇ ಪೈಪ್‌ಲೈನ್ ಅನ್ನು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಚಲಾಯಿಸುತ್ತದೆ ಮತ್ತು "
              "ನಗರವ್ಯಾಪ್ತಿ ಸಂಕ್ಷಿಪ್ತ ಜೊತೆಗೆ ಪ್ರತಿ ಕಾನ್ಫಿಗರ್ ಮಾಡಿದ ಇಲಾಖಾ ಸಂಪರ್ಕಕ್ಕೆ ಒಂದು ಇಲಾಖಾ-ವ್ಯಾಪ್ತಿಯ ವರದಿಯನ್ನು ಇಮೇಲ್ ಮಾಡುತ್ತದೆ "
              "— ಯಾರೂ ಈ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ತೆರೆಯಬೇಕಿಲ್ಲ. ಈಗ ಟ್ರಿಗರ್ ಮಾಡಿ ಲೈವ್ ನೋಡಲು.",
        "hi": "हर सोमवार, एक Cloud Scheduler जॉब यही पाइपलाइन स्वचालित रूप से चलाता है और शहरव्यापी ब्रीफ़ के साथ "
              "हर कॉन्फ़िगर किए गए विभाग संपर्क को एक विभाग-विशिष्ट रिपोर्ट ईमेल करता है — किसी को यह डैशबोर्ड खोलने की "
              "ज़रूरत नहीं। इसे अभी लाइव देखने के लिए ट्रिगर करें।",
    },
    "scheduled_not_configured": {
        "en": "Scheduled-report trigger isn't configured for this deployment.",
        "kn": "ಈ ನಿಯೋಜನೆಗೆ ಶೆಡ್ಯೂಲ್ ಮಾಡಿದ-ವರದಿ ಟ್ರಿಗರ್ ಕಾನ್ಫಿಗರ್ ಮಾಡಿಲ್ಲ.",
        "hi": "इस डिप्लॉयमेंट के लिए शेड्यूल्ड-रिपोर्ट ट्रिगर कॉन्फ़िगर नहीं है।",
    },
    "send_reports_btn": {"en": "📨 Send scheduled reports now", "kn": "📨 ಶೆಡ್ಯೂಲ್ ಮಾಡಿದ ವರದಿಗಳನ್ನು ಈಗ ಕಳುಹಿಸಿ", "hi": "📨 शेड्यूल्ड रिपोर्ट अभी भेजें"},
    "triggering_spinner": {
        "en": "Triggering the scheduled job — generating and emailing citywide + department reports...",
        "kn": "ಶೆಡ್ಯೂಲ್ ಮಾಡಿದ ಕೆಲಸವನ್ನು ಟ್ರಿಗರ್ ಮಾಡಲಾಗುತ್ತಿದೆ — ನಗರವ್ಯಾಪ್ತಿ + ಇಲಾಖಾ ವರದಿಗಳನ್ನು ರಚಿಸಿ ಇಮೇಲ್ ಮಾಡಲಾಗುತ್ತಿದೆ...",
        "hi": "शेड्यूल्ड जॉब ट्रिगर किया जा रहा है — शहरव्यापी + विभागीय रिपोर्ट तैयार और ईमेल की जा रही हैं...",
    },
    "trigger_failed": {"en": "Trigger failed: {err}", "kn": "ಟ್ರಿಗರ್ ವಿಫಲವಾಗಿದೆ: {err}", "hi": "ट्रिगर विफल: {err}"},
    "trigger_fallback_note": {"en": " (offline fallback used)", "kn": " (ಆಫ್‌ಲೈನ್ ಫಾಲ್‌ಬ್ಯಾಕ್ ಬಳಸಲಾಗಿದೆ)", "hi": " (ऑफ़लाइन फ़ॉलबैक उपयोग किया गया)"},
    "trigger_success": {"en": "✅ Citywide brief: {status}{note}", "kn": "✅ ನಗರವ್ಯಾಪ್ತಿ ಸಂಕ್ಷಿಪ್ತ: {status}{note}", "hi": "✅ शहरव्यापी ब्रीफ़: {status}{note}"},

    # ---------------------------------------------------------------- real-time alert (Recommendations tab)
    "send_realtime_alert_btn": {
        "en": "🚨 Send Real-Time Alert ({n} urgent)",
        "kn": "🚨 ರಿಯಲ್-ಟೈಮ್ ಎಚ್ಚರಿಕೆ ಕಳುಹಿಸಿ ({n} ತುರ್ತು)",
        "hi": "🚨 रीयल-टाइम अलर्ट भेजें ({n} अत्यावश्यक)",
    },
    "realtime_alert_sending": {
        "en": "Sending real-time alert...", "kn": "ರಿಯಲ್-ಟೈಮ್ ಎಚ್ಚರಿಕೆ ಕಳುಹಿಸಲಾಗುತ್ತಿದೆ...", "hi": "रीयल-टाइम अलर्ट भेजा जा रहा है...",
    },
    "realtime_alert_sent": {
        "en": "✅ Alert sent: {status}", "kn": "✅ ಎಚ್ಚರಿಕೆ ಕಳುಹಿಸಲಾಗಿದೆ: {status}", "hi": "✅ अलर्ट भेजा गया: {status}",
    },
    "realtime_alert_failed": {
        "en": "Alert failed: {err}", "kn": "ಎಚ್ಚರಿಕೆ ವಿಫಲವಾಗಿದೆ: {err}", "hi": "अलर्ट विफल: {err}",
    },
    "realtime_alert_needs_config": {
        "en": "⚠️ {n} action(s) need an immediate response, but the real-time alert trigger isn't configured for this deployment.",
        "kn": "⚠️ {n} ಕ್ರಮ(ಗಳಿಗೆ) ತಕ್ಷಣದ ಪ್ರತಿಕ್ರಿಯೆ ಬೇಕು, ಆದರೆ ಈ ನಿಯೋಜನೆಗೆ ರಿಯಲ್-ಟೈಮ್ ಎಚ್ಚರಿಕೆ ಟ್ರಿಗರ್ ಕಾನ್ಫಿಗರ್ ಮಾಡಿಲ್ಲ.",
        "hi": "⚠️ {n} कार्रवाई(यों) को तुरंत प्रतिक्रिया चाहिए, लेकिन इस डिप्लॉयमेंट के लिए रीयल-टाइम अलर्ट ट्रिगर कॉन्फ़िगर नहीं है।",
    },

    # ---------------------------------------------------------------- OCR scan (sidebar trigger + Recommendations result)
    "ocr_section_title": {
        "en": "📷 Scan a Complaint Form (OCR)", "kn": "📷 ದೂರು ಫಾರ್ಮ್ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ (OCR)", "hi": "📷 शिकायत फ़ॉर्म स्कैन करें (OCR)",
    },
    "ocr_section_caption": {
        "en": "Upload a photo or scanned copy of a paper complaint form — Gemini reads it directly "
              "(including handwriting) and turns it into a brief, shown in the Recommendations tab.",
        "kn": "ಕಾಗದದ ದೂರು ಫಾರ್ಮ್‌ನ ಫೋಟೋ ಅಥವಾ ಸ್ಕ್ಯಾನ್ ಮಾಡಿದ ಪ್ರತಿಯನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ — Gemini ಅದನ್ನು ನೇರವಾಗಿ ಓದುತ್ತದೆ "
              "(ಕೈಬರಹ ಸೇರಿದಂತೆ) ಮತ್ತು ಅದನ್ನು ಒಂದು ಸಂಕ್ಷಿಪ್ತಕ್ಕೆ ಪರಿವರ್ತಿಸುತ್ತದೆ, ಇದನ್ನು ಶಿಫಾರಸುಗಳು ಟ್ಯಾಬ್‌ನಲ್ಲಿ ತೋರಿಸಲಾಗುತ್ತದೆ.",
        "hi": "कागज़ी शिकायत फ़ॉर्म की फ़ोटो या स्कैन की गई प्रति अपलोड करें — Gemini इसे सीधे पढ़ता है "
              "(हस्तलेख सहित) और इसे एक ब्रीफ़ में बदल देता है, जो सिफ़ारिशें टैब में दिखाया जाता है।",
    },
    "ocr_upload_label": {
        "en": "Upload a photo or scanned PDF of a complaint form", "kn": "ದೂರು ಫಾರ್ಮ್‌ನ ಫೋಟೋ ಅಥವಾ ಸ್ಕ್ಯಾನ್ ಮಾಡಿದ PDF ಅಪ್‌ಲೋಡ್ ಮಾಡಿ", "hi": "शिकायत फ़ॉर्म की फ़ोटो या स्कैन की गई PDF अपलोड करें",
    },
    "ocr_scan_btn": {
        "en": "🔍 Extract & Summarize (OCR)", "kn": "🔍 ಹೊರತೆಗೆದು ಸಾರಾಂಶಿಸಿ (OCR)", "hi": "🔍 निकालें और सारांशित करें (OCR)",
    },
    "ocr_extracting_spinner": {
        "en": "Reading the image with Gemini (OCR)...", "kn": "Gemini ಮೂಲಕ ಚಿತ್ರವನ್ನು ಓದಲಾಗುತ್ತಿದೆ (OCR)...", "hi": "Gemini से छवि पढ़ी जा रही है (OCR)...",
    },
    "ocr_scan_done_hint": {
        "en": "✅ Scanned! See the result in the Recommendations tab.",
        "kn": "✅ ಸ್ಕ್ಯಾನ್ ಮಾಡಲಾಗಿದೆ! ಫಲಿತಾಂಶವನ್ನು ಶಿಫಾರಸುಗಳು ಟ್ಯಾಬ್‌ನಲ್ಲಿ ನೋಡಿ.",
        "hi": "✅ स्कैन हो गया! परिणाम सिफ़ारिशें टैब में देखें।",
    },
    "ocr_extracted_text_expander": {
        "en": "📄 Extracted text", "kn": "📄 ಹೊರತೆಗೆದ ಪಠ್ಯ", "hi": "📄 निकाला गया टेक्स्ट",
    },
    "ocr_failed": {
        "en": "OCR failed: {err}", "kn": "OCR ವಿಫಲವಾಗಿದೆ: {err}", "hi": "OCR विफल: {err}",
    },

    # ---------------------------------------------------------------- about (grouped into large blocks)
    "about_title": {"en": "ℹ️ About CivicPulse AI", "kn": "ℹ️ CivicPulse AI ಬಗ್ಗೆ", "hi": "ℹ️ CivicPulse AI के बारे में"},
    "about_intro_md": {
        "en": """**CivicPulse AI** is a decision intelligence dashboard for cities and communities.
It combines **deterministic Python analytics** (counts, trends, anomaly detection,
forecasting) with **Gemini** that explains the numbers and recommends concrete
next steps — and a set of Google Cloud services that turn it from a one-off
dashboard into an automated service.

**Why it's different from a chatbot**
- Numbers are computed locally first, so the AI never hallucinates statistics.
- Every answer maps to a decision: *what / why / where / next step / confidence*.
- A Decision Scoreboard (urgency · impact · confidence) tells teams what to act on.""",
        "kn": """**CivicPulse AI** ಎಂಬುದು ನಗರಗಳು ಮತ್ತು ಸಮುದಾಯಗಳಿಗಾಗಿ ಒಂದು ನಿರ್ಧಾರ ಬುದ್ಧಿಮತ್ತೆ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ಆಗಿದೆ.
ಇದು **ನಿರ್ಣಾಯಕ Python ವಿಶ್ಲೇಷಣೆ** (ಎಣಿಕೆಗಳು, ಪ್ರವೃತ್ತಿಗಳು, ಅಸಂಗತತೆ ಪತ್ತೆ, ಮುನ್ಸೂಚನೆ) ಅನ್ನು
**Gemini** ಯೊಂದಿಗೆ ಸಂಯೋಜಿಸುತ್ತದೆ, ಇದು ಸಂಖ್ಯೆಗಳನ್ನು ವಿವರಿಸುತ್ತದೆ ಮತ್ತು
ನಿರ್ದಿಷ್ಟ ಮುಂದಿನ ಹಂತಗಳನ್ನು ಶಿಫಾರಸು ಮಾಡುತ್ತದೆ — ಮತ್ತು ಒಂದು ಸೆಟ್ Google Cloud ಸೇವೆಗಳು ಇದನ್ನು
ಒಂದು-ಬಾರಿ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನಿಂದ ಸ್ವಯಂಚಾಲಿತ ಸೇವೆಯಾಗಿ ಪರಿವರ್ತಿಸುತ್ತವೆ.

**ಇದು ಚಾಟ್‌ಬಾಟ್‌ಗಿಂತ ಏಕೆ ಭಿನ್ನವಾಗಿದೆ**
- ಸಂಖ್ಯೆಗಳನ್ನು ಮೊದಲು ಸ್ಥಳೀಯವಾಗಿ ಲೆಕ್ಕಿಸಲಾಗುತ್ತದೆ, ಆದ್ದರಿಂದ AI ಎಂದಿಗೂ ಅಂಕಿಅಂಶಗಳನ್ನು ಭ್ರಮಿಸುವುದಿಲ್ಲ.
- ಪ್ರತಿಯೊಂದು ಉತ್ತರವು ಒಂದು ನಿರ್ಧಾರಕ್ಕೆ ನಕ್ಷೆ ಮಾಡುತ್ತದೆ: *ಏನು / ಏಕೆ / ಎಲ್ಲಿ / ಮುಂದಿನ ಹಂತ / ವಿಶ್ವಾಸ*.
- ಒಂದು ನಿರ್ಧಾರ ಸ್ಕೋರ್‌ಬೋರ್ಡ್ (ತುರ್ತು · ಪರಿಣಾಮ · ವಿಶ್ವಾಸ) ತಂಡಗಳಿಗೆ ಏನು ಕಾರ್ಯನಿರ್ವಹಿಸಬೇಕೆಂದು ತಿಳಿಸುತ್ತದೆ.""",
        "hi": """**CivicPulse AI** शहरों और समुदायों के लिए एक निर्णय बुद्धिमत्ता डैशबोर्ड है।
यह **निर्धारक Python विश्लेषण** (गिनती, रुझान, विसंगति पहचान, पूर्वानुमान) को
**Gemini** के साथ जोड़ता है जो संख्याओं की व्याख्या करता है और
ठोस अगले कदम सुझाता है — और Google Cloud सेवाओं का एक सेट इसे
एक बार के डैशबोर्ड से एक स्वचालित सेवा में बदल देता है।

**यह चैटबॉट से अलग क्यों है**
- संख्याओं की गणना पहले स्थानीय रूप से की जाती है, इसलिए AI कभी भी आँकड़े नहीं गढ़ता।
- हर उत्तर एक निर्णय से जुड़ता है: *क्या / क्यों / कहाँ / अगला कदम / विश्वास*।
- एक निर्णय स्कोरबोर्ड (तात्कालिकता · प्रभाव · विश्वास) टीमों को बताता है कि क्या करना है।""",
    },
    "about_features_heading": {"en": "**What's in here**", "kn": "**ಇಲ್ಲಿ ಏನಿದೆ**", "hi": "**यहाँ क्या है**"},
    "about_features_md": {
        "en": """- 🎨 **Light/dark app theme** — toggle at the top of the sidebar switches the
  whole dashboard between a clean professional light theme and the futuristic
  neon theme, for whichever reads best on your screen.
- 🌐 **Kannada / Hindi / English interface** — every label, button, and AI answer
  can switch language with one toggle, alongside area/category/severity/status
  values shown on screen.
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
  contacts — with an in-app button to trigger it on demand.""",
        "kn": """- 🎨 **ಬೆಳಕು/ಕತ್ತಲೆ ಆ್ಯಪ್ ಥೀಮ್** — ಸೈಡ್‌ಬಾರ್‌ನ ಮೇಲ್ಭಾಗದ ಟಾಗಲ್ ಇಡೀ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ಅನ್ನು
  ಸ್ವಚ್ಛ ವೃತ್ತಿಪರ ಬೆಳಕಿನ ಥೀಮ್ ಮತ್ತು ಭವಿಷ್ಯದ ನಿಯಾನ್ ಥೀಮ್ ನಡುವೆ ಬದಲಾಯಿಸುತ್ತದೆ, ನಿಮ್ಮ ಪರದೆಯಲ್ಲಿ
  ಯಾವುದು ಉತ್ತಮವಾಗಿ ಕಾಣುತ್ತದೆಯೋ ಅದಕ್ಕೆ.
- 🌐 **ಕನ್ನಡ / ಹಿಂದಿ / ಇಂಗ್ಲಿಷ್ ಇಂಟರ್‌ಫೇಸ್** — ಪ್ರತಿಯೊಂದು ಲೇಬಲ್, ಬಟನ್ ಮತ್ತು AI ಉತ್ತರವು
  ಒಂದು ಟಾಗಲ್‌ನೊಂದಿಗೆ ಭಾಷೆಯನ್ನು ಬದಲಾಯಿಸಬಹುದು, ಪರದೆಯ ಮೇಲೆ ತೋರಿಸಲಾದ ಪ್ರದೇಶ/ವರ್ಗ/ತೀವ್ರತೆ/ಸ್ಥಿತಿ
  ಮೌಲ್ಯಗಳ ಜೊತೆಗೆ.
- 💬 **ಏಜೆಂಟಿಕ್, ಬಹು-ತಿರುವು ಚಾಟ್** — AI ಕೇಳಿ ನಿಮ್ಮ ಲೈವ್ ಡೇಟಾ (ಒಂದು ಸ್ಥಿರ ಸ್ನ್ಯಾಪ್‌ಶಾಟ್ ಅಲ್ಲ) ವಿರುದ್ಧ
  ನೈಜ ಪ್ರಶ್ನೆ ಪರಿಕರಗಳನ್ನು ಕರೆಯುತ್ತದೆ ಮತ್ತು ಸಂಭಾಷಣೆಯನ್ನು ನೆನಪಿಟ್ಟುಕೊಳ್ಳುತ್ತದೆ, ಆದ್ದರಿಂದ
  *"ಎರಡನೆಯದರ ಬಗ್ಗೆ ಏನು?"* ನಂತಹ ಮುಂದುವರಿದ ಪ್ರಶ್ನೆಗಳು ಕೆಲಸ ಮಾಡುತ್ತವೆ. ಪ್ರತಿ ಉತ್ತರವು ಯಾವ
  ಪ್ರಶ್ನೆಗಳು ಚಾಲನೆಗೊಂಡಿವೆ ಎಂಬುದನ್ನು ನಿಖರವಾಗಿ ತೋರಿಸುತ್ತದೆ, ಮತ್ತು ಆಧಾರಿತ ಮುಂದಿನ ಪ್ರಶ್ನೆಗಳನ್ನು ಸೂಚಿಸುತ್ತದೆ.
- 🗺️ **ನೈಜ ಹಾಟ್‌ಸ್ಪಾಟ್ ಮ್ಯಾಪಿಂಗ್** — ನಿಜವಾದ BBMP ವಾರ್ಡ್ ನಿರ್ದೇಶಾಂಕಗಳು (OpenCity ಯ ಬೆಂಗಳೂರು
  ವಾರ್ಡ್ ಡೇಟಾಸೆಟ್), ನಕ್ಷೆಯ ಮೇಲೆ ತನ್ನದೇ ಆದ ಕತ್ತಲೆ/ಬೆಳಕಿನ ಬೇಸ್‌ಮ್ಯಾಪ್ ಟಾಗಲ್‌ನೊಂದಿಗೆ.
- 📈 **7-ದಿನದ ಮುನ್ಸೂಚನೆ** — Holt's ರೇಖೀಯ ಪ್ರವೃತ್ತಿ ವಿಧಾನವು ಪ್ರತಿ ಪ್ರದೇಶಕ್ಕೆ ಸಂಭವನೀಯ ಏರಿಕೆಗಳನ್ನು
  ಸಂಭವಿಸುವ ಮೊದಲೇ ಗುರುತಿಸುತ್ತದೆ, ನಂತರವಲ್ಲ.
- 📝 **ಒನ್-ಕ್ಲಿಕ್ ಕಾರ್ಯಕಾರಿ ಸಂಕ್ಷಿಪ್ತ** — ಒಂದು ಸಂಪೂರ್ಣ, ಸರಳ-ಭಾಷೆಯ ಹಸ್ತಾಂತರ ಮೆಮೊ
  (ಡೇಟಾಸೆಟ್ ಅವಲೋಕನ, ಪ್ರತಿ ಗಮನಾರ್ಹ ಮಾದರಿ, ತುರ್ತು-ಟ್ಯಾಗ್ ಮಾಡಿದ ಮುಂದಿನ ಹಂತಗಳು) ಒಂದೇ
  ಆಧಾರಿತ Gemini ಕರೆಯಿಂದ.
- 🗄️ **ಶಾಶ್ವತ ಸಂಕ್ಷಿಪ್ತ ಇತಿಹಾಸ** — ಪ್ರತಿ ರಚಿತ ಸಂಕ್ಷಿಪ್ತವು Firestore ಗೆ ಉಳಿಸುತ್ತದೆ, ಆದ್ದರಿಂದ
  ಒಂದು ತಂಡವು ಇಂದಿನ ಅಪ್‌ಲೋಡ್ ಮಾತ್ರವಲ್ಲದೆ ಸೆಶನ್‌ಗಳಾದ್ಯಂತ ಪ್ರವೃತ್ತಿಗಳನ್ನು ನೋಡಬಹುದು.
- 🔄 **ಮರುಲೋಡ್-ಸುರಕ್ಷಿತ ಸೆಶನ್‌ಗಳು** — ನಿಮ್ಮ ಲೋಡ್ ಮಾಡಿದ ಡೇಟಾ ಮತ್ತು ಚಾಟ್ ಇತಿಹಾಸವು ಪುಟ
  ರಿಫ್ರೆಶ್ ಅನ್ನು ಬದುಕುಳಿಯುತ್ತದೆ, URL ನಲ್ಲಿ ಇರಿಸಲಾದ ಸೆಶನ್ ಐಡಿ ಮೂಲಕ Firestore ನಿಂದ ಮರುಸ್ಥಾಪಿಸಲಾಗುತ್ತದೆ;
  ಹಳೆಯ ಸೆಶನ್‌ಗಳು 24 ಗಂಟೆಗಳ ನಂತರ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಅವಧಿ ಮುಗಿಯುತ್ತವೆ.
- 🔔 **ಸ್ವಯಂಚಾಲಿತ, ಇಲಾಖಾ-ಮಾರ್ಗಿತ ಇಮೇಲ್** — ಒಂದು Cloud Scheduler ಕೆಲಸವು ಅದೇ ಪೈಪ್‌ಲೈನ್ ಅನ್ನು
  ಒಂದು ಕ್ರಾನ್‌ನಲ್ಲಿ ಚಲಾಯಿಸುತ್ತದೆ ಮತ್ತು ನಗರವ್ಯಾಪ್ತಿ ಸಂಕ್ಷಿಪ್ತ *ಜೊತೆಗೆ* ಪ್ರತಿ ಇಲಾಖೆಗೆ ಒಂದು ಪ್ರತ್ಯೇಕ
  ಸಂಕ್ಷಿಪ್ತವನ್ನು, ಆ ಇಲಾಖೆಯ ಡೇಟಾಗೆ ಮಾತ್ರ ವ್ಯಾಪ್ತಿ ಹೊಂದಿದ, ಆ ಇಲಾಖೆಯ ಸ್ವಂತ ಸಂಪರ್ಕಗಳಿಗೆ ಇಮೇಲ್ ಮಾಡುತ್ತದೆ
  — ಬೇಡಿಕೆಯ ಮೇಲೆ ಟ್ರಿಗರ್ ಮಾಡಲು ಆ್ಯಪ್-ಒಳಗಿನ ಬಟನ್‌ನೊಂದಿಗೆ.""",
        "hi": """- 🎨 **हल्का/गहरा ऐप थीम** — साइडबार के ऊपर टॉगल पूरे डैशबोर्ड को एक स्वच्छ पेशेवर
  हल्के थीम और भविष्यवादी नियॉन थीम के बीच बदलता है, जो भी आपकी स्क्रीन पर बेहतर दिखे।
- 🌐 **कन्नड़ / हिंदी / अंग्रेज़ी इंटरफ़ेस** — हर लेबल, बटन और AI उत्तर एक टॉगल से भाषा
  बदल सकता है, साथ ही स्क्रीन पर दिखाए गए क्षेत्र/श्रेणी/गंभीरता/स्थिति मान भी।
- 💬 **एजेंटिक, बहु-चरण चैट** — AI से पूछें आपके लाइव डेटा (एक स्थिर स्नैपशॉट नहीं) के विरुद्ध
  वास्तविक क्वेरी टूल्स कॉल करता है और बातचीत याद रखता है, ताकि *"दूसरे के बारे में क्या?"* जैसे
  फ़ॉलो-अप बस काम करें। हर उत्तर बिल्कुल दिखाता है कि कौन सी क्वेरी चलीं, और आगे टैप करने के
  लिए प्रमाणित प्रश्न सुझाता है।
- 🗺️ **वास्तविक हॉटस्पॉट मैपिंग** — वास्तविक BBMP वार्ड निर्देशांक (OpenCity का बेंगलुरु
  वार्ड डेटासेट), मानचित्र के ऊपर अपने खुद के गहरे/हल्के बेसमैप टॉगल के साथ।
- 📈 **7-दिन का पूर्वानुमान** — Holt की रैखिक रुझान विधि प्रति क्षेत्र संभावित उछाल को
  होने से पहले ही चिह्नित करती है, बाद में नहीं।
- 📝 **वन-क्लिक कार्यकारी ब्रीफ़** — एक पूर्ण, सरल-भाषा हैंडऑफ़ मेमो (डेटासेट अवलोकन,
  हर उल्लेखनीय पैटर्न, तात्कालिकता-टैग किए गए अगले कदम) एक ही प्रमाणित Gemini कॉल से।
- 🗄️ **स्थायी ब्रीफ़ इतिहास** — हर तैयार ब्रीफ़ Firestore में सहेजा जाता है, ताकि एक टीम
  केवल आज के अपलोड ही नहीं, सत्रों में रुझान देख सके।
- 🔄 **रीलोड-सुरक्षित सत्र** — आपका लोड किया गया डेटा और चैट इतिहास पेज रीफ़्रेश से बच जाता है,
  URL में रखे गए सत्र आईडी के माध्यम से Firestore से पुनर्स्थापित; पुराने सत्र 24 घंटे बाद
  स्वचालित रूप से समाप्त हो जाते हैं।
- 🔔 **स्वचालित, विभाग-रूटेड ईमेल** — एक Cloud Scheduler जॉब उसी पाइपलाइन को क्रॉन पर
  चलाता है और शहरव्यापी ब्रीफ़ *के साथ* हर विभाग के लिए एक अलग ब्रीफ़, केवल उस विभाग के डेटा तक
  सीमित, उस विभाग के अपने संपर्कों को ईमेल करता है — मांग पर ट्रिगर करने के लिए ऐप के अंदर एक बटन के साथ।""",
    },
    "about_gcloud_heading": {"en": "**Google Cloud stack**", "kn": "**Google Cloud ಸ್ಟ್ಯಾಕ್**", "hi": "**Google Cloud स्टैक**"},
    "about_gcloud_md": {
        "en": """- 🤖 **Vertex AI / Gemini** (`gemini-2.5-pro` by default) — explanations,
  agentic function calling, brief generation
- 🚀 **Cloud Run** — hosts the app, scale-to-zero so idle cost is ~$0
- ⚡ **Cloud Functions (2nd gen)** — the scheduled brief job
- ⏰ **Cloud Scheduler** — triggers the weekly automated run
- 🗄️ **Firestore** — brief history + reload-safe session persistence
- 🔐 **Secret Manager** — stores the Gmail app password, never in code
- 🛠️ **Cloud Build**, **Artifact Registry**, **IAM**, **Cloud Logging**, **`gcloud` CLI**
  — builds, image storage, least-privilege service accounts, and one-command deploys""",
        "kn": """- 🤖 **Vertex AI / Gemini** (ಡೀಫಾಲ್ಟ್ ಆಗಿ `gemini-2.5-pro`) — ವಿವರಣೆಗಳು,
  ಏಜೆಂಟಿಕ್ ಫಂಕ್ಷನ್ ಕಾಲಿಂಗ್, ಸಂಕ್ಷಿಪ್ತ ಉತ್ಪಾದನೆ
- 🚀 **Cloud Run** — ಆ್ಯಪ್ ಅನ್ನು ಹೋಸ್ಟ್ ಮಾಡುತ್ತದೆ, ಸ್ಕೇಲ್-ಟು-ಜೀರೋ ಆದ್ದರಿಂದ ನಿಷ್ಕ್ರಿಯ ವೆಚ್ಚ ~$0
- ⚡ **Cloud Functions (2ನೇ ಪೀಳಿಗೆ)** — ಶೆಡ್ಯೂಲ್ ಮಾಡಿದ ಸಂಕ್ಷಿಪ್ತ ಕೆಲಸ
- ⏰ **Cloud Scheduler** — ಸಾಪ್ತಾಹಿಕ ಸ್ವಯಂಚಾಲಿತ ರನ್ ಅನ್ನು ಟ್ರಿಗರ್ ಮಾಡುತ್ತದೆ
- 🗄️ **Firestore** — ಸಂಕ್ಷಿಪ್ತ ಇತಿಹಾಸ + ಮರುಲೋಡ್-ಸುರಕ್ಷಿತ ಸೆಶನ್ ಶಾಶ್ವತೀಕರಣ
- 🔐 **Secret Manager** — Gmail ಆ್ಯಪ್ ಪಾಸ್‌ವರ್ಡ್ ಅನ್ನು ಸಂಗ್ರಹಿಸುತ್ತದೆ, ಎಂದಿಗೂ ಕೋಡ್‌ನಲ್ಲಿ ಅಲ್ಲ
- 🛠️ **Cloud Build**, **Artifact Registry**, **IAM**, **Cloud Logging**, **`gcloud` CLI**
  — ಬಿಲ್ಡ್‌ಗಳು, ಇಮೇಜ್ ಸಂಗ್ರಹಣೆ, ಕನಿಷ್ಠ-ಸವಲತ್ತು ಸೇವಾ ಖಾತೆಗಳು, ಮತ್ತು ಒಂದು-ಆಜ್ಞೆಯ ನಿಯೋಜನೆಗಳು""",
        "hi": """- 🤖 **Vertex AI / Gemini** (डिफ़ॉल्ट रूप से `gemini-2.5-pro`) — व्याख्याएँ,
  एजेंटिक फ़ंक्शन कॉलिंग, ब्रीफ़ जनरेशन
- 🚀 **Cloud Run** — ऐप होस्ट करता है, स्केल-टू-ज़ीरो इसलिए निष्क्रिय लागत ~$0
- ⚡ **Cloud Functions (दूसरी पीढ़ी)** — शेड्यूल्ड ब्रीफ़ जॉब
- ⏰ **Cloud Scheduler** — साप्ताहिक स्वचालित रन को ट्रिगर करता है
- 🗄️ **Firestore** — ब्रीफ़ इतिहास + रीलोड-सुरक्षित सत्र स्थायित्व
- 🔐 **Secret Manager** — Gmail ऐप पासवर्ड संग्रहीत करता है, कभी कोड में नहीं
- 🛠️ **Cloud Build**, **Artifact Registry**, **IAM**, **Cloud Logging**, **`gcloud` CLI**
  — बिल्ड, इमेज स्टोरेज, न्यूनतम-विशेषाधिकार सेवा खाते, और एक-कमांड डिप्लॉय""",
    },
    "about_cost_heading": {"en": "**Cost design**", "kn": "**ವೆಚ್ಚ ವಿನ್ಯಾಸ**", "hi": "**लागत डिज़ाइन**"},
    "about_cost_md": {
        "en": """- One Gemini call per meaningful action (not per keystroke)
- `gemini-2.5-pro` by default — spends the quality budget where it's felt most (briefs, Ask AI), not on every keystroke
- Cloud Run and Cloud Functions both scale to zero when idle
- Firestore/Secret Manager/Scheduler all stay within their free tiers at this scale""",
        "kn": """- ಪ್ರತಿ ಅರ್ಥಪೂರ್ಣ ಕ್ರಿಯೆಗೆ ಒಂದು Gemini ಕರೆ (ಪ್ರತಿ ಕೀಸ್ಟ್ರೋಕ್‌ಗಲ್ಲ)
- ಡೀಫಾಲ್ಟ್ ಆಗಿ `gemini-2.5-pro` — ಗುಣಮಟ್ಟದ ಬಜೆಟ್ ಅನ್ನು ಅತಿ ಹೆಚ್ಚು ಅನುಭವಿಸುವಲ್ಲಿ (ಸಂಕ್ಷಿಪ್ತಗಳು, Ask AI) ಖರ್ಚು ಮಾಡುತ್ತದೆ, ಪ್ರತಿ ಕೀಸ್ಟ್ರೋಕ್‌ಗಲ್ಲ
- Cloud Run ಮತ್ತು Cloud Functions ಎರಡೂ ನಿಷ್ಕ್ರಿಯವಾದಾಗ ಶೂನ್ಯಕ್ಕೆ ಸ್ಕೇಲ್ ಆಗುತ್ತವೆ
- Firestore/Secret Manager/Scheduler ಎಲ್ಲವೂ ಈ ಪ್ರಮಾಣದಲ್ಲಿ ಅವುಗಳ ಉಚಿತ ಶ್ರೇಣಿಗಳಲ್ಲಿ ಉಳಿಯುತ್ತವೆ""",
        "hi": """- प्रति सार्थक कार्रवाई एक Gemini कॉल (प्रति कीस्ट्रोक नहीं)
- डिफ़ॉल्ट रूप से `gemini-2.5-pro` — गुणवत्ता का बजट वहाँ खर्च होता है जहाँ सबसे ज़्यादा महसूस होता है (ब्रीफ़, Ask AI), हर कीस्ट्रोक पर नहीं
- Cloud Run और Cloud Functions दोनों निष्क्रिय होने पर शून्य तक स्केल होते हैं
- Firestore/Secret Manager/Scheduler सभी इस पैमाने पर अपने मुफ़्त टियर के भीतर रहते हैं""",
    },
    "about_glossary_heading": {"en": "📖 Key terms, in plain language", "kn": "📖 ಪ್ರಮುಖ ಪದಗಳು, ಸರಳ ಭಾಷೆಯಲ್ಲಿ", "hi": "📖 मुख्य शब्द, सरल भाषा में"},
    "glossary_term": {"en": "Term", "kn": "ಪದ", "hi": "शब्द"},
    "glossary_meaning": {"en": "What it means", "kn": "ಇದರ ಅರ್ಥ", "hi": "इसका मतलब"},
    "glossary_sigma_term": {
        "en": "σ score (sigma / standard deviation)", "kn": "σ ಸ್ಕೋರ್ (ಸಿಗ್ಮಾ / ಸ್ಟ್ಯಾಂಡರ್ಡ್ ಡಿವಿಯೇಶನ್)", "hi": "σ स्कोर (सिग्मा / स्टैंडर्ड डिविएशन)",
    },
    "glossary_sigma_meaning": {
        "en": "A measure of \"how unusual is this compared to normal?\" A σ score of 2 means a value is "
              "about twice as far from the typical/average value as most others ever get — the higher the "
              "number, the more it stands out. CivicPulse flags anything ≥ 1.5σ as worth a second look; "
              "anything above ~2.5–3σ is a genuine outlier, not just normal day-to-day variation.",
        "kn": "\"ಇದು ಸಾಮಾನ್ಯಕ್ಕೆ ಹೋಲಿಸಿದರೆ ಎಷ್ಟು ಅಸಾಮಾನ್ಯ?\" ಎಂಬುದರ ಅಳತೆ. σ ಸ್ಕೋರ್ 2 ಎಂದರೆ ಒಂದು ಮೌಲ್ಯವು "
              "ಸಾಮಾನ್ಯ/ಸರಾಸರಿ ಮೌಲ್ಯದಿಂದ ಸುಮಾರು ಎರಡು ಪಟ್ಟು ದೂರವಿದೆ — ಸಂಖ್ಯೆ ಹೆಚ್ಚಾದಷ್ಟೂ, ಅದು ಹೆಚ್ಚು ಎದ್ದು ಕಾಣುತ್ತದೆ. "
              "CivicPulse ≥ 1.5σ ಆಗಿರುವ ಯಾವುದನ್ನಾದರೂ ಮತ್ತೊಮ್ಮೆ ನೋಡಬೇಕಾದದ್ದು ಎಂದು ಗುರುತಿಸುತ್ತದೆ; ~2.5–3σ ಗಿಂತ "
              "ಹೆಚ್ಚಿನದು ನಿಜವಾದ ಹೊರಬೆಲೆ, ಸಾಮಾನ್ಯ ದೈನಂದಿನ ವ್ಯತ್ಯಾಸವಲ್ಲ.",
        "hi": "\"यह सामान्य की तुलना में कितना असामान्य है?\" का माप। σ स्कोर 2 का मतलब है कि एक मान "
              "सामान्य/औसत मान से लगभग दोगुना दूर है — संख्या जितनी अधिक, उतना ही यह अलग दिखता है। "
              "CivicPulse ≥ 1.5σ वाली किसी भी चीज़ को दोबारा देखने लायक चिह्नित करता है; ~2.5–3σ से ऊपर "
              "कुछ भी एक वास्तविक आउटलायर है, सामान्य दैनिक बदलाव नहीं।",
    },
    "glossary_confidence_term": {"en": "Confidence score", "kn": "ವಿಶ್ವಾಸ ಸ್ಕೋರ್", "hi": "विश्वास स्कोर"},
    "glossary_confidence_meaning": {
        "en": "How much CivicPulse trusts its own numbers, based on three real signals: how much data "
              "there is, how recent it is, and how steady (vs. erratic) the daily pattern is — *not* a "
              "guess about whether the underlying problem is real.",
        "kn": "CivicPulse ತನ್ನ ಸ್ವಂತ ಸಂಖ್ಯೆಗಳನ್ನು ಎಷ್ಟು ನಂಬುತ್ತದೆ, ಮೂರು ನೈಜ ಸಂಕೇತಗಳ ಆಧಾರದ ಮೇಲೆ: ಎಷ್ಟು ಡೇಟಾ "
              "ಇದೆ, ಅದು ಎಷ್ಟು ಇತ್ತೀಚಿನದು, ಮತ್ತು ದೈನಂದಿನ ಮಾದರಿ ಎಷ್ಟು ಸ್ಥಿರವಾಗಿದೆ (ಅನಿಯಮಿತಕ್ಕೆ ವಿರುದ್ಧವಾಗಿ) — "
              "ಮೂಲಭೂತ ಸಮಸ್ಯೆ ನಿಜವೇ ಎಂಬುದರ ಬಗ್ಗೆ ಊಹೆ *ಅಲ್ಲ*.",
        "hi": "CivicPulse अपनी खुद की संख्याओं पर कितना भरोसा करता है, तीन वास्तविक संकेतों के आधार पर: "
              "कितना डेटा है, यह कितना हालिया है, और दैनिक पैटर्न कितना स्थिर (बनाम अनियमित) है — यह "
              "इस बारे में अनुमान *नहीं* है कि अंतर्निहित समस्या वास्तविक है या नहीं।",
    },
    "glossary_urgency_term": {"en": "Urgency", "kn": "ತುರ್ತು", "hi": "तात्कालिकता"},
    "glossary_urgency_meaning": {
        "en": "How pressing the situation looks right now, blending severity, how many cases are still "
              "unresolved, and whether volume is trending up.",
        "kn": "ಪರಿಸ್ಥಿತಿ ಈಗ ಎಷ್ಟು ಒತ್ತಡದಂತೆ ಕಾಣುತ್ತದೆ, ತೀವ್ರತೆ, ಎಷ್ಟು ಪ್ರಕರಣಗಳು ಇನ್ನೂ ಬಗೆಹರಿಯದಿವೆ, ಮತ್ತು "
              "ಪ್ರಮಾಣ ಏರುತ್ತಿದೆಯೇ ಎಂಬುದನ್ನು ಸಂಯೋಜಿಸುತ್ತದೆ.",
        "hi": "स्थिति अभी कितनी दबावपूर्ण दिखती है, गंभीरता, कितने मामले अभी भी अनसुलझे हैं, और मात्रा "
              "बढ़ रही है या नहीं — इन्हें मिलाकर।",
    },
    "glossary_impact_term": {"en": "Impact", "kn": "ಪರಿಣಾಮ", "hi": "प्रभाव"},
    "glossary_impact_meaning": {
        "en": "How large-scale the issue is — driven by total volume and how concentrated it is in one area.",
        "kn": "ಸಮಸ್ಯೆ ಎಷ್ಟು ದೊಡ್ಡ-ಪ್ರಮಾಣದಲ್ಲಿದೆ — ಒಟ್ಟು ಪ್ರಮಾಣ ಮತ್ತು ಅದು ಒಂದು ಪ್ರದೇಶದಲ್ಲಿ ಎಷ್ಟು ಕೇಂದ್ರೀಕೃತವಾಗಿದೆ ಎಂಬುದರಿಂದ ನಡೆಸಲ್ಪಡುತ್ತದೆ.",
        "hi": "समस्या कितनी बड़े पैमाने पर है — कुल मात्रा और यह एक क्षेत्र में कितनी केंद्रित है, इससे संचालित।",
    },
    "glossary_severity_term": {"en": "Severity index", "kn": "ತೀವ್ರತೆ ಸೂಚ್ಯಂಕ", "hi": "गंभीरता सूचकांक"},
    "glossary_severity_meaning": {
        "en": "The average severity level (low/medium/high/critical) across all records, scaled 0–100.",
        "kn": "ಎಲ್ಲಾ ದಾಖಲೆಗಳಾದ್ಯಂತ ಸರಾಸರಿ ತೀವ್ರತೆ ಮಟ್ಟ (ಕಡಿಮೆ/ಮಧ್ಯಮ/ಹೆಚ್ಚು/ತೀವ್ರ), 0–100 ಪ್ರಮಾಣದಲ್ಲಿ.",
        "hi": "सभी रिकॉर्ड में औसत गंभीरता स्तर (कम/मध्यम/उच्च/गंभीर), 0–100 पैमाने पर।",
    },
    "glossary_hotspot_term": {"en": "Hotspot score (on the map)", "kn": "ಹಾಟ್‌ಸ್ಪಾಟ್ ಸ್ಕೋರ್ (ನಕ್ಷೆಯಲ್ಲಿ)", "hi": "हॉटस्पॉट स्कोर (मानचित्र पर)"},
    "glossary_hotspot_meaning": {
        "en": "One combined score per area blending complaint volume, severity, and how many cases are "
              "still open — the number behind each map marker's size.",
        "kn": "ಪ್ರತಿ ಪ್ರದೇಶಕ್ಕೆ ಒಂದು ಸಂಯೋಜಿತ ಸ್ಕೋರ್ ದೂರು ಪ್ರಮಾಣ, ತೀವ್ರತೆ, ಮತ್ತು ಎಷ್ಟು ಪ್ರಕರಣಗಳು ಇನ್ನೂ "
              "ತೆರೆದಿವೆ ಎಂಬುದನ್ನು ಸಂಯೋಜಿಸುತ್ತದೆ — ಪ್ರತಿ ನಕ್ಷೆ ಮಾರ್ಕರ್‌ನ ಗಾತ್ರದ ಹಿಂದಿನ ಸಂಖ್ಯೆ.",
        "hi": "प्रति क्षेत्र एक संयुक्त स्कोर जो शिकायत मात्रा, गंभीरता, और कितने मामले अभी भी खुले हैं — "
              "इन्हें मिलाता है — हर मानचित्र मार्कर के आकार के पीछे की संख्या।",
    },
}


# ---------------------------------------------------------------- categorical values
# Flat lookup: lowercased raw/humanized value -> translation. Covers area,
# category, severity, status, and department -- the columns actually shown
# as labels on cards, charts, the map, and the forecast table. complaint_type
# (24 free-text values) and raw dataframe preview cells are left as uploaded:
# they're either reproduced verbatim in the audit-facing raw preview, or
# folded into Gemini's own in-language prose rather than rendered as a
# standalone chip anywhere.
VALUE_TRANSLATIONS: dict[str, dict[str, str]] = {
    "kn": {
        # areas (Bengaluru BBMP wards)
        "koramangala": "ಕೋರಮಂಗಲ", "jayanagar": "ಜಯನಗರ", "malleshwaram": "ಮಲ್ಲೇಶ್ವರಂ",
        "basavanagudi": "ಬಸವನಗುಡಿ", "rajajinagar": "ರಾಜಾಜಿನಗರ", "btm layout": "ಬಿಟಿಎಂ ಲೇಔಟ್",
        "domlur": "ಡೊಮ್ಲೂರ್", "vijayanagar": "ವಿಜಯನಗರ",
        # categories
        "waste collection": "ತ್ಯಾಜ್ಯ ಸಂಗ್ರಹಣೆ", "water supply": "ನೀರು ಸರಬರಾಜು", "roads": "ರಸ್ತೆಗಳು",
        "public health": "ಸಾರ್ವಜನಿಕ ಆರೋಗ್ಯ", "sanitation": "ನೈರ್ಮಲ್ಯ", "noise": "ಶಬ್ದ",
        # severity
        "low": "ಕಡಿಮೆ", "medium": "ಮಧ್ಯಮ", "high": "ಹೆಚ್ಚು", "critical": "ತೀವ್ರ",
        # status
        "open": "ತೆರೆದಿದೆ", "in progress": "ಪ್ರಗತಿಯಲ್ಲಿದೆ", "resolved": "ಪರಿಹರಿಸಲಾಗಿದೆ", "escalated": "ಹೆಚ್ಚಿಸಲಾಗಿದೆ",
        # departments
        "sanitation dept": "ನೈರ್ಮಲ್ಯ ಇಲಾಖೆ", "water board": "ಜಲ ಮಂಡಳಿ", "public works": "ಲೋಕೋಪಯೋಗಿ ಇಲಾಖೆ",
        "environment cell": "ಪರಿಸರ ಕೋಶ", "health dept": "ಆರೋಗ್ಯ ಇಲಾಖೆ",
        "n/a": "ಲಭ್ಯವಿಲ್ಲ", "—": "—",
    },
    "hi": {
        "koramangala": "कोरमंगला", "jayanagar": "जयनगर", "malleshwaram": "मल्लेश्वरम",
        "basavanagudi": "बसवनगुड़ी", "rajajinagar": "राजाजीनगर", "btm layout": "बीटीएम लेआउट",
        "domlur": "डोमलूर", "vijayanagar": "विजयनगर",
        "waste collection": "कचरा संग्रहण", "water supply": "जल आपूर्ति", "roads": "सड़कें",
        "public health": "सार्वजनिक स्वास्थ्य", "sanitation": "स्वच्छता", "noise": "शोर",
        "low": "कम", "medium": "मध्यम", "high": "अधिक", "critical": "गंभीर",
        "open": "खुला", "in progress": "प्रगति पर", "resolved": "हल हो गया", "escalated": "आगे बढ़ाया गया",
        "sanitation dept": "स्वच्छता विभाग", "water board": "जल बोर्ड", "public works": "लोक निर्माण विभाग",
        "environment cell": "पर्यावरण प्रकोष्ठ", "health dept": "स्वास्थ्य विभाग",
        "n/a": "उपलब्ध नहीं", "—": "—",
    },
}


def T(lang: str, key: str, **kwargs: Any) -> str:
    """Look up a UI-chrome string in the active language, falling back to
    English (then the raw key) if a translation is missing."""
    entry = UI_STRINGS.get(key)
    if entry is None:
        return key
    s = entry.get(lang) or entry.get("en") or key
    return s.format(**kwargs) if kwargs else s


def L(lang: str, value: Any) -> Any:
    """Translate a categorical DISPLAY value (already humanized) into the
    active language when known; otherwise return it unchanged. Never touches
    numbers, dates, or None."""
    if lang == "en" or value is None or not isinstance(value, str):
        return value
    table = VALUE_TRANSLATIONS.get(lang)
    if not table:
        return value
    return table.get(value.strip().lower(), value)

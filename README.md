# 🏙️ CivicPulse AI

> **Community decision intelligence, powered by Gemini on Google Cloud.**
> *Not just answers — better decisions.*

CivicPulse AI is a decision-intelligence dashboard that lets a city or community
team ask natural-language questions about local data (citizen complaints,
sanitation, water, roads, noise, public health) and instantly get **patterns,
anomalies, a decision scoreboard, and an auto-generated action memo**.

It is **not** a generic chatbot. It computes real analytics in Python first, then
uses a **small, low-cost Gemini model** (`gemini-3.1-flash-lite`) to explain the
numbers and recommend concrete next steps — so the AI never hallucinates
statistics.

---

## ✨ What makes it stand out

| Feature | Description |
|---|---|
| 🧮 **Deterministic-first analytics** | Counts, weekly trends, severity mix & anomaly flags computed in Python — cheap, fast, reliable. |
| 💬 **Natural-language Q&A** | Ask *"What should we prioritize this week?"* — grounded strictly in your data. |
| 🚨 **Explainable anomaly detection** | Simple z-score thresholds (≥1.5σ) flag spikes by area, category & time. |
| 🎯 **Decision Scoreboard** | Urgency · Impact · Confidence · Severity scores (0–100) tell teams what to act on. |
| 📝 **One-click Executive Brief** | The wow feature: a downloadable, decision-ready city action memo from a single Gemini call. |
| 🔍 **Explainability panel** | Plain-language reasoning behind every recommendation. |
| 📥 **Multi-format ingest** | CSV, JSON, PDF text, or pasted text — with forgiving column auto-mapping. |

---

## 🏗️ Architecture

```
┌──────────────┐   upload    ┌───────────────┐   structured   ┌──────────────────┐
│  User / City │ ──────────▶ │ data_loader   │ ─────────────▶ │  analytics.py    │
│  team        │  CSV/JSON/  │ (normalize)   │   JSON facts   │ counts · trends  │
└──────────────┘  PDF/text   └───────────────┘                │ anomalies·scores │
        ▲                                                      └────────┬─────────┘
        │  decisions, memo, answers                                     │ analytics JSON
        │                                                               ▼
┌───────┴────────┐   report/JSON   ┌───────────────────┐   grounded    ┌──────────────┐
│ Streamlit UI   │ ◀────────────── │ gemini_client.py  │ ◀──prompt───── │ prompt_      │
│ dashboard      │                 │ (Gemini flash-lite)│               │ templates.py │
└────────────────┘                 └───────────────────┘               └──────────────┘
                                            │
                              Vertex AI  ──OR──  Gemini Developer API
```

**Stack:** Streamlit · Python · Gemini (Vertex AI or Gemini API) · Cloud Run · `gcloud` CLI.

---

## 📁 Project structure

```
civicpulse-ai/
├── app.py                  # Streamlit entry — dashboard UI (tabs, cards, charts)
├── src/
│   ├── data_loader.py      # CSV/JSON/PDF/text ingest + column normalization
│   ├── analytics.py        # deterministic analytics: counts, trends, anomalies, scores
│   ├── gemini_client.py    # reusable Gemini wrapper (retry + offline fallback)
│   ├── prompt_templates.py # civic-analyst prompts (grounded, JSON output)
│   └── utils.py            # shared helpers (column aliases, JSON extraction)
├── sample_data/
│   ├── citizen_complaints.csv   # ~370 realistic rows (bundled demo)
│   ├── citizen_complaints.json
│   └── generate_sample.py       # regenerate the dataset
├── requirements.txt
├── Dockerfile              # slim container for Cloud Run
├── cloudbuild.yaml         # Cloud Build → Cloud Run pipeline
├── deploy.sh               # one-command Cloud Run deploy
├── setup_gcloud.sh         # enable APIs + auth via gcloud
├── .env.example
└── README.md
```

---

## 🚀 Quickstart (local, ~2 minutes)

```bash
# 1. Clone & enter
git clone https://github.com/Yadu080/CivicPulse-AI.git
cd civicpulse-ai

# 2. (optional) virtualenv
python -m venv .venv && source .venv/bin/activate

# 3. Install
pip install -r requirements.txt

# 4. Add a Gemini key (get one free at https://aistudio.google.com/apikey)
cp .env.example .env
#   then edit .env and set GEMINI_API_KEY=...

# 5. Run
streamlit run app.py
```

Open http://localhost:8501 → click **⚡ Load demo dataset** → explore the tabs.

> 💡 **No key? No problem.** The app runs fully with a built-in deterministic
> fallback (analytics + rule-based brief). Add a key to unlock full Gemini
> explanations and Q&A.

---

## ☁️ Deploy to Google Cloud Run with `gcloud`

### One-time setup

```bash
# Authenticate and enable APIs (Cloud Run, Vertex AI, Cloud Build, Artifact Registry)
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com aiplatform.googleapis.com \
                       cloudbuild.googleapis.com artifactregistry.googleapis.com

# …or just run the helper:
./setup_gcloud.sh YOUR_PROJECT_ID us-central1
```

### Deploy (Vertex AI backend — no API key needed)

```bash
./deploy.sh YOUR_PROJECT_ID us-central1
```

### Deploy (Gemini Developer API key)

```bash
export GEMINI_API_KEY=your_key_here
./deploy.sh YOUR_PROJECT_ID us-central1
```

Under the hood `deploy.sh` runs:

```bash
gcloud run deploy civicpulse-ai \
  --source . --region us-central1 --allow-unauthenticated \
  --memory 512Mi --cpu 1 --min-instances 0 --max-instances 3 \
  --set-env-vars GEMINI_MODEL=gemini-3.1-flash-lite,GOOGLE_GENAI_USE_VERTEXAI=true,...
```

When it finishes it prints your **public URL** (e.g.
`https://civicpulse-ai-xxxxxxxx-uc.a.run.app`).

> **Vertex AI note:** grant the Cloud Run service account the
> `roles/aiplatform.user` role so it can call Gemini:
> ```bash
> PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')
> gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
>   --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
>   --role="roles/aiplatform.user"
> ```

---

## 🤖 Gemini integration

- **Wrapper:** `src/gemini_client.py` — auto-detects Vertex AI vs. Gemini API,
  requests JSON output, retries transient errors twice, and falls back to a
  deterministic offline report if the model is unreachable.
- **Model:** `gemini-3.1-flash-lite` by default (smallest/cheapest tier). Override
  with the `GEMINI_MODEL` env var.
- **Grounding:** every prompt embeds the computed analytics JSON and instructs the
  model to *use only the provided numbers* — see `src/prompt_templates.py`.

---

## 💰 Cost design

- **One Gemini call per meaningful action** (brief / question), never per keystroke.
- **Flash-lite model tier** — the cheapest Gemini option.
- **Deterministic analytics in Python** do the heavy lifting for free.
- **Local sample data** — no database, no Cloud Storage required.
- **Cloud Run scale-to-zero** (`--min-instances 0`) → you pay ~nothing when idle.
- Modest **512Mi / 1 CPU** container settings.

---

## 📊 Sample dataset

`sample_data/citizen_complaints.csv` (~370 rows over ~8 weeks) with columns:
`date, area, category, complaint_type, severity, status, department, notes`.

It contains a **persistent hotspot** (Riverside), a **rising trend**, and a
**planted anomaly** (a Waste Collection surge in the final week) so the demo
reliably shows trends, hotspots, anomalies, and actions. Regenerate with:

```bash
python sample_data/generate_sample.py
```

---

## 🧪 Troubleshooting

| Symptom | Fix |
|---|---|
| "Gemini offline" banner | Set `GEMINI_API_KEY` in `.env`, or configure Vertex AI env vars. |
| Vertex AI 403 on Cloud Run | Grant the runtime SA `roles/aiplatform.user` (see above). |
| PDF has no text | Scanned PDFs need OCR; this app reads text-based PDFs only. |
| Upload columns not recognized | Rename to `area`, `category`, `date`, etc. (aliases in `utils.py`). |

---

## 📄 License

MIT — free to use, adapt, and demo.

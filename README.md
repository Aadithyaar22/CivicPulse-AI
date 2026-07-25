# 🏙️ CivicPulse AI

> **Community decision intelligence, powered by Gemini on Google Cloud.**
> *Not just answers — better decisions.*

CivicPulse AI is a decision-intelligence dashboard that lets a city or community
team ask natural-language questions about local data (citizen complaints,
sanitation, water, roads, noise, public health) and instantly get **patterns,
anomalies, a decision scoreboard, and an auto-generated action memo**.

It is **not** a generic chatbot. It computes real analytics in Python first, then
uses a **small, low-cost Gemini model** (`gemini-2.5-flash-lite`) to explain the
numbers and recommend concrete next steps — so the AI never hallucinates
statistics.

---

## ✨ What makes it stand out

| Feature | Description |
|---|---|
| 🧮 **Deterministic-first analytics** | Counts, weekly trends, severity mix & anomaly flags computed in Python — cheap, fast, reliable. |
| 💬 **Agentic multi-turn chat** | Ask *"Compare Koramangala vs Domlur this month"*, then keep asking follow-ups — Gemini calls real query tools (`filter_records`, `get_top_complaints`, `get_summary_stats`) against your live data and remembers the conversation. It never computes numbers itself, only chooses which deterministic query to run. |
| 🚨 **Explainable anomaly detection** | Simple z-score thresholds (≥1.5σ) flag spikes by area, category & time. |
| 🎯 **Decision Scoreboard** | Urgency · Impact · Confidence · Severity scores (0–100) tell teams what to act on. |
| 📝 **One-click Executive Brief** | The wow feature: a downloadable, decision-ready city action memo from a single Gemini call. |
| 🔍 **Explainability panel** | Plain-language reasoning behind every recommendation. |
| 📥 **Multi-format ingest** | CSV, JSON, PDF text, or pasted text — with forgiving column auto-mapping. |
| 🗄️ **Persistent brief history** | Every generated brief is saved to Firestore, so a team can see how a location trends across sessions, not just today's snapshot. |
| 🔄 **Reload-safe sessions** | Loaded data and chat history survive a page refresh — restored from Firestore, keyed by a session id in the URL, auto-expiring after 24h. |
| 🔔 **Automated weekly brief** | A Cloud Scheduler job triggers the same analytics → Gemini pipeline on a cron and emails the result — insight delivered to an inbox with nobody opening the dashboard. |

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
  --memory 2Gi --cpu 2 --min-instances 0 --max-instances 3 --concurrency 4 \
  --set-env-vars GEMINI_MODEL=gemini-2.5-flash-lite,GOOGLE_GENAI_USE_VERTEXAI=true,...
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
- **Model:** `gemini-2.5-flash-lite` by default (smallest/cheapest tier). Override
  with the `GEMINI_MODEL` env var.
- **Grounding:** the executive brief and text-summary prompts embed the computed
  analytics JSON and instruct the model to *use only the provided numbers* — see
  `src/prompt_templates.py`.
- **Agentic Q&A:** the Ask AI tab instead gives Gemini function-calling tools
  (`src/qa_tools.py`) that query the real uploaded DataFrame on demand — so
  multi-step questions (comparisons, drill-downs) get real evidence instead of
  reasoning over one static snapshot. Every tool call and its real record count
  is shown in an expandable trace under each answer. Guardrails: unmatched
  areas/categories return an explicit error + the real valid values (never a
  guess), zero-result queries are labeled as genuine zeros, and any failure in
  the tool-calling loop falls back to the static grounded Q&A path.

---

## 🗄️ Brief history (Firestore)

Every successfully generated Executive Brief (from the UI or the scheduled
job below) is saved to a Firestore Native-mode database — same numbers, same
title, same recommended actions. The Recommendations tab shows the 5 most
recent under "📜 Recent briefs." This is entirely optional: if Firestore isn't
reachable (no ADC locally, API disabled, no database), the app keeps working
exactly as before — persistence just silently turns off. See `src/history_store.py`.

One-time setup:
```bash
gcloud services enable firestore.googleapis.com --project YOUR_PROJECT_ID
gcloud firestore databases create --location=us-central1 --type=firestore-native --project YOUR_PROJECT_ID
```

---

## 🔄 Reload-safe sessions (Firestore)

`st.session_state` is in-memory per browser session — a page reload opens a
fresh one server-side, so without this, refreshing wipes your loaded data and
chat. Instead, app.py keeps a session id in the URL (`?sid=...`, which *does*
survive a reload) and saves the loaded dataset + chat history + brief to
Firestore after every meaningful change; on a fresh session it looks up that
id and restores them. See `src/session_store.py`.

Entirely optional and best-effort, same as brief history above:
- If Firestore isn't reachable, the app just works as before (reload resets it).
- A dataset too large for Firestore's 1 MiB document cap (roughly a few
  thousand rows, depending on column count) silently isn't persisted —
  reload will reset that session's data, nothing else is affected.
- Uses the same Firestore database as brief history — no extra setup beyond
  what's above, **except** the TTL policy (so old sessions actually get
  reclaimed instead of just being ignored once expired):
```bash
gcloud firestore fields ttls update expires_at \
  --collection-group=civicpulse_sessions \
  --enable-ttl \
  --project YOUR_PROJECT_ID
```

---

## 🔔 Automated weekly brief (Cloud Scheduler + Gmail)

A second, small Cloud Function (`main.py` at the repo root, entry point
`scheduled_brief`) runs the exact same pipeline as the "Generate Executive
Brief" button — `analytics.compute_insights` → `GeminiClient.executive_brief`
→ save to Firestore — then emails the result via Gmail SMTP. It's what turns
CivicPulse from a dashboard someone has to remember to open into a service
that delivers a decision on its own schedule.

**Department-scoped routing:** on top of the citywide brief (sent to
`ALERT_RECIPIENT`), the function also finds every department present in the
data and sends each one its own brief — computed from *only that
department's* records, not the whole city. Recipients come from
`src/department_contacts.py` (department name → list of emails, so one
department can route to multiple sub-offices). A department with no
configured contact is skipped and reported in the response JSON, never
guessed. Edit that file to point departments at real addresses.

**One-time setup:**

1. On the sending Gmail account, enable 2-Step Verification, then generate an
   App Password: <https://myaccount.google.com/apppasswords>. **Never paste
   this into chat, code, or a commit** — it goes straight into Secret Manager.
   ```bash
   gcloud secrets create civicpulse-gmail-app-password --replication-policy=automatic --project YOUR_PROJECT_ID
   gcloud secrets versions add civicpulse-gmail-app-password --data-file=- --project YOUR_PROJECT_ID
   # (paste the 16-character app password, then Ctrl+D)
   gcloud secrets add-iam-policy-binding civicpulse-gmail-app-password \
     --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor" --project YOUR_PROJECT_ID
   ```

2. Deploy the function:
   ```bash
   gcloud functions deploy civicpulse-scheduled-brief \
     --gen2 --runtime=python312 --region=us-central1 \
     --source=. --entry-point=scheduled_brief --trigger-http \
     --no-allow-unauthenticated --memory=512Mi --timeout=300s \
     --set-env-vars=GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1,ALERT_SENDER=you@gmail.com,ALERT_RECIPIENT=official@example.com,GEMINI_MODEL=gemini-2.5-flash-lite \
     --set-secrets=GMAIL_APP_PASSWORD=civicpulse-gmail-app-password:latest \
     --project YOUR_PROJECT_ID
   ```

3. Create a dedicated invoker service account and a weekly Cloud Scheduler job:
   ```bash
   gcloud iam service-accounts create civicpulse-scheduler --project YOUR_PROJECT_ID
   gcloud functions add-invoker-policy-binding civicpulse-scheduled-brief \
     --region=us-central1 \
     --member="serviceAccount:civicpulse-scheduler@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --project YOUR_PROJECT_ID
   gcloud scheduler jobs create http civicpulse-weekly-brief \
     --location=us-central1 --schedule="0 8 * * 1" --time-zone="Asia/Kolkata" \
     --uri="<function-url-from-step-2>" --http-method=POST \
     --oidc-service-account-email="civicpulse-scheduler@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --project YOUR_PROJECT_ID
   ```

Optional: set `CIVICPULSE_DATA_GCS_URI` (a `gs://` or `https://` CSV URL) as
an env var on the function to point scheduled runs at a real dataset instead
of the bundled sample — it goes through the same column auto-mapping as a
manual upload.

Cost: Cloud Scheduler's first 3 jobs/month are free, the function scales to
zero between runs, and Secret Manager's free tier covers a handful of active
secrets — the only per-run cost is one small Gemini call (a fraction of a cent).

---

## 💰 Cost design

- **One Gemini call per meaningful action** (brief / question), never per keystroke.
- **Flash-lite model tier** — the cheapest Gemini option.
- **Deterministic analytics in Python** do the heavy lifting for free.
- **Local sample data** — no database, no Cloud Storage required.
- **Cloud Run scale-to-zero** (`--min-instances 0`) → you pay ~nothing when idle.
- **2Gi / 2 CPU** container settings — sized for real-world CSV uploads
  (pandas + Streamlit + Plotly + statsmodels resident together needs more
  than the 512Mi that's enough for the small bundled demo dataset alone;
  512Mi was silently OOM-killing the container on larger uploads). Still
  costs nothing while idle thanks to scale-to-zero — you only pay for the
  CPU/memory-seconds of active requests.

---

## 📊 Sample dataset

`sample_data/citizen_complaints.csv` (~370 rows over ~8 weeks) across 8 real
Bengaluru wards (Koramangala, Jayanagar, Malleshwaram, Basavanagudi,
Rajajinagar, BTM Layout, Domlur, Vijayanagar) with columns:
`date, area, category, complaint_type, severity, status, department, notes`.

It contains a **persistent hotspot** (Koramangala), a **rising trend**, and a
**planted anomaly** (a Waste Collection surge in the final week) so the demo
reliably shows trends, real-ward hotspot mapping, anomalies, and actions.
Regenerate with:

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

## ☁️ Google Cloud services & tools used

| Service | What it's used for |
|---|---|
| **Vertex AI (Gemini 2.5 Flash-Lite)** | The core model — explains analytics, drives agentic Q&A via function calling, drafts the Executive Brief. Accessed via Vertex AI (no exposed API key) in production. |
| **Cloud Run** | Hosts the main Streamlit app, scale-to-zero so idle cost is $0. |
| **Cloud Functions (2nd gen)** | Hosts the scheduled Executive Brief job (`main.py`) — built on Cloud Run under the hood. |
| **Cloud Scheduler** | Cron trigger (weekly) for the automated brief-and-email job. |
| **Firestore** | Stores generated brief history so trends are visible across sessions, not just the current upload. |
| **Secret Manager** | Holds the Gmail App Password used to send the scheduled brief email — never in code or env vars in plaintext. |
| **Cloud Build** | Builds the container image on every `gcloud run deploy --source .`. |
| **Artifact Registry** | Stores the built container images. |
| **IAM** | Least-privilege service accounts — a dedicated `civicpulse-scheduler` account can only invoke the one function it needs. |
| **Cloud Logging** | Request/error logs for both the app and the scheduled function (used to diagnose the OOM and truncation bugs found during testing). |
| **Gmail (SMTP)** | Delivers the automated weekly brief email. |
| **`gcloud` CLI** | All deployment, IAM, and infra setup in this repo's scripts. |

---

## 👥 Team

**Team CodeSickOs**
- Aadithya A R
- Yadunandan M N
- Kenisha P

---

## 📄 License

MIT — free to use, adapt, and demo.

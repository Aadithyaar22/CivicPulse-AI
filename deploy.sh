#!/usr/bin/env bash
# Build & deploy CivicPulse AI to Cloud Run with a single command.
# Usage:  ./deploy.sh YOUR_PROJECT_ID [REGION] [SERVICE_NAME]
#
# Requires: gcloud CLI, an enabled project (see setup_gcloud.sh).
# For Gemini: pass GEMINI_API_KEY in your env, OR use --use-vertex flag logic below.
set -euo pipefail

PROJECT_ID="${1:-}"
REGION="${2:-us-central1}"
SERVICE="${3:-civicpulse-ai}"
MODEL="${GEMINI_MODEL:-gemini-2.5-pro}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "Usage: ./deploy.sh YOUR_PROJECT_ID [REGION] [SERVICE_NAME]"
  exit 1
fi

gcloud config set project "${PROJECT_ID}"

# Choose credentials mode:
#  - If GEMINI_API_KEY is set, pass it as an env var (Gemini Developer API).
#  - Otherwise use Vertex AI with the Cloud Run service account.
# URL of the scheduled-brief Cloud Function (see README's "Automated weekly
# brief" section) -- lets the "Send scheduled reports now" button in the app
# trigger it on demand. Harmless if that function isn't deployed; the app
# just shows the button as unavailable.
SCHEDULED_BRIEF_FUNCTION_URL="${SCHEDULED_BRIEF_FUNCTION_URL:-https://${REGION}-${PROJECT_ID}.cloudfunctions.net/civicpulse-scheduled-brief}"
# Same idea, for the "Send Real-Time Alert" button in the Recommendations
# tab (fires the moment a brief has an immediate-urgency action, instead of
# waiting for the weekly schedule). Harmless if that function isn't deployed.
REALTIME_ALERT_FUNCTION_URL="${REALTIME_ALERT_FUNCTION_URL:-https://${REGION}-${PROJECT_ID}.cloudfunctions.net/civicpulse-realtime-alert}"

ENV_VARS="GEMINI_MODEL=${MODEL},SCHEDULED_BRIEF_FUNCTION_URL=${SCHEDULED_BRIEF_FUNCTION_URL},REALTIME_ALERT_FUNCTION_URL=${REALTIME_ALERT_FUNCTION_URL}"
if [[ -n "${GEMINI_API_KEY:-}" ]]; then
  echo "==> Deploying with Gemini Developer API key."
  ENV_VARS="${ENV_VARS},GEMINI_API_KEY=${GEMINI_API_KEY}"
else
  echo "==> No GEMINI_API_KEY found; deploying with Vertex AI backend."
  ENV_VARS="${ENV_VARS},GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION}"
fi

echo "==> Building & deploying '${SERVICE}' to Cloud Run (${REGION})..."
# `gcloud run deploy --source .` uses Cloud Build to build the Dockerfile.
gcloud run deploy "${SERVICE}" \
  --source . \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 3 \
  --concurrency 4 \
  --timeout 300 \
  --port 8080 \
  --set-env-vars "${ENV_VARS}"

echo ""
echo "==> Deployed. Public URL:"
gcloud run services describe "${SERVICE}" --region "${REGION}" --format='value(status.url)'

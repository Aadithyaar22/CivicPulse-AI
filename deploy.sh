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
MODEL="${GEMINI_MODEL:-gemini-3.1-flash-lite}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "Usage: ./deploy.sh YOUR_PROJECT_ID [REGION] [SERVICE_NAME]"
  exit 1
fi

gcloud config set project "${PROJECT_ID}"

# Choose credentials mode:
#  - If GEMINI_API_KEY is set, pass it as an env var (Gemini Developer API).
#  - Otherwise use Vertex AI with the Cloud Run service account.
ENV_VARS="GEMINI_MODEL=${MODEL}"
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
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --concurrency 20 \
  --timeout 300 \
  --port 8080 \
  --set-env-vars "${ENV_VARS}"

echo ""
echo "==> Deployed. Public URL:"
gcloud run services describe "${SERVICE}" --region "${REGION}" --format='value(status.url)'

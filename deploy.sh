#!/bin/bash
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="saven-backend"

gcloud run deploy $SERVICE_NAME \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=$PROJECT_ID

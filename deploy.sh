#!/bin/bash

# Deployment script for Google Cloud Run
# Deploys both backend and frontend services

set -e

echo "🚀 Deploying Grok Onboarding Platform to Google Cloud Run..."

# Get project ID
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"

echo "📦 Project: $PROJECT_ID"
echo "🌍 Region: $REGION"
echo ""

# Deploy Backend
echo "🔧 Deploying Backend API..."
cd backend

gcloud run deploy grok-onboarding-backend \
  --source . \
  --allow-unauthenticated \
  --region $REGION \
  --platform managed \
  --timeout 300 \
  --memory 1Gi \
  --set-env-vars XAI_API_KEY=$XAI_API_KEY,XAI_BASE_URL=https://api.x.ai/v1,XAI_MODEL=grok-4-1-fast-reasoning

BACKEND_URL=$(gcloud run services describe grok-onboarding-backend --region $REGION --format 'value(status.url)')
echo "✅ Backend deployed at: $BACKEND_URL"
echo ""

# Deploy Frontend
echo " Deploying Frontend..."
cd ../client

# Build and Deploy Frontend
echo "🏗️  Building Frontend Container..."
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_NEXT_PUBLIC_API_URL=$BACKEND_URL \
  .

echo "🚀 Deploying Frontend Service..."
gcloud run deploy grok-onboarding-frontend \
  --image gcr.io/$PROJECT_ID/grok-onboarding-frontend \
  --allow-unauthenticated \
  --region $REGION \
  --platform managed \
  --timeout 60 \
  --memory 512Mi

FRONTEND_URL=$(gcloud run services describe grok-onboarding-frontend --region $REGION --format 'value(status.url)')
echo "✅ Frontend deployed at: $FRONTEND_URL"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Deployment Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Backend API:  $BACKEND_URL"
echo "Frontend App: $FRONTEND_URL"
echo ""
echo "🧪 Test your API:"
echo "curl \"$BACKEND_URL/\""
echo "curl \"$BACKEND_URL/api/codebases\""
echo ""
echo "🌐 Open in browser:"
echo "$FRONTEND_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# GitHub Auto-Deploy Setup Guide

##  This enables auto-deployment on every GitHub push!

### Step 1: Complete Google Cloud Login
1. Complete the browser login that opened
2. Run: `gcloud projects create ai-chatbot-jb020725`
3. Run: `gcloud config set project ai-chatbot-jb020725`

### Step 2: Create Service Account for GitHub
```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --description="GitHub Actions deployment" \
  --display-name="GitHub Actions"

# Add roles
gcloud projects add-iam-policy-binding ai-chatbot-jb020725 \
  --member="serviceAccount:github-actions@ai-chatbot-jb020725.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding ai-chatbot-jb020725 \
  --member="serviceAccount:github-actions@ai-chatbot-jb020725.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding ai-chatbot-jb020725 \
  --member="serviceAccount:github-actions@ai-chatbot-jb020725.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.editor"

# Create and download key
gcloud iam service-accounts keys create github-key.json \
  --iam-account=github-actions@ai-chatbot-jb020725.iam.gserviceaccount.com
```

### Step 3: Add GitHub Secrets
Go to: https://github.com/jb020725/AI_Chat/settings/secrets/actions

Add these secrets:
- `GCP_SA_KEY`: Contents of github-key.json file
- `GCP_PROJECT_ID`: ai-chatbot-jb020725

### Step 4: Enable APIs
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable storage.googleapis.com
```

### Step 5: Push Changes
```bash
git add .
git commit -m "Add GitHub auto-deployment"
git push origin main
```

##  Result: Auto-deploy on every push!
- Backend: https://ai-chatbot-backend-xxxxx-uc.a.run.app
- Frontend: https://storage.googleapis.com/ai-chatbot-jb020725-frontend/index.html

##  Environment Variables
Add in Cloud Run console:
- GEMINI_API_KEY
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY

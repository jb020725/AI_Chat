# GitHub Auto-Deploy Setup Commands
# Run these after billing is enabled

# 1. Enable APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com storage.googleapis.com iam.googleapis.com

# 2. Create service account for GitHub Actions
gcloud iam service-accounts create github-actions \
    --description="GitHub Actions deployment" \
    --display-name="GitHub Actions"

# 3. Add required roles
gcloud projects add-iam-policy-binding ai-chatbot-jb020725 \
    --member="serviceAccount:github-actions@ai-chatbot-jb020725.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding ai-chatbot-jb020725 \
    --member="serviceAccount:github-actions@ai-chatbot-jb020725.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding ai-chatbot-jb020725 \
    --member="serviceAccount:github-actions@ai-chatbot-jb020725.iam.gserviceaccount.com" \
    --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding ai-chatbot-jb020725 \
    --member="serviceAccount:github-actions@ai-chatbot-jb020725.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

# 4. Create and download service account key
gcloud iam service-accounts keys create github-key.json \
    --iam-account=github-actions@ai-chatbot-jb020725.iam.gserviceaccount.com

# 5. Create storage bucket for frontend
gsutil mb gs://ai-chatbot-jb020725-frontend
gsutil web set -m index.html gs://ai-chatbot-jb020725-frontend
gsutil iam ch allUsers:objectViewer gs://ai-chatbot-jb020725-frontend

echo "Setup complete! Now add GitHub secrets and push to deploy."

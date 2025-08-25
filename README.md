# AI Chatbot - Production Ready 

## 🚀 **LIVE DEPLOYMENT URLs**

### **Frontend (Chatbot Interface):**
```
https://visa-chatbot-frontend-971031410928.us-central1.run.app
```

### **Backend (API Service):**
```
https://visa-chatbot-backend-971031410928.us-central1.run.app
```

### **Quick Access Commands:**
```bash
# Get current URLs (run from project root)
gcloud run services list --platform managed --region us-central1 --filter="metadata.name~visa-chatbot"

# Check deployment status
gcloud run services describe visa-chatbot-frontend --region us-central1
gcloud run services describe visa-chatbot-backend --region us-central1
```

### **Deployment Status:**
- ✅ **Frontend:** Live and connected to backend
- ✅ **Backend:** Live with RAG, Gemini API, and all functions
- ✅ **Auto-deployment:** Configured via GitHub Actions
- ✅ **Stable URLs:** Won't change on redeployment

---

A production-ready AI chatbot with lead capture, built with FastAPI + React + Google Gemini AI.

## Features 
-  AI-powered conversations with Gemini 2.5 Flash
-  Automatic lead capture and email notifications
-  Supabase database integration
-  Production-ready security
-  Fast and scalable

## Quick Deploy to Google Cloud 

### 1. Deploy Backend (Cloud Run)
```bash
cd backend
gcloud run deploy ai-chatbot-backend   --source .   --region us-central1   --allow-unauthenticated   --memory 2Gi   --cpu 1
```

### 2. Deploy Frontend (Cloud Storage)
```bash
cd frontend
npm install
npm run build
gsutil mb gs://your-project-id-frontend
gsutil web set -m index.html gs://your-project-id-frontend
gsutil -m cp -r dist/* gs://your-project-id-frontend
gsutil iam ch allUsers:objectViewer gs://your-project-id-frontend
```

### 3. Set Environment Variables
In Google Cloud Run, add these environment variables from `backend/production.env.template`

## Tech Stack 
- **Backend**: Python, FastAPI, Google Gemini AI
- **Frontend**: React, TypeScript, Vite
- **Database**: Supabase
- **Deployment**: Google Cloud Run + Storage

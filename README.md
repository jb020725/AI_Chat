# AI Consultancy Chatbot

A production-ready AI chatbot with function calling and lead capture, built with FastAPI + React + Google Gemini AI. Uses function calling for intelligent responses and automatic contact detection.

## 🚀 Features

- **AI-powered conversations** with Gemini 2.5 Flash
- **Function calling** for intelligent responses and lead capture
- **Session memory** for personalized conversations
- **Automatic contact detection** and database storage
- **Email notification system**
- **Supabase database integration**
- **Production-ready security** with rate limiting
- **Fast and scalable**

## 🌐 Live Deployment

### **Frontend (Chatbot Interface):**
```
https://ai-chatbot-frontend-irsvqln4dq-uc.a.run.app
```

### **Backend (API Service):**
```
https://ai-chatbot-backend-irsvqln4dq-uc.a.run.app
```

### **Quick Access Commands:**
```bash
# Get current URLs (run from project root)
gcloud run services list --platform managed --region us-central1 --filter="metadata.name~ai-chatbot"

# Check deployment status
gcloud run services describe ai-chatbot-frontend --region us-central1
gcloud run services describe ai-chatbot-backend --region us-central1
```

### **Deployment Status:**
- ✅ **Frontend:** Live and connected to backend
- ✅ **Backend:** Live with Function Calling, Gemini API, and all functions (RAG disabled)
- ✅ **Auto-deployment:** Configured via GitHub Actions
- ✅ **Stable URLs:** Won't change on redeployment

## 🏗️ Architecture

- **Backend**: FastAPI with function calling and session memory
- **Frontend**: React + TypeScript + Tailwind CSS
- **AI**: Google Gemini 2.5 Flash
- **Database**: Supabase
- **Deployment**: Google Cloud Run

## 📁 Project Structure

```
├── backend/                 # FastAPI backend
│   ├── app/                # Application code
│   │   ├── functions/      # Function calling system
│   │   ├── memory/         # Session memory system
│   │   ├── tools/          # Lead capture tools
│   │   └── utils/          # Utilities
│   ├── main.py             # Main application
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/                # Source code
│   ├── package.json        # Node dependencies
│   └── vite.config.ts      # Vite configuration
└── README.md               # This file
```

## 🚀 Quick Start

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

Create `.env` file in backend directory:

```env
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## 🔧 Configuration

- **Rate Limiting**: 60/minute, 1000/hour per IP
- **Concurrency**: Max 20 concurrent LLM calls
- **Supported Countries**: USA, UK, Australia, South Korea
- **Target Audience**: Nepali students

## 📊 API Endpoints

- `POST /api/chat` - Main chat endpoint
- `GET /health` - Health check
- `GET /api/leads` - Get captured leads
- `GET /memory/sessions` - Session management

## 🚀 Deployment

### Google Cloud Run

```bash
# Backend
gcloud run deploy visa-chatbot-backend --source backend

# Frontend
gcloud run deploy visa-chatbot-frontend --source frontend
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is proprietary software for AI Consultancy.

## 📞 Support

For support, contact AI Consultancy team.

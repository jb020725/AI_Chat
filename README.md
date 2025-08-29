# 🎓 AI Student Visa Consultancy Chatbot

A production-ready AI chatbot specializing in student visa guidance for Nepali students applying to USA, UK, Australia, and South Korea. Built with FastAPI + React + Google Gemini AI, featuring intelligent responses, lead capture, and multi-platform support.

## 🚀 Live Demo

### **🌐 Web Chatbot:**
```
https://ai-chatbot-frontend-irsvqln4dq-uc.a.run.app
```

### **📱 Telegram Bot:**
**Bot Name:** `@YourStudentVisaBot` *(Replace with actual bot username)*
**Direct Link:** `https://t.me/YourStudentVisaBot` *(Replace with actual bot username)*

### **🔧 Backend API:**
```
https://ai-chatbot-backend-irsvqln4dq-uc.a.run.app
```

## ✨ Key Features

### **🤖 AI-Powered Conversations**
- **Google Gemini 2.5 Flash** for intelligent responses
- **Student visa expertise** for USA, UK, Australia, South Korea
- **Context-aware conversations** with session memory
- **Multi-language support** (English + Nepali context)

### **📱 Multi-Platform Support**
- **Web Interface** - Responsive React frontend
- **Telegram Bot** - Native mobile experience
- **Unified Backend** - Same AI logic across platforms
- **Session Persistence** - Web (ephemeral), Telegram (permanent)

### **🎯 Lead Capture & Management**
- **Automatic contact detection** from conversations
- **Supabase database** integration
- **Email notifications** for new leads
- **Professional follow-up** system

### **🔒 Production Ready**
- **Rate limiting** (60/min, 1000/hour per IP)
- **Security headers** and CORS protection
- **Auto-deployment** via GitHub Actions
- **Health monitoring** and error handling

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │  Telegram Bot   │    │   FastAPI      │
│   (React/TS)    │◄──►│   Integration   │◄──►│   Backend      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Google Gemini  │    │   Supabase      │
                       │      AI API     │    │   Database      │
                       └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
AI_chatbot/
├── frontend/                 # React + TypeScript frontend
│   ├── src/
│   │   ├── components/      # ChatBox, ChatInput, ChatMessage
│   │   ├── lib/             # API client, utilities
│   │   └── pages/           # Main pages
│   ├── package.json
│   └── vite.config.ts
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── memory/          # Session management
│   │   ├── prompts/         # LLM prompt orchestration
│   │   ├── tools/           # Lead capture tools
│   │   └── utils/           # Utilities
│   ├── telegram_integration.py  # Telegram bot
│   ├── main.py              # Main API
│   └── requirements.txt
└── README.md                # This file
```

## 🚀 Quick Start

### **1. Clone & Setup**
```bash
git clone https://github.com/jb020725/AI_Chat.git
cd AI_Chat
```

### **2. Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### **3. Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

### **4. Environment Variables**
Create `.env` file in backend directory:
```env
# AI Configuration
GEMINI_API_KEY=your_gemini_api_key

# Database
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_key
SUPABASE_ANON_KEY=your_anon_key

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
ENABLE_TELEGRAM=true

# Email (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email
SMTP_PASSWORD=your_app_password
FROM_EMAIL=your_email
FROM_NAME=Student Visa Bot
```

## 🔧 Configuration

### **Supported Countries & Services**
- 🇺🇸 **USA** - F-1 Student Visa
- 🇬🇧 **UK** - Tier 4 Student Visa  
- 🇦🇺 **Australia** - Subclass 500 Student Visa
- 🇰🇷 **South Korea** - D-2/D-4 Student Visa

### **Target Audience**
- **Primary**: Nepali students from Nepal
- **Services**: Student visa applications only
- **Focus**: Legitimate consultancy guidance

### **System Limits**
- **Rate Limiting**: 60 requests/minute, 1000/hour per IP
- **Concurrency**: Max 20 concurrent LLM calls
- **Session Memory**: Web (temporary), Telegram (permanent)

## 📊 API Endpoints

### **Core Chat**
- `POST /api/chat` - Main chat endpoint
- `GET /healthz` - Health check

### **Lead Management**
- `GET /api/leads` - List captured leads
- `POST /api/leads` - Create new lead

### **Session Management**
- `GET /memory/sessions` - Active sessions
- `GET /memory/sessions/{id}` - Session details

### **Telegram Integration**
- `POST /telegram/webhook` - Telegram webhook
- `GET /telegram/set-webhook` - Configure webhook

## 🚀 Deployment

### **Google Cloud Run (Recommended)**
```bash
# Backend
gcloud run deploy ai-chatbot-backend --source backend --region us-central1

# Frontend  
gcloud run deploy ai-chatbot-frontend --source frontend --region us-central1
```

### **GitHub Actions Auto-Deploy**
- **Push to `main`** branch
- **Automatic deployment** to Cloud Run
- **Permanent URLs** that never change
- **Zero downtime** updates

## 📱 Mobile Experience

### **Web Interface**
- ✅ **Responsive design** for all screen sizes
- ✅ **Touch-optimized** with 48px minimum targets
- ✅ **Mobile keyboard** management (disappears after sending)
- ✅ **Dynamic viewport** height (`100dvh`)
- ✅ **Safe area** handling for notched devices

### **Telegram Bot**
- ✅ **Native mobile** experience
- ✅ **Session persistence** across app restarts
- ✅ **Typing indicators** and smooth interactions
- ✅ **Offline support** when needed

## 🎯 Use Cases

### **For Students**
- **Visa Requirements** - Documents, timelines, costs
- **Application Process** - Step-by-step guidance
- **IELTS Preparation** - Booking and tips
- **University Selection** - Country-specific advice

### **For Consultancy**
- **Lead Generation** - Automatic contact capture
- **24/7 Availability** - Instant responses
- **Consistent Quality** - AI-powered accuracy
- **Multi-Platform** - Web + Telegram reach

## 🔒 Security & Privacy

- **Rate limiting** prevents abuse
- **CORS protection** for web security
- **Input validation** and sanitization
- **Secure API keys** management
- **GDPR compliant** data handling

## 📈 Performance

- **Fast responses** with Gemini 2.5 Flash
- **Efficient memory** management
- **Background processing** for lead capture
- **Optimized database** queries
- **CDN-ready** static assets

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

## 📄 License

This project is proprietary software for AI Consultancy. All rights reserved.

## 📞 Support & Contact

- **AI Consultancy Team** - For business inquiries
- **GitHub Issues** - For technical support
- **Documentation** - This README + inline code comments

## 🎉 Project Status

- ✅ **Frontend**: Live and responsive
- ✅ **Backend**: Production-ready with all features
- ✅ **Telegram**: Integrated and functional
- ✅ **Database**: Supabase integration complete
- ✅ **Deployment**: Auto-deploy from GitHub
- ✅ **Mobile**: Optimized for all devices

---

**Last Updated:** 2025-08-29  
**Version:** 2.0.0  
**Status:** Production Ready 🚀

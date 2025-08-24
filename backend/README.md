# 🤖 AI Chatbot - Production Ready with Gemini 2.5 Flash

A clean, production-ready AI chatbot that integrates with your RAG system and Gemini AI, optimized for student visa consultation.

## 🚀 Quick Start

### Option 1: Windows Batch File
```bash
# Double-click or run:
start_simple_chatbot.bat
```

### Option 2: Manual Start
```bash
# Install dependencies
pip install -r requirements.txt

# Start chatbot
python main.py
```

## 📡 API Endpoints

- **`POST /api/chat`** - Main chat endpoint
- **`GET /health`** - System health check
- **`GET /api/conversations/{id}`** - Get chat history
- **`GET /`** - API information

## 🗄️ Features

- ✅ **RAG Integration** - Uses your existing RAG system
- ✅ **AI Responses** - Powered by Gemini 2.5 Flash
- ✅ **User Info Extraction** - Automatically captures leads
- ✅ **Database Storage** - SQLite for conversations and user data
- ✅ **Session Management** - Persistent chat sessions
- ✅ **CORS Enabled** - Ready for frontend integration
- ✅ **Rate Limiting** - 120/minute, 2000/hour (Gemini 2.5 Flash optimized)
- ✅ **Concurrency Control** - 20 concurrent LLM calls

## 🔧 Configuration

The chatbot reads from `test.env`:
- `GEMINI_API_KEY` - Your Gemini AI key
- `GEMINI_MODEL` - Set to `gemini-2.5-flash-001`
- Other settings are optional

## 📁 Structure

```
backend/
├── main.py                    # Main chatbot application
├── test.env                   # Environment configuration
├── requirements.txt            # All necessary dependencies
├── manage_logs.py             # Log management utility
├── LOGGING_README.md          # Logging documentation
├── sessions_table.sql         # Database schema (for reference)
├── app/
│   ├── rag/                   # Your RAG system
│   ├── data/                  # Knowledge base
│   ├── config.py              # Configuration
│   ├── tools/                 # Tool management
│   ├── memory/                # Session memory system
│   └── utils/                 # Utilities and logging
└── logs/                      # Application logs
```

## 💡 What It Does

1. **Receives** user messages via HTTP API
2. **Retrieves** relevant info from your RAG system
3. **Sends** to Gemini 2.5 Flash for intelligent responses
4. **Saves** user information to database
5. **Returns** responses to users
6. **Maintains** conversation history

## 🚀 Gemini 2.5 Flash Optimizations

- **Model**: `gemini-2.5-flash-001`
- **Rate Limits**: 120/minute, 2000/hour (doubled from 1.5)
- **Concurrency**: 20 concurrent LLM calls (doubled from 1.5)
- **Performance**: Enhanced throughput and response times

## 🧹 Clean Codebase

- **No test files** - All unnecessary test scripts removed
- **No debug files** - Clean production environment
- **Optimized logging** - Automatic rotation and cleanup
- **Streamlined functions** - Only essential functions retained

---

**Production Ready!** 🎉

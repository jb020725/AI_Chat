#!/usr/bin/env python3
"""
AI Chatbot Backend - Main Application
- Receives user messages
- Uses clean function calling for intelligent responses
- Manages session memory and lead capture
- Returns vetted, helpful responses
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import logging
import os
import sys
from datetime import datetime
import json
from pathlib import Path
from contextlib import asynccontextmanager
import re
import asyncio
from collections import defaultdict
import time
import platform

# Rate Limiting Imports
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Add current directory to path for imports
sys.path.append('.')

# Import centralized utilities
from app.utils.paths import CFG
from app.utils.logging_config import setup_clean_logging
from app.config import settings

# Import Telegram integration
try:
    from telegram_integration import telegram_router
    TELEGRAM_AVAILABLE = True
    print("✅ Telegram integration loaded successfully")
except ImportError as e:
    print(f"❌ Telegram integration not available: {e}")
    TELEGRAM_AVAILABLE = False

# RAG components have been completely removed
RAG_AVAILABLE = False
RAG_ENABLED = False

# Import Memory Management components
try:
    from app.memory import get_session_memory, get_smart_response
    from app.memory.api import router as memory_router
    MEMORY_AVAILABLE = True
except ImportError as e:
    print(f"Memory system not available: {e}")
    MEMORY_AVAILABLE = False

# Import Lead Capture Tool
try:
    from app.tools.lead_capture_tool import LeadCaptureTool
    LEAD_CAPTURE_AVAILABLE = True
except ImportError as e:
    print(f"Lead capture tool not available: {e}")
    LEAD_CAPTURE_AVAILABLE = False

# Import Gemini AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError as e:
    print(f"Gemini not available: {e}")
    GEMINI_AVAILABLE = False

# Configure clean logging with rotation
setup_clean_logging(
    log_level="INFO",
    max_size_mb=10,  # 10MB max file size
    backup_count=5    # Keep 5 backup files
)
logger = logging.getLogger(__name__)

# Initialize Rate Limiting
limiter = Limiter(key_func=get_remote_address)
logger.info("Rate limiting initialized")

# Environment variables are loaded from Cloud Run via app.config.settings

# Initialize Gemini
if GEMINI_AVAILABLE:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    logger.info("Gemini 2.5 Flash initialized for AI Consultancy chatbot")
else:
    model = None

# Initialize Lead Capture Tool
lead_capture_tool = None
if LEAD_CAPTURE_AVAILABLE:
    try:
        lead_capture_tool = LeadCaptureTool()
        logger.info("Lead Capture Tool initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Lead Capture Tool: {e}")
        LEAD_CAPTURE_AVAILABLE = False

# Concurrency Control - Updated for Gemini 2.5 Flash
llm_semaphore = asyncio.Semaphore(20)  # Max 20 concurrent LLM calls (doubled for 2.5)
logger.info("Concurrency control initialized - max 20 concurrent LLM calls (Gemini 2.5 Flash)")

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    user_info_extracted: Optional[Dict[str, str]] = None
    timestamp: str

def extract_user_info(message: str) -> Dict[str, str]:
    """Extract user information from message (legacy support)"""
    user_info = {}
    message_lower = message.lower()
    
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, message)
    if email_match:
        user_info['email'] = email_match.group()
    
    # Extract phone number
    phone_pattern = r'\b\d{10,15}\b'
    phone_match = re.search(phone_pattern, message)
    if phone_match:
        user_info['phone'] = phone_match.group()
    
    # Extract name (improved pattern)
    name_patterns = [
        r'\bmy name is\s+([A-Za-z\s]+?)(?:\s*[,.]|$)',
        r'\bi\'m\s+([A-Za-z\s]+?)(?:\s*[,.]|$)',
        r'\bi am\s+([A-Za-z\s]+?)(?:\s*[,.]|$)',
        r'\bname\s*:\s*([A-Za-z\s]+?)(?:\s*[,.]|$)',
        r'\bcall me\s+([A-Za-z\s]+?)(?:\s*[,.]|$)'
    ]
    
    for pattern in name_patterns:
        name_match = re.search(pattern, message_lower, re.IGNORECASE)
        if name_match:
            name = name_match.group(1).strip()
            if name and len(name) > 1 and name not in ['user', 'test', 'example', 'sample']:
                user_info['name'] = name.title()
                break
    
    # Extract target country with better detection
    country_patterns = {
        'usa': ['usa', 'united states', 'america', 'us', 'u.s.', 'u.s.a'],
        'uk': ['uk', 'united kingdom', 'britain', 'england', 'great britain'],
        'australia': ['australia', 'aussie'],
        'south_korea': ['south korea', 'korea', 'korean', 'seoul']
    }
    
    for country, patterns in country_patterns.items():
        for pattern in patterns:
            if pattern in message_lower:
                user_info['country'] = country
                logger.info(f"Extracted country '{country}' from message")
                break
        if 'country' in user_info:
            break
    
    # Extract intake period
    intake_keywords = ['fall', 'spring', 'summer', 'autumn', 'winter']
    for keyword in intake_keywords:
        if keyword in message_lower:
            user_info['intake'] = keyword.title()
            break
    
    return user_info

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup on startup/shutdown"""
    # Startup
    logger.info("AI Chatbot started with SIMPLE CHATBOT STRUCTURE! - FORCE DEPLOYMENT")
    logger.info(f"Application Directory: {CFG.APP_DIR}")
    logger.info(f"Data Directory: {CFG.DATA_DIR}")
    logger.info(f"Index Directory: {CFG.INDEX_DIR}")
    logger.info(f"Lead Capture: {'Available' if LEAD_CAPTURE_AVAILABLE else 'Not Available'}")
    logger.info(f"Memory System: {'Available' if MEMORY_AVAILABLE else 'Not Available'}")
    logger.info(f"RAG System: Completely removed from project")
    logger.info(f"Gemini AI: {'Available' if GEMINI_AVAILABLE else 'Not Available'}")
    logger.info(f"Simple Chatbot: Direct LLM responses with session memory")
    logger.info(f"Rate Limiting: 60/minute, 1000/hour per IP")
    logger.info(f"Concurrency Control: Max 20 concurrent LLM calls")
    yield
    # Shutdown (if needed)
    logger.info("AI Chatbot shutting down...")

# FastAPI app
app = FastAPI(title="AI Consultancy AI Assistant - Simple Chatbot", version="3.0.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting exception handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add memory router
if MEMORY_AVAILABLE:
    app.include_router(memory_router, prefix="/memory", tags=["memory"])

# Add Telegram router
if TELEGRAM_AVAILABLE:
    app.include_router(telegram_router)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "rag_available": False,
        "rag_status": "Completely Removed",
        "gemini_available": GEMINI_AVAILABLE,
        "memory_available": MEMORY_AVAILABLE,
        "lead_capture_available": LEAD_CAPTURE_AVAILABLE,
        "rate_limiting": "Active - 60/minute, 1000/hour per IP",
        "concurrency_control": "Active - Max 20 concurrent LLM calls",
        "simple_chatbot_enabled": True,
        "chatbot_type": "Direct LLM responses with session memory"
    }

@app.get("/healthz")
async def healthz():
    """Lightweight health check for Cloud Run"""
    return {"ready": True}, 200

@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("60/minute")  # 60 requests per minute per IP
@limiter.limit("1000/hour")  # 1000 requests per hour per IP
async def chat(request: Request, chat_request: ChatRequest):
    """Main chat endpoint using simple chatbot"""
    try:
        # Use provided session ID or generate new one
        session_id = chat_request.session_id or f"session_{datetime.now().timestamp()}"
        
        # Generate smart response using simple chatbot (this handles extraction)
        if MEMORY_AVAILABLE and GEMINI_AVAILABLE:
            try:
                # Set the LLM model in the smart response system
                get_smart_response().set_llm_model(model)
                logger.info("LLM model set in smart response system for simple chatbot")
                
                # Get conversation history
                memory = get_session_memory()
                conversation_context = memory.get_conversation_context(session_id)
                conversation_history = conversation_context.get("conversation_history", [])
                logger.info(f"Retrieved conversation history: {len(conversation_history)} exchanges")
                
                # Use concurrency control for LLM calls
                async with llm_semaphore:
                    logger.info(f"🔍 DEBUG: About to call get_smart_response().generate_smart_response")
                    logger.info(f"🔍 DEBUG: Message: '{chat_request.message[:100]}...'")
                    logger.info(f"🔍 DEBUG: Session ID: {session_id}")
                    logger.info(f"🔍 DEBUG: Conversation history length: {len(conversation_history)}")
                    
                    smart_response_instance = get_smart_response()
                    smart_response_instance.set_llm_model(model)
                    result = smart_response_instance.generate_smart_response(
                        chat_request.message, session_id, conversation_history
                    )
                    
                    logger.info(f"🔍 DEBUG: smart_response result: {result}")
                
                # Extract response from result
                if result.get('success'):
                    ai_response = result.get('response', '')
                    logger.info("Simple chatbot response generated successfully")
                    
                    # Update session memory with extracted info from smart_response
                    if result.get('user_info_extracted'):
                        memory.update_session(session_id, result.get('user_info_extracted'))
                        logger.info(f"Session updated with enhanced extraction: {result.get('user_info_extracted')}")
                    
                else:
                    # Fallback response if chatbot fails
                    ai_response = "I'm experiencing technical difficulties. Please try again or ask a different question."
                    logger.warning(f"Simple chatbot failed: {result.get('error')}")
                
                # Track the conversation exchange in session memory
                try:
                    memory.add_conversation_exchange(session_id, chat_request.message, ai_response)
                    logger.info(f"Conversation exchange tracked for session {session_id}")
                except Exception as e:
                    logger.warning(f"Failed to track conversation exchange: {e}")
                    
            except Exception as e:
                logger.error(f"🔍 DEBUG: Error in smart response generation: {e}")
                import traceback
                logger.error(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
                ai_response = "I'm having technical difficulties. Please try again."
                
        else:
            # Fallback to basic response
            ai_response = "I can help you with student visa information for USA, UK, Australia, and South Korea. Please share your contact details and preferred country for personalized guidance."
        
        return ChatResponse(
            response=ai_response,
            session_id=session_id,
            user_info_extracted={},  # Will be populated by smart_response
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/leads")
async def create_lead(lead_data: Dict[str, Any]):
    """Create a new lead manually (for testing)"""
    if not LEAD_CAPTURE_AVAILABLE or not lead_capture_tool:
        raise HTTPException(status_code=503, detail="Lead capture system not available")
    
    try:
        logger.info(f"Manual lead creation attempt: {lead_data}")
        
        # Create the lead
        result = lead_capture_tool.create_lead(lead_data)
        
        if result.get('success'):
            logger.info(f"Lead created successfully: {result}")
            return {
                "success": True,
                "message": "Lead created successfully",
                "lead_id": result.get('data', {}).get('id'),
                "data": result.get('data')
            }
        else:
            logger.error(f"Failed to create lead: {result}")
            raise HTTPException(status_code=400, detail=f"Failed to create lead: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error creating lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leads")
async def get_leads():
    """Get leads from Supabase (for monitoring)"""
    if not LEAD_CAPTURE_AVAILABLE or not lead_capture_tool:
        raise HTTPException(status_code=503, detail="Lead capture system not available")
    
    try:
        # Get all leads (you can add filters later)
        result = lead_capture_tool.search_leads({}, limit=50)
        return result
    except Exception as e:
        logger.error(f"Error getting leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leads/{lead_id}")
async def get_lead(lead_id: str):
    """Get specific lead by ID"""
    if not LEAD_CAPTURE_AVAILABLE or not lead_capture_tool:
        raise HTTPException(status_code=503, detail="Lead capture system not available")
    
    try:
        result = lead_capture_tool.get_lead(lead_id=lead_id)
        if result.get('success'):
            return result
        else:
            raise HTTPException(status_code=404, detail="Lead not found")
    except Exception as e:
        logger.error(f"Error getting lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/info")
async def get_system_info():
    """Get system information and paths"""
    return {
        "application_info": {
            "name": "AI Chatbot - AI Consultancy Lead Capture",
            "version": "3.0.0",
            "environment": "production",
            "security_features": {
                "rate_limiting": "Active",
                "concurrency_control": "Active",
                "user_isolation": "Active"
            }
        },
        "paths": {
            "backend_root": str(CFG.BACKEND_ROOT),
            "app_directory": str(CFG.APP_DIR),
            "data_directory": str(CFG.DATA_DIR),
            "index_directory": str(CFG.INDEX_DIR),
            "logs_directory": str(CFG.LOGS_DIR),
            "config_directory": str(CFG.CONFIG_DIR)
        },
        "data_structure": {
            "available_countries": ["USA", "UK", "Australia", "South Korea"],
            "rag_files": "Completely removed",
            "data_files": list(CFG.DATA_DIR.glob("**/*.jsonl")) if CFG.DATA_DIR.exists() else []
        },
        "chatbot_features": {
            "type": "AI Consultancy Lead Capture",
            "session_memory": "Active for conversation flow",
            "lead_detection": "Automatic contact info extraction",
            "database_saving": "Supabase integration active",
            "email_notifications": "Advisor alerts enabled",
            "visa_knowledge": "Built into prompt"
        },
        "rate_limiting": {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "concurrent_llm_calls": 20
        }
    }

@app.get("/api/countries")
async def get_countries():
    """Get supported countries"""
    return {
        "countries": ["USA", "UK", "Australia", "South Korea"],
        "count": 4
    }

@app.get("/api/version")
async def get_version():
    """Get current version and deployment info"""
    return {
        "version": "ENHANCED EXTRACTION VERSION 2.1 - FORCE RESTART",
        "deployment_time": datetime.now().isoformat(),
        "force_restart": True,
        "features": {
            "enhanced_extraction": "ENABLED",
            "debug_logging": "ENABLED",
            "study_level_detection": "FIXED",
            "program_detection": "FIXED",
            "email_debugging": "ENABLED"
        }
    }

@app.get("/api/status")
async def get_status():
    """Get system status and configuration"""
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "features": {
            "chat": "Active",
            "lead_capture": "Active",
            "session_memory": "Active for conversation flow",
            "email_notifications": "Smart lead-based (sent when leads are complete)",
            "database": "Supabase integration active",
            "llm": "Gemini AI integration active"
        },
        "system_info": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "uptime": "Active"
        }
    }

# ⚠️ DEPRECATED: Session close endpoints removed - emails now sent automatically when leads complete
# The new smart email system triggers emails based on lead completeness, not session closure

@app.post("/api/test-lead-creation")
async def test_lead_creation(test_data: dict):
    """
    Test endpoint to manually create a lead for debugging
    """
    try:
        session_id = test_data.get("session_id", "test_session_123")
        lead_data = test_data.get("lead_data", {})
        
        logger.info(f"🧪 TEST LEAD CREATION: Session {session_id}, Data: {lead_data}")
        
        # Get the lead capture tool
        from app.tools.lead_capture_tool import LeadCaptureTool
        from app.config import settings
        
        config = {
            "supabase_url": settings.SUPABASE_URL,
            "supabase_service_role_key": settings.SUPABASE_SERVICE_ROLE_KEY,
            "smtp_server": settings.SMTP_SERVER,
            "smtp_port": settings.SMTP_PORT,
            "smtp_username": settings.SMTP_USERNAME,
            "smtp_password": settings.SMTP_PASSWORD,
            "from_email": settings.FROM_EMAIL,
            "from_name": settings.FROM_NAME,
            "lead_notification_email": settings.LEAD_NOTIFICATION_EMAIL,
            "enable_email_notifications": settings.ENABLE_EMAIL_NOTIFICATIONS
        }
        
        lead_tool = LeadCaptureTool(config)
        
        # Create test lead
        result = lead_tool.create_lead(lead_data)
        
        logger.info(f"🧪 TEST LEAD CREATION RESULT: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"🧪 TEST LEAD CREATION ERROR: {str(e)}")
        import traceback
        logger.error(f"🧪 TEST LEAD CREATION TRACEBACK: {traceback.format_exc()}")
        return {
            "success": False,
            "error": f"Test lead creation failed: {str(e)}"
        }

# Initialize Memory System with LLM model (Clean Function Calling)
if MEMORY_AVAILABLE and GEMINI_AVAILABLE:
    try:
        # Initialize the smart response system for simple chatbot
        logger.info("About to set LLM model in smart response system...")
        get_smart_response().set_llm_model(model)
        logger.info("Memory system initialized with LLM model for simple chatbot")
        
        # Verify the integration
        smart_response_instance = get_smart_response()
        if smart_response_instance.llm_model:
            logger.info("Simple chatbot successfully connected to smart response system")
        else:
            logger.error("Simple chatbot failed to connect to smart response system")
            logger.error(f"LLM model status: {smart_response_instance.llm_model}")
            
    except Exception as e:
        logger.error(f"Failed to initialize memory system with LLM: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
else:
    logger.warning("Memory system or LLM not available for clean function calling integration")

if __name__ == "__main__":
    # Run the FastAPI app
    logger.info("AI Chatbot started with ENHANCED EXTRACTION VERSION 2.0! - FORCE DEPLOYMENT")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=False,  # Disable reload to stop file watching spam
        log_level="info"
    )



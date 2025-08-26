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

# RAG components are kept in folder but not imported or used
RAG_AVAILABLE = False
RAG_ENABLED = False

# Import Memory Management components
try:
    from app.memory import get_session_memory, smart_response
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
    logger.info("Gemini 2.5 Flash initialized for clean function calling")
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
    logger.info("AI Chatbot started with CLEAN FUNCTION CALLING STRUCTURE!")
    logger.info(f"Application Directory: {CFG.APP_DIR}")
    logger.info(f"Data Directory: {CFG.DATA_DIR}")
    logger.info(f"Index Directory: {CFG.INDEX_DIR}")
    logger.info(f"Lead Capture: {'Available' if LEAD_CAPTURE_AVAILABLE else 'Not Available'}")
    logger.info(f"Memory System: {'Available' if MEMORY_AVAILABLE else 'Not Available'}")
    logger.info(f"RAG System: Not Used (files kept but not imported)")
    logger.info(f"Gemini AI: {'Available' if GEMINI_AVAILABLE else 'Not Available'}")
    logger.info(f"Clean Functions: get_answer, qualify_interest, request_consent, save_lead, notify_human")
    logger.info(f"Rate Limiting: 60/minute, 1000/hour per IP")
    logger.info(f"Concurrency Control: Max 20 concurrent LLM calls")
    yield
    # Shutdown (if needed)
    logger.info("AI Chatbot shutting down...")

# FastAPI app
app = FastAPI(title="AI Consultancy AI Assistant - Clean Function Calling", version="3.0.0", lifespan=lifespan)

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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "rag_available": RAG_AVAILABLE,
        "rag_status": "Not Used",
        "gemini_available": GEMINI_AVAILABLE,
        "memory_available": MEMORY_AVAILABLE,
        "lead_capture_available": LEAD_CAPTURE_AVAILABLE,
        "rate_limiting": "Active - 60/minute, 1000/hour per IP",
        "concurrency_control": "Active - Max 20 concurrent LLM calls",
        "function_calling_enabled": True,
        "clean_functions": ["get_answer", "qualify_interest", "request_consent", "save_lead", "notify_human"]
    }

@app.get("/healthz")
async def healthz():
    """Lightweight health check for Cloud Run"""
    return {"ready": True}, 200

@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("60/minute")  # 60 requests per minute per IP
@limiter.limit("1000/hour")  # 1000 requests per hour per IP
async def chat(request: Request, chat_request: ChatRequest):
    """Main chat endpoint using clean function calling"""
    try:
        # Use provided session ID or generate new one
        session_id = chat_request.session_id or f"session_{datetime.now().timestamp()}"
        
        # Extract user information for THIS TURN (legacy support)
        turn_info = extract_user_info(chat_request.message)
        
        # Update session memory with extracted info
        if MEMORY_AVAILABLE and turn_info:
            memory = get_session_memory()
            if turn_info:
                memory.update_session(session_id, turn_info)
                logger.info(f"Session updated with turn info: {turn_info}")
        
        # Generate smart response using clean function calling
        if MEMORY_AVAILABLE and GEMINI_AVAILABLE:
            try:
                # Set the LLM model in the smart response system
                smart_response.set_llm_model(model)
                logger.info("LLM model set in smart response system for clean function calling")
                
                # Get conversation history
                memory = get_session_memory()
                conversation_context = memory.get_conversation_context(session_id)
                conversation_history = conversation_context.get("conversation_history", [])
                logger.info(f"Retrieved conversation history: {len(conversation_history)} exchanges")
                
                # Use concurrency control for LLM calls
                async with llm_semaphore:
                    result = smart_response.generate_smart_response(
                        chat_request.message, session_id, conversation_history
                    )
                
                # Extract response from result
                if result.get('success'):
                    ai_response = result.get('response', '')
                    function_calls = result.get('function_calls', [])
                    
                    # Log function calls for debugging
                    if function_calls:
                        logger.info(f"Function calls executed: {[fc.get('function_name') for fc in function_calls]}")
                    
                else:
                    # Fallback response if function calling fails
                    ai_response = "I'm experiencing technical difficulties. Please try again or ask a different question."
                    logger.warning(f"Function calling failed: {result.get('error')}")
                
                # Track the conversation exchange in session memory
                try:
                    memory.add_conversation_exchange(session_id, chat_request.message, ai_response)
                    logger.info(f"Conversation exchange tracked for session {session_id}")
                except Exception as e:
                    logger.warning(f"Failed to track conversation exchange: {e}")
                    
            except Exception as e:
                logger.error(f"Error in smart response generation: {e}")
                ai_response = "I'm having technical difficulties. Please try again."
                
        else:
            # Fallback to basic response
            ai_response = "I can help you with student visa information for USA, UK, Australia, and South Korea. Please share your contact details and preferred country for personalized guidance."
        
        return ChatResponse(
            response=ai_response,
            session_id=session_id,
            user_info_extracted=turn_info,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
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
            "name": "AI Chatbot - Clean Function Calling",
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
            "rag_files": "Kept in folder but not used",
            "data_files": list(CFG.DATA_DIR.glob("**/*.jsonl")) if CFG.DATA_DIR.exists() else []
        },
        "clean_functions": {
            "get_answer": "Vetted content lookup",
            "qualify_interest": "Interest capture without PII",
            "request_consent": "Explicit consent management",
            "save_lead": "Contact storage after consent",
    
            "notify_human": "CRM handoff"
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

@app.get("/api/status")
async def get_status():
    """Get system status"""
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0",
        "components": {
            "rag_system": "not_used",
            "memory_system": "operational" if MEMORY_AVAILABLE else "unavailable",
            "lead_capture": "operational" if LEAD_CAPTURE_AVAILABLE else "unavailable",
            "gemini_ai": "operational" if GEMINI_AVAILABLE else "unavailable",
            "rate_limiting": "operational",
            "concurrency_control": "operational",
            "clean_function_calling": "operational" if MEMORY_AVAILABLE and GEMINI_AVAILABLE else "unavailable"
        },
        "uptime": 0  # You can add actual uptime calculation if needed
    }

# Initialize Memory System with LLM model (Clean Function Calling)
if MEMORY_AVAILABLE and GEMINI_AVAILABLE:
    try:
        # Initialize the smart response system with clean function calling
        smart_response.set_llm_model(model)
        logger.info("Memory system initialized with LLM model for clean function calling")
        
        # Verify the integration
        if smart_response.function_integrator:
            logger.info("Clean function calling successfully connected to smart response system")
        else:
            logger.error("Clean function calling failed to connect to smart response system")
            
    except Exception as e:
        logger.error(f"Failed to initialize memory system with LLM: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
else:
    logger.warning("Memory system or LLM not available for clean function calling integration")

if __name__ == "__main__":
    # Run the FastAPI app
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=False,  # Disable reload to stop file watching spam
        log_level="info"
    )



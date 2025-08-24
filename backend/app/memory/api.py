#!/usr/bin/env python3
"""
Memory Management API Endpoints
Provides endpoints for monitoring and managing session memory
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from .session_memory import get_session_memory
from .smart_response import get_smart_response_generator

router = APIRouter(prefix="/memory", tags=["memory"])

@router.get("/sessions")
async def get_all_sessions():
    """Get summary of all active sessions"""
    try:
        memory = get_session_memory()
        return {
            "status": "success",
            "total_sessions": len(memory.sessions),
            "sessions": memory.get_all_sessions()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get detailed information about a specific session"""
    try:
        memory = get_session_memory()
        session_info = memory.get_session_summary(session_id)
        return {
            "status": "success",
            "session": session_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear a specific session (useful for testing)"""
    try:
        memory = get_session_memory()
        memory.clear_session(session_id)
        return {
            "status": "success",
            "message": f"Session {session_id} cleared"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/response-metadata")
async def get_response_metadata(session_id: str):
    """Get metadata about response generation for a session"""
    try:
        generator = get_smart_response_generator()
        metadata = generator.get_response_metadata(session_id)
        return {
            "status": "success",
            "metadata": metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

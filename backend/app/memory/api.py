#!/usr/bin/env python3
"""
Memory Management API Endpoints
Provides endpoints for monitoring and managing session memory
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from .session_memory import get_session_memory
from .smart_response import smart_response

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
        session_info = smart_response.get_session_info(session_id)
        return {
            "status": "success",
            "metadata": {
                "session_id": session_id,
                "has_contact_info": bool(session_info.email or session_info.phone) if session_info else False,
                "has_consent": getattr(session_info, 'consent_given', False) if session_info else False,
                "study_country": getattr(session_info, 'study_country', None) if session_info else None,
                "study_level": getattr(session_info, 'study_level', None) if session_info else None,
                "target_intake": getattr(session_info, 'target_intake', None) if session_info else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

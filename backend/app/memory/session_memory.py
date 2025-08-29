#!/usr/bin/env python3
"""
Session Memory Manager
Tracks user information and manages smart question flow
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import os

# Try to import Supabase for persistence
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

logger = logging.getLogger(__name__)

@dataclass
class UserInfo:
    """User information structure with enhanced conversation tracking"""
    email: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    country: Optional[str] = None
    intake: Optional[str] = None
    program_level: Optional[str] = None
    field_of_study: Optional[str] = None
    
    # Conversation tracking
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    conversation_summary: str = ""
    progress_state: str = "greeting"
    exchange_count: int = 0
    
    # Progress tracking
    completed_steps: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    def add_conversation_exchange(self, user_input: str, bot_response: str) -> None:
        """Add a new conversation exchange"""
        exchange = {
            "user_input": user_input,
            "bot_response": bot_response,
            "timestamp": datetime.now().isoformat(),
            "exchange_number": self.exchange_count + 1
        }
        self.conversation_history.append(exchange)
        self.exchange_count += 1
        self.last_updated = datetime.now()
        self._update_conversation_summary()
        self._update_progress_state()
        self._update_next_actions()
    
    def _update_conversation_summary(self) -> None:
        """Build a smart summary of the conversation"""
        if not self.conversation_history:
            self.conversation_summary = "New conversation started"
            return
        
        summary_parts = []
        
        # Add collected information
        if self.country:
            summary_parts.append(f"Target country: {self.country}")
        if self.program_level:
            summary_parts.append(f"Program level: {self.program_level}")
        if self.intake:
            summary_parts.append(f"Intake period: {self.intake}")
        if self.field_of_study:
            summary_parts.append(f"Field of study: {self.field_of_study}")
        if self.email:
            summary_parts.append(f"Contact info provided: {self.email}")
        
        # Add current state
        summary_parts.append(f"Current stage: {self.progress_state}")
        
        self.conversation_summary = ". ".join(summary_parts)
    
    def _update_progress_state(self) -> None:
        """Update the progress state based on collected information"""
        # Let the LLM decide naturally - don't force specific progress states
        self.progress_state = "conversation_active"
        
        # Don't track completed steps - let LLM decide naturally
        self.completed_steps = []
    
    def _update_next_actions(self) -> None:
        """Determine what actions should happen next"""
        # Let the LLM decide naturally - don't force specific actions
        self.next_actions = []
    
    def get_conversation_context(self) -> Dict[str, Any]:
        """Get comprehensive conversation context for LLM"""
        return {
            "session_info": {
                "country": self.country,
                "program_level": self.program_level,
                "intake": self.intake,
                "field_of_study": self.field_of_study,
                "email": self.email
            },
            "conversation_summary": self.conversation_summary,
            "conversation_history": self.conversation_history[-5:] if self.conversation_history else []  # Last 5 exchanges
        }
    
    def _get_conversation_flow(self) -> str:
        """Get the current conversation flow status"""
        # Let the LLM decide naturally - don't force specific flow steps
        return "Conversation in progress - LLM guided naturally"
    
    def get_missing_fields(self) -> List[str]:
        """Get list of missing information fields"""
        # Let the LLM decide naturally - don't force specific missing field questions
        return []
    
    def is_complete(self) -> bool:
        """Check if all required user info is collected"""
        return all([
            self.country,
            self.program_level,
            self.intake,
            self.field_of_study,
            self.email
        ])
    
    def update_info(self, new_info: Dict[str, str]) -> None:
        """Update user information"""
        for key, value in new_info.items():
            if hasattr(self, key) and value:
                setattr(self, key, value)
                self.last_updated = datetime.now()
                logger.info(f"Updated {key}: {value}")
        
        # Update progress and actions after info change
        self._update_progress_state()
        self._update_next_actions()
        self._update_conversation_summary()

class SessionMemory:
    """Manages session-based user memory with Supabase persistence"""
    
    def __init__(self):
        self.sessions: Dict[str, UserInfo] = {}
        self.supabase: Optional[Client] = None
        self._initialize_supabase()
        logger.info("Session Memory Manager initialized")
    
    def _initialize_supabase(self):
        """Initialize Supabase client for session persistence"""
        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase not available - sessions will only be stored in memory")
            return
            
        try:
            # Get Supabase credentials from environment
            from app.config import settings
            url = settings.SUPABASE_URL
            key = settings.SUPABASE_SERVICE_ROLE_KEY
            
            logger.info(f"🔍 Debug: Supabase URL = '{url}'")
            logger.info(f"🔍 Debug: Supabase Key length = {len(key) if key else 0}")
            
            if not url or not key:
                logger.warning("Supabase credentials not found - sessions will only be stored in memory")
                return
            
            self.supabase = create_client(url, key)
            logger.info("Supabase client initialized for session persistence")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.supabase = None
    
    def _save_session_to_supabase(self, session_id: str, session_data: UserInfo) -> bool:
        """Save session data to Supabase for persistence - ONLY for Telegram sessions"""
        # Check if this is a Telegram session (permanent) or website session (temporary)
        if not self._is_telegram_session(session_id):
            logger.info(f"Session {session_id} is website session - not saving to database (temporary)")
            return True  # Return success for temporary sessions
            
        if not self.supabase:
            logger.warning(f"Cannot save Telegram session {session_id} - Supabase not available")
            return False
            
        try:
            # Convert session data to JSON-serializable format
            session_record = {
                "session_id": session_id,
                "email": session_data.email,
                "phone": session_data.phone,
                "name": session_data.name,
                "country": session_data.country,
                "intake": session_data.intake,
                "program_level": session_data.program_level,
                "field_of_study": session_data.field_of_study,
                "conversation_summary": session_data.conversation_summary,
                "progress_state": session_data.progress_state,
                "exchange_count": session_data.exchange_count,
                "completed_steps": json.dumps(session_data.completed_steps),
                "next_actions": json.dumps(session_data.next_actions),
                "created_at": session_data.created_at.isoformat() if session_data.created_at else None,
                "last_updated": session_data.last_updated.isoformat() if session_data.last_updated else None,
                "platform": "telegram"  # Mark as Telegram session
            }
            
            # Upsert session data (create or update)
            result = self.supabase.table("sessions").upsert(session_record, on_conflict="session_id").execute()
            
            if result.data:
                logger.info(f"Telegram session {session_id} saved to Supabase successfully")
                return True
            else:
                logger.error(f"Failed to save Telegram session {session_id} to Supabase")
                return False
                
        except Exception as e:
            logger.error(f"Error saving Telegram session {session_id} to Supabase: {str(e)}")
            return False
    
    def _is_telegram_session(self, session_id: str) -> bool:
        """Check if session is from Telegram (should be permanent)"""
        # Telegram sessions typically have specific patterns
        telegram_patterns = [
            "telegram_",           # telegram_123456789
            "tg_",                 # tg_123456789
            "bot_",                # bot_123456789
            "chat_",               # chat_123456789
            "user_"                # user_123456789
        ]
        
        session_lower = session_id.lower()
        return any(pattern in session_lower for pattern in telegram_patterns)
    
    def _is_website_session(self, session_id: str) -> bool:
        """Check if session is from website (should be temporary)"""
        # Website sessions typically have these patterns
        website_patterns = [
            "session_",            # session_1234567890
            "web_",                # web_123456789
            "widget_",             # widget_123456789
            "browser_",            # browser_123456789
            "temp_"                # temp_123456789
        ]
        
        session_lower = session_id.lower()
        return any(pattern in session_lower for pattern in website_patterns)
    
    def _load_session_from_supabase(self, session_id: str) -> Optional[UserInfo]:
        """Load session data from Supabase for persistence - ONLY for Telegram sessions"""
        # Only load Telegram sessions from database
        if not self._is_telegram_session(session_id):
            logger.info(f"Session {session_id} is website session - not loading from database (temporary)")
            return None
            
        if not self.supabase:
            logger.warning(f"Cannot load Telegram session {session_id} - Supabase not available")
            return None
            
        try:
            # Query Supabase for Telegram session data
            result = self.supabase.table("sessions").select("*").eq("session_id", session_id).eq("platform", "telegram").execute()
            
            if result.data and len(result.data) > 0:
                session_data = result.data[0]
                
                # Create UserInfo object from Supabase data
                user_info = UserInfo(
                    email=session_data.get("email"),
                    phone=session_data.get("phone"),
                    name=session_data.get("name"),
                    country=session_data.get("country"),
                    intake=session_data.get("intake"),
                    program_level=session_data.get("program_level"),
                    field_of_study=session_data.get("field_of_study"),
                    conversation_summary=session_data.get("conversation_summary", ""),
                    progress_state=session_data.get("progress_state", "conversation_active"),
                    exchange_count=session_data.get("exchange_count", 0),
                    completed_steps=json.loads(session_data.get("completed_steps", "[]")),
                    next_actions=json.loads(session_data.get("next_actions", "[]"))
                )
                
                # Set timestamps if available
                if session_data.get("created_at"):
                    user_info.created_at = datetime.fromisoformat(session_data["created_at"])
                if session_data.get("last_updated"):
                    user_info.last_updated = datetime.fromisoformat(session_data["last_updated"])
                
                logger.info(f"Telegram session {session_id} loaded from Supabase successfully")
                return user_info
            else:
                logger.info(f"No Telegram session data found in Supabase for {session_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading Telegram session {session_id} from Supabase: {str(e)}")
            return None
    
    def _delete_session_from_supabase(self, session_id: str) -> bool:
        """Delete session data from Supabase - DISABLED for now"""
        # DISABLED: Don't delete from Supabase - sessions are in-memory only
        logger.info(f"Session {session_id} NOT deleted from Supabase (persistence disabled)")
        return True
    
    def get_session(self, session_id: str) -> UserInfo:
        """Get or create session for user - handles both temporary and permanent sessions"""
        if session_id not in self.sessions:
            # For Telegram sessions: try to load from Supabase first
            if self._is_telegram_session(session_id):
                loaded_session = self._load_session_from_supabase(session_id)
                if loaded_session:
                    self.sessions[session_id] = loaded_session
                    logger.info(f"Loaded existing Telegram session from Supabase: {session_id}")
                else:
                    self.sessions[session_id] = UserInfo()
                    logger.info(f"Created new Telegram session: {session_id}")
            else:
                # For website sessions: always create new (temporary)
                self.sessions[session_id] = UserInfo()
                logger.info(f"Created new website session (temporary): {session_id}")
        return self.sessions[session_id]
    
    def update_session(self, session_id: str, new_info: Dict[str, str]) -> None:
        """Update session with new user information"""
        session = self.get_session(session_id)
        session.update_info(new_info)
        
        # Save to Supabase
        self._save_session_to_supabase(session_id, session)
        
        logger.info(f"Updated session {session_id} with new info (persisted)")
    
    def get_user_info(self, session_id: str) -> UserInfo:
        """Get current user information for session"""
        return self.get_session(session_id)
    
    def should_ask_question(self, session_id: str) -> bool:
        """DEPRECATED: This method is no longer used - LLM handles everything"""
        # This method is deprecated - LLM now decides when to ask questions based on context
        return False
    
    def get_conversation_context(self, session_id: str) -> str:
        """Get conversation context for AI response"""
        session = self.get_session(session_id)
        
        if session.is_complete():
            return f"User Profile Complete: {session.name} ({session.email}) interested in {session.country} visa for {session.intake} intake."
        else:
            missing = session.get_missing_fields()
            return f"User Profile Incomplete: Missing {', '.join(missing)}. Current info: {session.country or 'Unknown'} country."
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of session for debugging/monitoring"""
        session = self.get_session(session_id)
        return {
            "session_id": session_id,
            "is_complete": session.is_complete(),
            "missing_fields": session.get_missing_fields(),
            "user_info": {
                "email": session.email,
                "phone": session.phone,
                "name": session.name,
                "country": session.country,
                "intake": session.intake
            },
            "last_updated": session.last_updated.isoformat() if session.last_updated else None
        }
    
    def clear_session(self, session_id: str) -> None:
        """Clear session data (useful for testing)"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            
        # Also delete from Supabase
        self._delete_session_from_supabase(session_id)
        
        logger.info(f"Cleared session: {session_id}")
    
    def clear_session_data(self, session_id: str) -> None:
        """Force clear session data and refresh from database (for Telegram memory sync)"""
        # Remove from memory
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"🗑️ Session {session_id} removed from memory")
        
        # Force delete from Supabase database
        if self.supabase and self._is_telegram_session(session_id):
            try:
                # Delete from sessions table
                result = self.supabase.table("sessions").delete().eq("session_id", session_id).execute()
                logger.info(f"🗑️ Session {session_id} deleted from Supabase database")
                
                # Also delete from leads table if exists
                try:
                    lead_result = self.supabase.table("leads").delete().eq("session_id", session_id).execute()
                    logger.info(f"🗑️ Lead data for session {session_id} deleted from Supabase")
                except Exception as e:
                    logger.warning(f"⚠️ Could not delete lead data: {e}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to delete session {session_id} from Supabase: {e}")
        else:
            logger.info(f"ℹ️ Session {session_id} is not a Telegram session or Supabase not available")
        
        logger.info(f"✅ Session {session_id} completely cleared and synced with database")
    
    def force_refresh_telegram_session(self, session_id: str) -> None:
        """Force refresh Telegram session from database (for memory sync issues)"""
        if not self._is_telegram_session(session_id):
            logger.info(f"Session {session_id} is not a Telegram session - no refresh needed")
            return
            
        if not self.supabase:
            logger.warning(f"Cannot refresh session {session_id} - Supabase not available")
            return
            
        try:
            # Remove from memory to force fresh load
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"🔄 Session {session_id} removed from memory for refresh")
            
            # Force load from database
            result = self.supabase.table("sessions").select("*").eq("session_id", session_id).execute()
            
            if result.data and len(result.data) > 0:
                session_data = result.data[0]
                # Create new UserInfo from database
                user_info = UserInfo(
                    email=session_data.get('email'),
                    phone=session_data.get('phone'),
                    name=session_data.get('name'),
                    country=session_data.get('country'),
                    intake=session_data.get('intake'),
                    program_level=session_data.get('program_level'),
                    field_of_study=session_data.get('field_of_study'),
                    conversation_summary=session_data.get('conversation_summary', ''),
                    progress_state=session_data.get('progress_state', 'conversation_active'),
                    exchange_count=session_data.get('exchange_count', 0)
                )
                
                # Set timestamps
                if session_data.get('created_at'):
                    user_info.created_at = datetime.fromisoformat(session_data['created_at'])
                if session_data.get('last_updated'):
                    user_info.last_updated = datetime.fromisoformat(session_data['last_updated'])
                
                # Store in memory
                self.sessions[session_id] = user_info
                logger.info(f"✅ Session {session_id} refreshed from database successfully")
            else:
                logger.info(f"ℹ️ Session {session_id} not found in database - will be created fresh")
                
        except Exception as e:
            logger.error(f"❌ Failed to refresh session {session_id} from database: {e}")
            # Create fresh session on error
            self.sessions[session_id] = UserInfo()
            logger.info(f"🆕 Created fresh session {session_id} due to refresh error")
    
    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all active sessions"""
        return {
            session_id: self.get_session_summary(session_id)
            for session_id in self.sessions
        }

    def add_conversation_exchange(self, session_id: str, user_input: str, bot_response: str) -> None:
        """Add a conversation exchange to the session"""
        session = self.get_session(session_id)
        session.add_conversation_exchange(user_input, bot_response)
        
        # Save to Supabase
        self._save_session_to_supabase(session_id, session)
        
        logger.info(f"Added conversation exchange to session {session_id} (persisted)")
    
    def get_conversation_context(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive conversation context for LLM"""
        session = self.get_session(session_id)
        return session.get_conversation_context()
    
    def get_conversation_summary(self, session_id: str) -> str:
        """Get conversation summary for LLM context"""
        session = self.get_session(session_id)
        return session.conversation_summary
    
    def get_progress_state(self, session_id: str) -> str:
        """Get current progress state"""
        session = self.get_session(session_id)
        return session.progress_state
    
    def get_next_actions(self, session_id: str) -> List[str]:
        """Get next actions needed"""
        session = self.get_session(session_id)
        return session.next_actions
    
    def get_missing_information(self, session_id: str) -> List[str]:
        """Get missing information fields"""
        session = self.get_session(session_id)
        return session.get_missing_fields()
    
    def get_conversation_flow(self, session_id: str) -> str:
        """Get conversation flow status"""
        session = self.get_session(session_id)
        return session._get_conversation_flow()
    
    def get_session_metadata(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session metadata for debugging and monitoring"""
        session = self.get_session(session_id)
        return {
            "session_id": session_id,
            "is_complete": session.is_complete(),
            "conversation_summary": session.conversation_summary,
            "exchange_count": session.exchange_count,
            "user_info": {
                "country": session.country,
                "program_level": session.program_level,
                "intake": session.intake,
                "field_of_study": session.field_of_study,
                "email": session.email
            },
            "timestamps": {
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "last_updated": session.last_updated.isoformat() if session.last_updated else None
            }
        }

# Global session memory instance
_session_memory = SessionMemory()

def get_session_memory() -> SessionMemory:
    """Get global session memory instance"""
    return _session_memory

"""
Telegram User Manager
Manages permanent storage of Telegram user details and provides enhanced context to LLM
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass
from app.tools.lead_capture_tool import LeadCaptureTool
from app.config import settings

logger = logging.getLogger(__name__)

@dataclass
class TelegramUser:
    """Telegram user data structure"""
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    is_bot: bool = False
    last_activity: Optional[datetime] = None
    total_messages: int = 0
    session_id: Optional[str] = None
    lead_id: Optional[str] = None
    preferences: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class TelegramUserManager:
    """Manages Telegram users with permanent storage and enhanced context"""
    
    def __init__(self):
        self.lead_capture_tool = LeadCaptureTool()
        self.table_name = "telegram_users"
        
    def create_or_update_user(self, telegram_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update Telegram user record"""
        try:
            # Extract user data from Telegram update
            user_data = telegram_data.get('from', {})
            telegram_id = user_data.get('id')
            
            if not telegram_id:
                return {"success": False, "error": "No telegram ID provided"}
            
            # Prepare user record
            user_record = {
                "telegram_id": telegram_id,
                "username": user_data.get('username'),
                "first_name": user_data.get('first_name'),
                "last_name": user_data.get('last_name'),
                "language_code": user_data.get('language_code'),
                "is_bot": user_data.get('is_bot', False),
                "last_activity": datetime.now(timezone.utc).isoformat(),
                "total_messages": 1,  # Will be incremented
                "preferences": {},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Check if user exists
            existing_user = self.get_user_by_telegram_id(telegram_id)
            
            if existing_user:
                # Update existing user
                user_record["total_messages"] = existing_user.get("total_messages", 0) + 1
                user_record["session_id"] = existing_user.get("session_id")
                user_record["lead_id"] = existing_user.get("lead_id")
                user_record["preferences"] = existing_user.get("preferences", {})
                user_record["created_at"] = existing_user.get("created_at")
                
                result = self._update_user(telegram_id, user_record)
                if result.get('success'):
                    logger.info(f"Updated Telegram user {telegram_id}")
                    return {"success": True, "user": user_record, "action": "updated"}
            else:
                # Create new user
                result = self._create_user(user_record)
                if result.get('success'):
                    logger.info(f"Created new Telegram user {telegram_id}")
                    return {"success": True, "user": user_record, "action": "created"}
            
            return result
            
        except Exception as e:
            logger.error(f"Error in create_or_update_user: {e}")
            return {"success": False, "error": str(e)}
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get user by Telegram ID"""
        try:
            # This would query your telegram_users table
            # For now, we'll use the leads table to find associated users
            result = self.lead_capture_tool.get_leads_by_session(f"telegram_{telegram_id}")
            if result.get('success') and result.get('data'):
                lead = result['data'][0]
                return {
                    "telegram_id": telegram_id,
                    "lead_id": lead.get('id'),
                    "session_id": lead.get('session_id'),
                    "preferences": {}
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user by telegram ID: {e}")
            return None
    
    def update_user_preferences(self, telegram_id: int, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            user = self.get_user_by_telegram_id(telegram_id)
            if user and user.get('lead_id'):
                # Update the associated lead with preferences
                update_data = {
                    "preferences": preferences,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                result = self.lead_capture_tool.update_lead(user['lead_id'], update_data)
                return result.get('success', False)
            return False
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False
    
    def get_user_context_for_llm(self, telegram_id: int) -> Dict[str, Any]:
        """Get comprehensive user context for LLM"""
        try:
            user = self.get_user_by_telegram_id(telegram_id)
            if not user:
                return {"user_known": False}
            
            # Get lead information
            lead_info = {}
            if user.get('lead_id'):
                lead_result = self.lead_capture_tool.get_lead_by_id(user['lead_id'])
                if lead_result.get('success'):
                    lead_info = lead_result.get('data', {})
            
            # Get conversation history
            conversation_history = []
            if user.get('session_id'):
                # This would get conversation history from your session system
                pass
            
            # Build comprehensive context
            context = {
                "user_known": True,
                "telegram_user": {
                    "id": telegram_id,
                    "username": user.get('username'),
                    "first_name": user.get('first_name'),
                    "last_name": user.get('last_name'),
                    "language": user.get('language_code'),
                    "total_messages": user.get('total_messages', 0),
                    "last_activity": user.get('last_activity')
                },
                "lead_information": {
                    "name": lead_info.get('name'),
                    "email": lead_info.get('email'),
                    "phone": lead_info.get('phone'),
                    "target_country": lead_info.get('target_country'),
                    "intake": lead_info.get('intake'),
                    "study_level": lead_info.get('study_level'),
                    "status": lead_info.get('status'),
                    "created_at": lead_info.get('created_at'),
                    "preferences": lead_info.get('preferences', {})
                },
                "conversation_summary": {
                    "total_exchanges": len(conversation_history),
                    "session_id": user.get('session_id'),
                    "lead_id": user.get('lead_id')
                }
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting user context for LLM: {e}")
            return {"user_known": False, "error": str(e)}
    
    def _create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new Telegram user"""
        try:
            # This would insert into telegram_users table
            # For now, we'll create a lead entry
            lead_data = {
                "session_id": f"telegram_{user_data['telegram_id']}",
                "name": f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip(),
                "email": f"telegram_{user_data['telegram_id']}@telegram.user",
                "phone": "",
                "target_country": "",
                "intake": "",
                "study_level": "",
                "status": "telegram_user",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "preferences": user_data.get('preferences', {})
            }
            
            result = self.lead_capture_tool.create_lead(lead_data)
            if result.get('success'):
                return {"success": True, "user_id": result.get('lead_id')}
            return result
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return {"success": False, "error": str(e)}
    
    def _update_user(self, telegram_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing Telegram user"""
        try:
            user = self.get_user_by_telegram_id(telegram_id)
            if user and user.get('lead_id'):
                update_data = {
                    "preferences": user_data.get('preferences', {}),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                result = self.lead_capture_tool.update_lead(user['lead_id'], update_data)
                return result
            return {"success": False, "error": "User not found"}
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return {"success": False, "error": str(e)}

# Global instance
telegram_user_manager = TelegramUserManager()

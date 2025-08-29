#!/usr/bin/env python3
"""
Telegram Bot Integration for AI Chatbot
This shows how easy it is to integrate Telegram with your existing system.
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging
import json
from datetime import datetime
import time
from collections import defaultdict

# Import your existing systems (SAME AS WEB) - with safe fallback
try:
    from app.memory.smart_response import get_smart_response
    from app.memory import get_session_memory
    MEMORY_IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: Memory imports not available: {e}")
    MEMORY_IMPORTS_AVAILABLE = False
    # Create fallback functions
    def get_smart_response():
        return None
    def get_session_memory():
        return None

logger = logging.getLogger(__name__)

# Track users waiting for responses (prevent double question sending)
users_waiting_for_response = set()

# Telegram message models
class TelegramMessage(BaseModel):
    message_id: int
    from_: Dict[str, Any] = Field(alias="from")  # Telegram sends "from", not "from_user"
    chat: Dict[str, Any]
    text: Optional[str] = None
    date: int

class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[TelegramMessage] = None

# Router for Telegram webhooks
telegram_router = APIRouter(prefix="/telegram", tags=["telegram"])

def create_telegram_session_id(user_id: int) -> str:
    """Create a session ID for Telegram users"""
    return f"telegram_{user_id}"

async def send_typing_action(chat_id: int) -> None:
    """Send typing indicator to show bot is working"""
    try:
        import requests
        
        # Get bot token from environment
        try:
            from app.config import settings
            bot_token = settings.TELEGRAM_BOT_TOKEN
        except ImportError:
            import os
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        
        if not bot_token:
            logger.warning("No bot token available for typing indicator")
            return
        
        # Send typing action
        typing_url = f"https://api.telegram.org/bot{bot_token}/sendChatAction"
        typing_data = {
            "chat_id": chat_id,
            "action": "typing"
        }
        
        response = requests.post(typing_url, json=typing_data, timeout=5)
        
        if response.status_code == 200:
            logger.debug(f"✅ Typing indicator sent to chat {chat_id}")
        else:
            logger.warning(f"⚠️ Failed to send typing indicator: {response.status_code}")
            
    except Exception as e:
        logger.warning(f"⚠️ Error sending typing indicator: {e}")

def format_telegram_response(text: str) -> Dict[str, Any]:
    """Format response for Telegram"""
    return {
        "method": "sendMessage",
        "chat_id": None,  # Will be set by the calling function
        "text": text,
        "parse_mode": "HTML",  # Support basic HTML formatting

    }
    

@telegram_router.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle incoming Telegram webhooks"""
    try:
        # Get the update from Telegram
        update_data = await request.json()
        update = TelegramUpdate(**update_data)
        
        if not update.message or not update.message.text:
            return {"ok": True}
        
        message = update.message
        user_id = message.from_["id"]  # Use from_ instead of from_user
        chat_id = message.chat["id"]
        text = message.text
        session_id = create_telegram_session_id(user_id)
        
        # Check if user is already waiting for a response
        if user_id in users_waiting_for_response:
            logger.info(f"⏳ User {user_id} already waiting for response - ignoring message")
            return {"ok": True}  # Ignore message, don't respond
        
        # Check if this is a duplicate message (same text, same user, within 5 seconds)
        current_time = time.time()
        message_key = f"{user_id}_{text}"
        if hasattr(telegram_webhook, 'recent_messages') and message_key in telegram_webhook.recent_messages:
            last_time = telegram_webhook.recent_messages[message_key]
            if current_time - last_time < 5:  # Within 5 seconds
                logger.info(f"⏳ Duplicate message detected for user {user_id} within 5 seconds - ignoring")
                return {"ok": True}
        
        # Store this message to prevent duplicates
        if not hasattr(telegram_webhook, 'recent_messages'):
            telegram_webhook.recent_messages = {}
        telegram_webhook.recent_messages[message_key] = current_time
        
        # Mark user as waiting for response
        users_waiting_for_response.add(user_id)
        
        logger.info(f"📱 Telegram message from user {user_id}: {text}")
        
        # Send typing indicator to show bot is working
        try:
            await send_typing_action(chat_id)
            logger.info(f"⌨️ Sent typing indicator to user {user_id}")
        except Exception as typing_error:
            logger.warning(f"⚠️ Failed to send typing indicator: {typing_error}")
        
        # Get conversation history for this user (SAME AS WEB)
        conversation_history = []
        if MEMORY_IMPORTS_AVAILABLE and get_session_memory():
            try:
                memory = get_session_memory()
                conversation_context = memory.get_conversation_context(session_id)
                conversation_history = conversation_context.get("conversation_history", [])
            except Exception as e:
                logger.warning(f"⚠️ Failed to get conversation history: {e}")
        
        # Check for special commands first
        if text.lower().strip() in ["delete history", "clear history", "reset", "start over", "delete my data", "delete data", "clear data", "remove data"]:
            # Force delete all session data for this user
            if MEMORY_IMPORTS_AVAILABLE and get_session_memory():
                try:
                    memory = get_session_memory()
                    # Force refresh from database and clear
                    memory.clear_session_data(session_id)
                    logger.info(f"🗑️ User {user_id} requested history deletion - session cleared")
                    result = {
                        "success": True,
                        "response": "Your conversation history has been cleared. How can I help you with student visa information?"
                    }
                except Exception as e:
                    logger.error(f"❌ Failed to clear session data: {e}")
                    result = {
                        "success": False,
                        "error": str(e),
                        "response": "I'm experiencing technical difficulties. Please try again."
                    }
            else:
                result = {
                    "success": True,
                    "response": "Your conversation history has been cleared. How can I help you with student visa information?"
                }
        elif text.lower().strip() in ["refresh memory", "sync memory"]:
            # Force refresh session from database (for memory sync issues)
            if MEMORY_IMPORTS_AVAILABLE and get_session_memory():
                try:
                    memory = get_session_memory()
                    # Force refresh from database
                    memory.force_refresh_telegram_session(session_id)
                    logger.info(f"🔄 User {user_id} requested memory refresh - session synced with database")
                    result = {
                        "success": True,
                        "response": "Your session has been refreshed and synced with the database. How can I help you with student visa information?"
                    }
                except Exception as e:
                    logger.error(f"❌ Failed to refresh session: {e}")
                    result = {
                        "success": False,
                        "error": str(e),
                        "response": "I'm experiencing technical difficulties. Please try again."
                    }
            else:
                result = {
                    "success": True,
                    "response": "Your session has been refreshed. How can I help you with student visa information?"
                }
        else:
                    # Process message through your existing smart response system
        logger.info(f"🔍 Processing message through smart response system...")
        if MEMORY_IMPORTS_AVAILABLE and get_smart_response():
            try:
                logger.info(f"🔍 Smart response system available, calling generate_smart_response...")
                result = get_smart_response().generate_smart_response(
                    user_message=text,
                    session_id=session_id,
                    conversation_history=conversation_history
                )
                logger.info(f"🔍 Smart response result: {result}")
            except Exception as e:
                logger.error(f"❌ Smart response failed: {e}")
                result = {
                    "success": False,
                    "error": str(e),
                    "response": "I'm experiencing technical difficulties. Please try again."
                }
        else:
            # Fallback response if smart response system is not available
            logger.warning(f"⚠️ Smart response system not available, using fallback")
            result = {
                "success": True,
                "response": "I'm experiencing technical difficulties. Please try again."
            }
        
        if result.get('success'):
            ai_response = result.get('response', '')
            logger.info(f"🤖 AI Response: {ai_response[:100]}...")
            
            # IMPORTANT: Save conversation exchange to memory for persistence
            if MEMORY_IMPORTS_AVAILABLE and get_session_memory():
                try:
                    memory = get_session_memory()
                    memory.add_conversation_exchange(session_id, text, ai_response)
                    logger.info(f"💾 Conversation saved to memory for session {session_id}")
                except Exception as mem_error:
                    logger.warning(f"⚠️ Failed to save conversation to memory: {mem_error}")
            else:
                logger.info(f"💾 Memory system not available - skipping conversation save")
            
            # Remove user from waiting list - they can now send another message
            users_waiting_for_response.discard(user_id)
            logger.info(f"✅ User {user_id} can now send another message")
            
            # Format response for Telegram
            telegram_response = format_telegram_response(ai_response)
            telegram_response["chat_id"] = chat_id
            
            # Return the response (Telegram will send it)
            return telegram_response
        else:
            logger.error(f"❌ Smart response failed: {result.get('error')}")
            # Remove user from waiting list even on error
            users_waiting_for_response.discard(user_id)
            logger.info(f"✅ User {user_id} removed from waiting list due to error")
            return format_telegram_response("I'm experiencing technical difficulties. Please try again.")
            
    except Exception as e:
        logger.error(f"❌ Telegram webhook error: {e}")
        # Remove user from waiting list on any exception
        if 'user_id' in locals():
            users_waiting_for_response.discard(user_id)
            logger.info(f"✅ User {user_id} removed from waiting list due to exception")
        raise HTTPException(status_code=500, detail="Internal server error")

@telegram_router.get("/set-webhook")
async def set_webhook(bot_token: str, webhook_url: str):
    """Set Telegram webhook URL (for initial setup)"""
    try:
        import requests
        
        # Set webhook with Telegram
        webhook_data = {
            "url": webhook_url,
            "allowed_updates": ["message"],
            "drop_pending_updates": True
        }
        
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/setWebhook",
            json=webhook_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                logger.info(f"✅ Telegram webhook set successfully: {webhook_url}")
                return {"success": True, "message": "Webhook set successfully"}
            else:
                logger.error(f"❌ Failed to set webhook: {result}")
                return {"success": False, "error": result.get("description")}
        else:
            logger.error(f"❌ HTTP error setting webhook: {response.status_code}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        logger.error(f"❌ Error setting webhook: {e}")
        return {"success": False, "error": str(e)}

@telegram_router.get("/bot-info")
async def get_bot_info(bot_token: str):
    """Get bot information from Telegram"""
    try:
        import requests
        
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                bot_info = result.get("result", {})
                return {
                    "success": True,
                    "bot_info": {
                        "id": bot_info.get("id"),
                        "name": bot_info.get("first_name"),
                        "username": bot_info.get("username"),
                        "can_join_groups": bot_info.get("can_join_groups"),
                        "can_read_all_group_messages": bot_info.get("can_read_all_group_messages"),
                        "supports_inline_queries": bot_info.get("supports_inline_queries")
                    }
                }
            else:
                return {"success": False, "error": result.get("description")}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# Example usage in your main.py:
"""
# Add this to your main.py imports:
from telegram_integration import telegram_router

# Add this to your FastAPI app:
app.include_router(telegram_router)

# Your Telegram webhook will be available at:
# https://your-backend-url.com/telegram/webhook
"""

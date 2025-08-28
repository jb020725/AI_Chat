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

# Import your existing systems (SAME AS WEB)
from app.memory.smart_response import get_smart_response
from app.memory import get_session_memory

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
        from app.config import settings
        bot_token = settings.TELEGRAM_BOT_TOKEN
        
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
        "reply_markup": {
            "keyboard": [
                [{"text": "🇺🇸 USA Visa"}],
                [{"text": "🇬🇧 UK Visa"}],
                [{"text": "🇦🇺 Australia Visa"}],
                [{"text": "🇰🇷 South Korea Visa"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
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
        memory = get_session_memory()
        conversation_context = memory.get_conversation_context(session_id)
        conversation_history = conversation_context.get("conversation_history", [])
        
        # Process message through your existing smart response system
        result = get_smart_response().generate_smart_response(
            user_message=text,
            session_id=session_id,
            conversation_history=conversation_history
        )
        
        if result.get('success'):
            ai_response = result.get('response', '')
            logger.info(f"🤖 AI Response: {ai_response[:100]}...")
            
            # IMPORTANT: Save conversation exchange to memory for persistence
            try:
                memory.add_conversation_exchange(session_id, text, ai_response)
                logger.info(f"💾 Conversation saved to memory for session {session_id}")
            except Exception as mem_error:
                logger.warning(f"⚠️ Failed to save conversation to memory: {mem_error}")
            
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
#   F o r c e   r e d e p l o y   -   0 8 / 2 8 / 2 0 2 5   1 8 : 4 7 : 4 1  
 
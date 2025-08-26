#!/usr/bin/env python3
"""
Telegram Bot Integration for AI Chatbot
This shows how easy it is to integrate Telegram with your existing system.
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import json
from datetime import datetime

# Import your existing systems (SAME AS WEB)
from app.memory.smart_response import get_smart_response
from app.memory import get_session_memory

logger = logging.getLogger(__name__)

# Telegram message models
class TelegramMessage(BaseModel):
    message_id: int
    from_user: Dict[str, Any]
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
        user_id = message.from_user["id"]
        chat_id = message.chat["id"]
        text = message.text
        session_id = create_telegram_session_id(user_id)
        
        logger.info(f"📱 Telegram message from user {user_id}: {text}")
        
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
            
            # Format response for Telegram
            telegram_response = format_telegram_response(ai_response)
            telegram_response["chat_id"] = chat_id
            
            # Return the response (Telegram will send it)
            return telegram_response
        else:
            logger.error(f"❌ Smart response failed: {result.get('error')}")
            return format_telegram_response("I'm experiencing technical difficulties. Please try again.")
            
    except Exception as e:
        logger.error(f"❌ Telegram webhook error: {e}")
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

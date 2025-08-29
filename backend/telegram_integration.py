#!/usr/bin/env python3
"""
Telegram Bot Integration - FOCUSED VERSION
Fixes: Double greeting + Delete system + Typing indicator + Message queue
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)

# Track users currently being processed (message queue system)
users_being_processed = set()

# Simple message models
class TelegramMessage(BaseModel):
    message_id: int
    from_: Dict[str, Any] = Field(alias="from")
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

def format_telegram_response(text: str, chat_id: int) -> Dict[str, Any]:
    """Format response for Telegram"""
    return {
        "method": "sendMessage",
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

async def send_typing_action(chat_id: int) -> None:
    """Send typing indicator - appears where message will come"""
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
        
        # Send typing action - shows "typing..." in chat
        typing_url = f"https://api.telegram.org/bot{bot_token}/sendChatAction"
        typing_data = {
            "chat_id": chat_id,
            "action": "typing"
        }
        
        response = requests.post(typing_url, json=typing_data, timeout=5)
        
        if response.status_code == 200:
            logger.debug(f"⌨️ Typing indicator sent to chat {chat_id}")
        else:
            logger.warning(f"⚠️ Failed to send typing indicator: {response.status_code}")
            
    except Exception as e:
        logger.warning(f"⚠️ Error sending typing indicator: {e}")

async def stop_typing_action(chat_id: int) -> None:
    """Stop typing indicator"""
    try:
        import requests
        
        try:
            from app.config import settings
            bot_token = settings.TELEGRAM_BOT_TOKEN
        except ImportError:
            import os
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        
        if not bot_token:
            return
        
        # Send stop typing action
        typing_url = f"https://api.telegram.org/bot{bot_token}/sendChatAction"
        typing_data = {
            "chat_id": chat_id,
            "action": "stop_typing"
        }
        
        requests.post(typing_url, json=typing_data, timeout=5)
        
    except Exception as e:
        logger.warning(f"⚠️ Error stopping typing indicator: {e}")

@telegram_router.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle incoming Telegram webhooks - FOCUSED VERSION with typing + queue"""
    try:
        # Get the update from Telegram
        update_data = await request.json()
        update = TelegramUpdate(**update_data)
        
        if not update.message or not update.message.text:
            return {"ok": True}
        
        message = update.message
        user_id = message.from_["id"]
        chat_id = message.chat["id"]
        text = message.text
        session_id = create_telegram_session_id(user_id)
        
        logger.info(f"📱 Telegram message from user {user_id}: {text}")
        
        # MESSAGE QUEUE SYSTEM: Check if user is already being processed
        if user_id in users_being_processed:
            logger.info(f"⏳ User {user_id} already being processed - ignoring message")
            return {"ok": True}  # Ignore message, don't respond
        
        # Mark user as being processed
        users_being_processed.add(user_id)
        logger.info(f"🔄 User {user_id} marked as being processed")
        
        try:
            # Handle /start command
            if text.lower().strip() == "/start":
                response_text = "Hello! Welcome to our student visa consultancy. I'm here to help you with information about student visas for USA, UK, Australia, and South Korea. How can I assist you today?"
                
                # Remove user from processing list
                users_being_processed.discard(user_id)
                logger.info(f"✅ User {user_id} removed from processing list after start command")
                
                return format_telegram_response(response_text, chat_id)
            
            # Handle delete commands - ACTUALLY DELETE DATA
            elif text.lower().strip() in ["delete my data", "delete data", "clear data", "delete my chat", "delete chat", "clear chat", "delete history", "clear history"]:
                try:
                    from app.memory import get_session_memory
                    memory = get_session_memory()
                    
                    # ACTUALLY DELETE the session data
                    memory.clear_session_data(session_id)
                    logger.info(f"🗑️ User {user_id} requested data deletion - session data CLEARED from database")
                    
                    response_text = "✅ Your data has been completely deleted from our system. This is a fresh start - I have no memory of our previous conversation. How can I help you with student visa information?"
                    
                except Exception as e:
                    logger.error(f"❌ Failed to delete session data: {e}")
                    response_text = "I'm experiencing technical difficulties with data deletion. Please try again."
                
                # Remove user from processing list
                users_being_processed.discard(user_id)
                logger.info(f"✅ User {user_id} removed from processing list after delete command")
                
                return format_telegram_response(response_text, chat_id)
            
            # For normal messages, use smart response system
            try:
                # SHOW TYPING INDICATOR - appears where message will come
                await send_typing_action(chat_id)
                logger.info(f"⌨️ Typing indicator shown for user {user_id}")
                
                from app.memory.smart_response import get_smart_response
                from app.memory import get_session_memory
                
                # Get conversation history
                memory = get_session_memory()
                conversation_context = memory.get_conversation_context(session_id)
                conversation_history = conversation_context.get("conversation_history", [])
                
                # CRITICAL FIX: If this is a fresh conversation (no history), force empty context
                if not conversation_history:
                    logger.info(f"🆕 Fresh conversation detected for user {user_id} - forcing empty context")
                    conversation_history = []
                
                # Generate response
                smart_response = get_smart_response()
                result = smart_response.generate_smart_response(
                    user_message=text,
                    session_id=session_id,
                    conversation_history=conversation_history
                )
                
                if result.get('success'):
                    ai_response = result.get('response', '')
                    
                    # Save conversation to memory
                    memory.add_conversation_exchange(session_id, text, ai_response)
                    logger.info(f"💾 Conversation saved to memory for session {session_id}")
                    
                    # STOP TYPING INDICATOR
                    await stop_typing_action(chat_id)
                    logger.info(f"⏹️ Typing indicator stopped for user {user_id}")
                    
                    # Remove user from processing list - they can now send another message
                    users_being_processed.discard(user_id)
                    logger.info(f"✅ User {user_id} can now send another message")
                    
                    return format_telegram_response(ai_response, chat_id)
                else:
                    logger.error(f"❌ Smart response failed: {result.get('error')}")
                    
                    # STOP TYPING INDICATOR
                    await stop_typing_action(chat_id)
                    
                    # Remove user from processing list
                    users_being_processed.discard(user_id)
                    logger.info(f"✅ User {user_id} removed from processing list due to error")
                    
                    return format_telegram_response("I'm experiencing technical difficulties. Please try again.", chat_id)
                    
            except Exception as e:
                logger.error(f"❌ Smart response failed: {e}")
                
                # STOP TYPING INDICATOR
                await stop_typing_action(chat_id)
                
                # Remove user from processing list
                users_being_processed.discard(user_id)
                logger.info(f"✅ User {user_id} removed from processing list due to error")
                
                # Fallback response
                fallback_text = "Hello! I'm here to help with student visa information. How can I assist you today?"
                return format_telegram_response(fallback_text, chat_id)
                
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            # Remove user from processing list on any error
            users_being_processed.discard(user_id)
            logger.info(f"✅ User {user_id} removed from processing list due to processing error")
            raise
            
    except Exception as e:
        logger.error(f"❌ Telegram webhook error: {e}")
        # Remove user from processing list on any exception
        if 'user_id' in locals():
            users_being_processed.discard(user_id)
            logger.info(f"✅ User {user_id} removed from processing list due to exception")
        raise HTTPException(status_code=500, detail="Internal server error")

@telegram_router.get("/set-webhook")
async def set_webhook(bot_token: str, webhook_url: str):
    """Set Telegram webhook URL"""
    try:
        import requests
        
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
                return {"success": True, "message": "Webhook set successfully"}
            else:
                return {"success": False, "error": result.get("description")}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


#!/usr/bin/env python3
"""
Telegram Webhook Setup Script
This script will set up the webhook for your Telegram bot.
"""

import requests
import json

# Your bot details
BOT_TOKEN = "7628745027:AAGW6adRBzUNwa9KvjalY8EqTFa8CqzGJAc"
BACKEND_URL = "https://ai-chatbot-backend-irsvqln4dq-uc.a.run.app"
WEBHOOK_URL = f"{BACKEND_URL}/telegram/webhook"

def setup_webhook():
    """Set up the Telegram webhook"""
    print("🚀 Setting up Telegram webhook...")
    print(f"📡 Backend URL: {BACKEND_URL}")
    print(f"🔗 Webhook URL: {WEBHOOK_URL}")
    print(f"🤖 Bot Token: {BOT_TOKEN[:10]}...")
    
    try:
        # Set webhook with Telegram
        webhook_data = {
            "url": WEBHOOK_URL,
            "allowed_updates": ["message"],
            "drop_pending_updates": True
        }
        
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
            json=webhook_data,
            timeout=10
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📋 Response: {json.dumps(result, indent=2)}")
            
            if result.get("ok"):
                print("✅ Webhook set successfully!")
                print(f"🔗 Your bot is now connected to: {WEBHOOK_URL}")
                return True
            else:
                print(f"❌ Failed to set webhook: {result.get('description')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"📋 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")
        return False

def get_bot_info():
    """Get bot information"""
    try:
        response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                bot_info = result.get("result", {})
                print(f"🤖 Bot Info:")
                print(f"   Name: {bot_info.get('first_name')}")
                print(f"   Username: @{bot_info.get('username')}")
                print(f"   ID: {bot_info.get('id')}")
                return True
        
        print("❌ Failed to get bot info")
        return False
        
    except Exception as e:
        print(f"❌ Error getting bot info: {e}")
        return False

def test_webhook():
    """Test if webhook is working"""
    try:
        response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                webhook_info = result.get("result", {})
                print(f"🔍 Webhook Info:")
                print(f"   URL: {webhook_info.get('url')}")
                print(f"   Has Custom Certificate: {webhook_info.get('has_custom_certificate')}")
                print(f"   Pending Update Count: {webhook_info.get('pending_update_count')}")
                print(f"   Last Error Date: {webhook_info.get('last_error_date', 'None')}")
                print(f"   Last Error Message: {webhook_info.get('last_error_message', 'None')}")
                return True
        
        print("❌ Failed to get webhook info")
        return False
        
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")
        return False

if __name__ == "__main__":
    print("🤖 Telegram Bot Setup")
    print("=" * 50)
    
    # Get bot info
    print("\n1. Getting bot information...")
    get_bot_info()
    
    # Set up webhook
    print("\n2. Setting up webhook...")
    success = setup_webhook()
    
    # Test webhook
    print("\n3. Testing webhook...")
    test_webhook()
    
    if success:
        print("\n✅ Setup completed successfully!")
        print(f"🚀 Your bot is ready at: t.me/visa_consultant_bot")
        print(f"💬 Test it by sending a message!")
    else:
        print("\n❌ Setup failed. Check the errors above.")
    
    print("\n" + "=" * 50)

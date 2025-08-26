#!/usr/bin/env python3
"""
COMPREHENSIVE SYSTEM DEBUG FILE
This will test ALL components and show exactly what's working and what's not.
Run this to diagnose the entire system.
"""

import os
import sys
import logging
import asyncio
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Configure logging to see everything
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug_system.log')
    ]
)

logger = logging.getLogger(__name__)

def test_environment_variables():
    """Test if all required environment variables are set"""
    print("\n" + "="*80)
    print("🔍 TESTING ENVIRONMENT VARIABLES")
    print("="*80)
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY',
        'SMTP_SERVER',
        'SMTP_PORT',
        'SMTP_USERNAME',
        'SMTP_PASSWORD',
        'FROM_EMAIL',
        'FROM_NAME',
        'LEAD_NOTIFICATION_EMAIL',
        'ENABLE_EMAIL_NOTIFICATIONS',
        'TELEGRAM_BOT_TOKEN',
        'GEMINI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:20]}{'...' if len(value) > 20 else ''}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n🚨 MISSING ENVIRONMENT VARIABLES: {missing_vars}")
    else:
        print("\n✅ ALL ENVIRONMENT VARIABLES ARE SET")
    
    return len(missing_vars) == 0

def test_config_loading():
    """Test if the config can be loaded properly"""
    print("\n" + "="*80)
    print("🔍 TESTING CONFIG LOADING")
    print("="*80)
    
    try:
        from app.config import settings
        print("✅ Config module imported successfully")
        
        # Test specific settings
        print(f"✅ SUPABASE_URL: {settings.SUPABASE_URL[:30]}...")
        print(f"✅ SMTP_SERVER: {settings.SMTP_SERVER}")
        print(f"✅ TELEGRAM_BOT_TOKEN: {settings.TELEGRAM_BOT_TOKEN[:20] if settings.TELEGRAM_BOT_TOKEN else 'NOT SET'}...")
        
        return True
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_smart_response_initialization():
    """Test if SmartResponse can be initialized properly"""
    print("\n" + "="*80)
    print("🔍 TESTING SMART RESPONSE INITIALIZATION")
    print("="*80)
    
    try:
        from app.memory.smart_response import get_smart_response
        
        print("✅ SmartResponse module imported successfully")
        
        # Try to get an instance
        smart_response = get_smart_response()
        print("✅ SmartResponse instance created successfully")
        
        # Test the lead capture tool
        if hasattr(smart_response, 'lead_capture_tool'):
            print("✅ LeadCaptureTool is attached")
            print(f"✅ LeadCaptureTool config: {smart_response.lead_capture_tool.config}")
        else:
            print("❌ LeadCaptureTool is NOT attached")
        
        return True
    except Exception as e:
        print(f"❌ SmartResponse initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_lead_capture_tool():
    """Test if the lead capture tool works"""
    print("\n" + "="*80)
    print("🔍 TESTING LEAD CAPTURE TOOL")
    print("="*80)
    
    try:
        from app.tools.lead_capture_tool import LeadCaptureTool
        from app.config import settings
        
        print("✅ LeadCaptureTool module imported successfully")
        
        # Create config
        config = {
            "supabase_url": settings.SUPABASE_URL,
            "supabase_service_role_key": settings.SUPABASE_SERVICE_ROLE_KEY,
            "smtp_server": settings.SMTP_SERVER,
            "smtp_port": settings.SMTP_PORT,
            "smtp_username": settings.SMTP_USERNAME,
            "smtp_password": settings.SMTP_PASSWORD,
            "from_email": settings.FROM_EMAIL,
            "from_name": settings.FROM_NAME,
            "lead_notification_email": settings.LEAD_NOTIFICATION_EMAIL,
            "enable_email_notifications": settings.ENABLE_EMAIL_NOTIFICATIONS
        }
        
        print("✅ Config created successfully")
        
        # Initialize tool
        tool = LeadCaptureTool(config)
        print("✅ LeadCaptureTool initialized successfully")
        
        # Test Supabase connection
        print("🔍 Testing Supabase connection...")
        result = tool.search_leads({}, limit=1)
        if result.get('success'):
            print("✅ Supabase connection successful")
        else:
            print(f"❌ Supabase connection failed: {result.get('error')}")
        
        return True
    except Exception as e:
        print(f"❌ LeadCaptureTool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_email_tool():
    """Test if the email tool works"""
    print("\n" + "="*80)
    print("🔍 TESTING EMAIL TOOL")
    print("="*80)
    
    try:
        from app.tools.email_tool import EmailTool
        from app.config import settings
        
        print("✅ EmailTool module imported successfully")
        
        # Create config
        config = {
            "smtp_server": settings.SMTP_SERVER,
            "smtp_port": settings.SMTP_PORT,
            "smtp_username": settings.SMTP_USERNAME,
            "smtp_password": settings.SMTP_PASSWORD,
            "from_email": settings.FROM_EMAIL,
            "from_name": settings.FROM_NAME,
            "lead_notification_email": settings.LEAD_NOTIFICATION_EMAIL,
            "enable_email_notifications": settings.ENABLE_EMAIL_NOTIFICATIONS
        }
        
        print("✅ Email config created successfully")
        
        # Initialize tool
        tool = EmailTool(config)
        print("✅ EmailTool initialized successfully")
        
        # Check if email is configured
        if tool.email_configured:
            print("✅ Email is properly configured")
            print(f"✅ SMTP Server: {tool.smtp_server}")
            print(f"✅ SMTP Port: {tool.smtp_port}")
            print(f"✅ Username: {tool.smtp_username}")
            print(f"✅ From Email: {tool.from_email}")
            print(f"✅ Notification Email: {tool.lead_notification_email}")
        else:
            print("❌ Email is NOT properly configured")
            print(f"❌ SMTP Server: {tool.smtp_server}")
            print(f"❌ SMTP Port: {tool.smtp_port}")
            print(f"❌ Username: {tool.smtp_username}")
            print(f"❌ Password: {'SET' if tool.smtp_password else 'NOT SET'}")
        
        return tool.email_configured
    except Exception as e:
        print(f"❌ EmailTool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_telegram_integration():
    """Test if Telegram integration works"""
    print("\n" + "="*80)
    print("🔍 TESTING TELEGRAM INTEGRATION")
    print("="*80)
    
    try:
        from app.config import settings
        
        if not settings.TELEGRAM_BOT_TOKEN:
            print("❌ TELEGRAM_BOT_TOKEN is not set")
            return False
        
        print(f"✅ TELEGRAM_BOT_TOKEN is set: {settings.TELEGRAM_BOT_TOKEN[:20]}...")
        
        # Test if we can make a request to Telegram API
        import requests
        
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getMe"
        print(f"🔍 Testing Telegram API connection: {url}")
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                print(f"✅ Telegram bot connection successful!")
                print(f"✅ Bot name: {bot_info.get('first_name')}")
                print(f"✅ Bot username: {bot_info.get('username')}")
                print(f"✅ Bot ID: {bot_info.get('id')}")
                return True
            else:
                print(f"❌ Telegram API error: {data}")
                return False
        else:
            print(f"❌ Telegram API request failed: {response.status_code}")
            print(f"❌ Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Telegram integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_extraction_logic():
    """Test if the enhanced extraction logic works"""
    print("\n" + "="*80)
    print("🔍 TESTING ENHANCED EXTRACTION LOGIC")
    print("="*80)
    
    try:
        from app.memory.smart_response import SmartResponse
        
        print("✅ SmartResponse class imported successfully")
        
        # Create a test instance
        smart_response = SmartResponse()
        print("✅ SmartResponse test instance created")
        
        # Test messages
        test_messages = [
            "I want to study bachelor in computer science in USA",
            "My name is John Smith, email is john@example.com, phone is 1234567890",
            "I'm interested in master's degree in engineering in UK",
            "Hello, I want to apply for PhD in medicine in Australia"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n🔍 Test {i}: '{message}'")
            try:
                contact_info = smart_response._extract_contact_info(message)
                print(f"✅ Extraction result: {contact_info}")
            except Exception as e:
                print(f"❌ Extraction failed: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Extraction logic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_endpoints():
    """Test if the main API endpoints are accessible"""
    print("\n" + "="*80)
    print("🔍 TESTING MAIN API ENDPOINTS")
    print("="*80)
    
    try:
        # Test if we can import the main app
        from main import app
        print("✅ Main app imported successfully")
        
        # Check available routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        print(f"✅ Available routes: {routes}")
        
        # Check if critical endpoints exist
        critical_endpoints = ['/api/chat', '/api/leads', '/api/version']
        for endpoint in critical_endpoints:
            if endpoint in routes:
                print(f"✅ {endpoint} endpoint exists")
            else:
                print(f"❌ {endpoint} endpoint missing")
        
        return True
    except Exception as e:
        print(f"❌ Main endpoints test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 STARTING COMPREHENSIVE SYSTEM DEBUG")
    print(f"📅 Time: {datetime.now()}")
    print(f"📁 Working Directory: {os.getcwd()}")
    
    results = {}
    
    # Run all tests
    results['environment'] = test_environment_variables()
    results['config'] = test_config_loading()
    results['smart_response'] = test_smart_response_initialization()
    results['lead_capture'] = test_lead_capture_tool()
    results['email'] = test_email_tool()
    results['telegram'] = test_telegram_integration()
    results['extraction'] = test_extraction_logic()
    results['endpoints'] = test_main_endpoints()
    
    # Summary
    print("\n" + "="*80)
    print("📊 DEBUG SUMMARY")
    print("="*80)
    
    passed = sum(results.values())
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test.upper()}")
    
    print(f"\n🎯 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL SYSTEMS ARE WORKING!")
    else:
        print("🚨 SOME SYSTEMS ARE FAILING - CHECK THE LOGS ABOVE")
    
    # Save results to file
    with open('debug_results.txt', 'w') as f:
        f.write(f"Debug Results - {datetime.now()}\n")
        f.write("="*50 + "\n")
        for test, result in results.items():
            f.write(f"{test}: {'PASS' if result else 'FAIL'}\n")
        f.write(f"\nOverall: {passed}/{total} tests passed\n")

if __name__ == "__main__":
    main()

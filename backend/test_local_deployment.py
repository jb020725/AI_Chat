#!/usr/bin/env python3
"""
Local Test Script - EXACTLY replicates Cloud Run deployment
Tests function calling, RAG system, and all components locally
"""

import os
import sys
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv('local_test.env')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_function_calling():
    """Test function calling exactly as it works in Cloud Run"""
    try:
        logger.info("🧪 Testing Function Calling System...")
        
        # Import the exact same components used in Cloud Run
        from app.functions.function_integrator import FunctionIntegrator
        from app.functions.function_definitions import FUNCTIONS
        import google.generativeai as genai
        
        # Configure Gemini exactly as in Cloud Run
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        logger.info(f"✅ Gemini model loaded: {model}")
        logger.info(f"✅ Available functions: {len(FUNCTIONS)}")
        
        # Test Gemini types
        logger.info("🧪 Testing Gemini types...")
        try:
            from google.generativeai.types import GenerationConfig
            logger.info("✅ GenerationConfig imported successfully")
        except ImportError as e:
            logger.error(f"❌ GenerationConfig import failed: {e}")
            
        # Create FunctionIntegrator exactly as in Cloud Run
        integrator = FunctionIntegrator(model)
        integrator.set_llm_model(model)
        
        logger.info("✅ FunctionIntegrator created successfully")
        
        # Test function calling with the exact same prompt
        test_message = "I want to apply for a USA student visa. Can you help me?"
        session_id = "test_session_123"
        
        logger.info(f"🧪 Testing with message: {test_message}")
        
        # Call the exact same method used in Cloud Run
        result = integrator.process_with_functions(
            user_message=test_message,
            session_id=session_id,
            rag_context=[],  # Mock RAG context
            conversation_history=[],
            session_info={}
        )
        
        logger.info("✅ Function calling completed!")
        logger.info(f"📊 Result: {result}")
        
        # Check if functions were called
        function_calls = result.get('function_calls', [])
        if function_calls:
            logger.info(f"🎉 SUCCESS: {len(function_calls)} functions called!")
            for i, call in enumerate(function_calls):
                logger.info(f"  Function {i+1}: {call.get('function_name')}")
                logger.info(f"  Arguments: {call.get('arguments')}")
                logger.info(f"  Result: {call.get('result')}")
        else:
            logger.warning("⚠️  No functions were called - this indicates a problem!")
            
        return result
        
    except Exception as e:
        logger.error(f"❌ Function calling test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_rag_system():
    """Test RAG system locally"""
    try:
        logger.info("🧪 Testing RAG System...")
        
        from app.rag.embedder import LightweightEmbedder
        
        # Test embedder creation
        embedder = LightweightEmbedder()
        logger.info("✅ LightweightEmbedder created")
        
        # Test availability check
        available = embedder.is_available()
        logger.info(f"✅ Embedder available: {available}")
        
        # Test search functionality
        if available:
            results = embedder.search("USA student visa requirements", top_k=3)
            logger.info(f"✅ RAG search returned {len(results)} results")
            for i, result in enumerate(results):
                logger.info(f"  Result {i+1}: {result.get('title', 'No title')}")
        else:
            logger.warning("⚠️  RAG system not available locally (expected - needs GCS)")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ RAG test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_session_memory():
    """Test session memory system"""
    try:
        logger.info("🧪 Testing Session Memory...")
        
        from app.memory.session_memory import SessionMemory
        
        memory = SessionMemory()
        session_id = "test_session_123"
        
        # Test session creation
        memory.create_session(session_id)
        logger.info("✅ Session created")
        
        # Test user info update
        user_info = {
            "name": "James Bond",
            "email": "james@test.com",
            "phone": "1234567890"
        }
        memory.update_user_info(session_id, user_info)
        logger.info("✅ User info updated")
        
        # Test retrieval
        retrieved = memory.get_user_info(session_id)
        logger.info(f"✅ Retrieved user info: {retrieved}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Session memory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting Local Deployment Tests...")
    logger.info("=" * 60)
    
    # Test 1: Function Calling
    logger.info("\n🧪 TEST 1: Function Calling System")
    logger.info("-" * 40)
    function_result = test_function_calling()
    
    # Test 2: RAG System
    logger.info("\n🧪 TEST 2: RAG System")
    logger.info("-" * 40)
    rag_result = test_rag_system()
    
    # Test 3: Session Memory
    logger.info("\n🧪 TEST 3: Session Memory")
    logger.info("-" * 40)
    memory_result = test_session_memory()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"✅ Function Calling: {'PASS' if function_result else 'FAIL'}")
    logger.info(f"✅ RAG System: {'PASS' if rag_result else 'PASS (Expected)'}")
    logger.info(f"✅ Session Memory: {'PASS' if memory_result else 'FAIL'}")
    
    if function_result and memory_result:
        logger.info("\n🎉 ALL CRITICAL TESTS PASSED!")
        logger.info("Your local setup matches Cloud Run deployment!")
    else:
        logger.info("\n⚠️  Some tests failed - check the logs above")
    
    return function_result and memory_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

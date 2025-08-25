#!/usr/bin/env python3
"""
Quick test for concise response changes
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv('local_test.env')

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_concise_responses():
    """Test that responses are now more concise"""
    try:
        from app.memory.smart_response import SmartResponseGenerator
        
        logger.info("🧪 Testing Concise Responses...")
        
        # Initialize smart response generator
        generator = SmartResponseGenerator()
        
        # Test 1: Simple RAG response
        logger.info("📝 Testing simple RAG response...")
        test_rag_context = [{
            'title': 'USA Student Visa Requirements',
            'content': 'The USA student visa (F-1) requires a valid passport, Form DS-160 confirmation, SEVIS fee payment, visa application fee, and financial documents showing sufficient funds for tuition and living expenses. You must also demonstrate strong ties to your home country and intent to return after studies.'
        }]
        
        response = generator._generate_simple_rag_response("What are USA visa requirements?", test_rag_context)
        logger.info(f"Response: {response}")
        
        # Check if response is concise (less than 200 characters)
        if len(response) < 200:
            logger.info("✅ Simple RAG response is concise!")
        else:
            logger.warning(f"⚠️ Simple RAG response might be too long: {len(response)} characters")
        
        # Test 2: Basic domain response
        logger.info("📝 Testing basic domain response...")
        response = generator._generate_basic_domain_response("I want to contact you")
        logger.info(f"Response: {response}")
        
        if len(response) < 150:
            logger.info("✅ Basic domain response is concise!")
        else:
            logger.warning(f"⚠️ Basic domain response might be too long: {len(response)} characters")
        
        # Test 3: Out of domain response
        logger.info("📝 Testing out of domain response...")
        response = generator._generate_out_of_domain_response({'confidence': 0.9})
        logger.info(f"Response: {response}")
        
        if len(response) < 150:
            logger.info("✅ Out of domain response is concise!")
        else:
            logger.warning(f"⚠️ Out of domain response might be too long: {len(response)} characters")
        
        logger.info("✅ All concise response tests completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Concise response test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_concise_responses()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Test script to verify RAG fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.rag.retriever import retrieve
from app.functions.function_handlers import FunctionHandlers
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rag_retrieval():
    """Test RAG retrieval with country detection"""
    print("🧪 Testing RAG Retrieval Fixes...")
    
    test_queries = [
        "usa student visa requirements",
        "uk student visa process", 
        "australia student visa",
        "south korea d-2 visa",
        "student visa information"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        try:
            results = retrieve(query, top_k=3)
            print(f"   Found {len(results)} results")
            
            for i, result in enumerate(results, 1):
                country = result.get('country', 'Unknown')
                title = result.get('title', 'Unknown')
                score = result.get('score', 0.0)
                print(f"   {i}. Country: {country}, Score: {score:.3f}, Title: {title[:50]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_lead_creation():
    """Test lead creation logic"""
    print("\n🧪 Testing Lead Creation Logic...")
    
    handlers = FunctionHandlers()
    
    # Test case 1: Name + Email (should create lead)
    test_data_1 = {
        'session_id': 'test_session_1',
        'user_query': 'My name is Janak Baht and my email is janak@test.com',
        'conversation_context': 'User is interested in USA student visa'
    }
    
    print(f"\n📝 Test 1: Name + Email")
    try:
        result = handlers.detect_and_save_contact_info(**test_data_1)
        print(f"   Success: {result.get('success')}")
        print(f"   Saved as lead: {result.get('data', {}).get('saved_as_lead')}")
        print(f"   Message: {result.get('data', {}).get('message', 'No message')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test case 2: Name + Phone (should create lead)
    test_data_2 = {
        'session_id': 'test_session_2', 
        'user_query': 'My name is John Doe and my phone is +1234567890',
        'conversation_context': 'User is interested in UK student visa'
    }
    
    print(f"\n📝 Test 2: Name + Phone")
    try:
        result = handlers.detect_and_save_contact_info(**test_data_2)
        print(f"   Success: {result.get('success')}")
        print(f"   Saved as lead: {result.get('data', {}).get('saved_as_lead')}")
        print(f"   Message: {result.get('data', {}).get('message', 'No message')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Testing RAG and Lead Creation Fixes")
    print("=" * 50)
    
    test_rag_retrieval()
    test_lead_creation()
    
    print("\n✅ Testing complete!")

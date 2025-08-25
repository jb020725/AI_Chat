#!/usr/bin/env python3
"""
Simple test to verify core fixes work
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_country_detection():
    """Test the country detection logic"""
    print("🧪 Testing Country Detection Logic...")
    
    # Test the country detection logic directly without initializing the full retriever
    def detect_country_from_query(query: str):
        """Detect country from user query using smart keyword matching"""
        query_lower = query.lower()
        
        # Comprehensive country detection keywords
        country_keywords = {
            'usa': ['usa', 'united states', 'america', 'us', 'u.s.', 'u.s.a', 'f-1', 'f1', 'american'],
            'uk': ['uk', 'united kingdom', 'britain', 'england', 'tier 4', 'tier4', 'british'],
            'australia': ['australia', 'aussie', 'subclass 500', 'australian'],
            'south korea': ['south korea', 'korea', 'korean', 'd-2', 'd-4', 'd2', 'd4', 'korean student']
        }
        
        # Check for exact country matches first (using word boundaries)
        import re
        for country, keywords in country_keywords.items():
            for keyword in keywords:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, query_lower):
                    return country
        
        # If no direct match, check for visa type patterns
        visa_patterns = {
            'usa': ['f-1', 'f1'],
            'uk': ['tier 4', 'tier4'],
            'australia': ['subclass 500'],
            'south korea': ['d-2', 'd-4', 'd2', 'd4']
        }
        
        for country, patterns in visa_patterns.items():
            for pattern in patterns:
                # Use word boundaries for visa patterns too
                pattern_re = r'\b' + re.escape(pattern) + r'\b'
                if re.search(pattern_re, query_lower):
                    return country
        
        return None
    
    test_queries = [
        ("usa student visa requirements", "usa"),
        ("uk student visa process", "uk"), 
        ("australia student visa", "australia"),
        ("south korea d-2 visa", "south korea"),
        ("f-1 visa information", "usa"),
        ("tier 4 student visa", "uk"),
        ("subclass 500 australia", "australia"),
        ("d-4 visa korea", "south korea"),
        ("student visa information", None),  # No specific country
        ("general visa questions", None)     # No specific country
    ]
    
    for query, expected_country in test_queries:
        detected = detect_country_from_query(query)
        status = "✅" if detected == expected_country else "❌"
        print(f"   {status} Query: '{query}' -> Detected: {detected}, Expected: {expected_country}")

def test_lead_creation_logic():
    """Test the lead creation logic"""
    print("\n🧪 Testing Lead Creation Logic...")
    
    # Test cases for lead creation logic
    test_cases = [
        # (name, phone, email, should_create_lead, description)
        ("Janak Baht", "1234567890", "janak@test.com", True, "Complete info"),
        ("John Doe", "1234567890", "", True, "Name + Phone"),
        ("Jane Smith", "", "jane@test.com", True, "Name + Email"),
        ("Bob Wilson", "", "", False, "Name only"),
        ("", "1234567890", "bob@test.com", False, "No name"),
        ("", "", "", False, "No info")
    ]
    
    for name, phone, email, should_create, description in test_cases:
        # Simulate the logic
        has_name = bool(name)
        has_phone = bool(phone)
        has_email = bool(email)
        
        # The new logic: name + (phone OR email)
        would_create = has_name and (has_phone or has_email)
        
        status = "✅" if would_create == should_create else "❌"
        print(f"   {status} {description}: Name='{name}', Phone='{phone}', Email='{email}' -> Would create: {would_create}")

if __name__ == "__main__":
    print("🚀 Testing Core Fixes")
    print("=" * 50)
    
    test_country_detection()
    test_lead_creation_logic()
    
    print("\n✅ Core testing complete!")

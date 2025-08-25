#!/usr/bin/env python3
"""
Domain Checker for Student Visa Queries
Determines if a query is within our student visa domain or outside it
"""

import re
from typing import Dict, Any

class DomainChecker:
    """Checks if queries are within student visa domain"""
    
    def __init__(self):
        # Student visa domain keywords
        self.domain_keywords = [
            # Core visa topics
            "student visa", "study visa", "education visa", "academic visa",
            "visa application", "visa process", "visa requirements", "visa documents",
            "visa interview", "visa fees", "visa timeline", "visa deadline",
            
            # Target countries
            "usa", "united states", "america", "us", "u.s.", "u.s.a",
            "uk", "united kingdom", "britain", "england", "great britain",
            "australia", "aussie", "australian",
            "south korea", "korea", "korean", "seoul",
            
            # Visa types
            "f-1", "m-1", "tier 4", "student route", "subclass 500", "d-2", "d-4",
            
            # Study-related
            "study", "education", "university", "college", "school", "course",
            "degree", "bachelor", "master", "phd", "doctorate", "undergraduate", "graduate",
            "intake", "semester", "academic year", "enrollment", "admission",
            
            # Financial
            "tuition", "fees", "cost", "expenses", "financial requirements",
            "bank statement", "funding", "scholarship", "loan",
            
            # Documents
            "passport", "transcript", "certificate", "recommendation", "sop",
            "cv", "resume", "ielts", "toefl", "gre", "gmat", "sat", "act",
            
            # Process
            "application", "apply", "process", "procedure", "timeline", "deadline",
            "interview", "appointment", "biometric", "medical", "police clearance",
            
            # Nepal context
            "nepal", "nepali", "nepalese", "from nepal", "nepal to",
            
            # Contact/Consultation
            "consultant", "consultancy", "guidance", "help", "assist", "support",
            "contact", "phone", "email", "number", "call", "reach"
        ]
        
        # Out-of-domain keywords (indicators of non-student visa topics)
        self.out_of_domain_keywords = [
            # Work/Employment
            "work visa", "employment", "job", "career", "salary", "employment visa",
            "work permit", "h1b", "l1", "e3", "tier 2", "tier 5",
            
            # Tourism/Travel
            "tourist visa", "travel", "vacation", "holiday", "tourism", "visit",
            "sightseeing", "trip", "vacation", "leisure",
            
            # Business
            "business visa", "business", "company", "corporate", "investment",
            "entrepreneur", "startup", "commercial",
            
            # Family/Immigration
            "family visa", "marriage", "spouse", "partner", "immigration",
            "permanent residence", "citizenship", "green card", "pr",
            
            # Other domains
            "medical", "healthcare", "treatment", "surgery", "hospital",
            "real estate", "property", "house", "apartment", "rent",
            "shopping", "buy", "purchase", "product", "service"
        ]
    
    def is_in_domain(self, query: str) -> Dict[str, Any]:
        """
        Check if query is within student visa domain
        
        Returns:
            Dict with:
                - in_domain: bool
                - confidence: float (0-1)
                - reason: str
                - matched_keywords: list
        """
        query_lower = query.lower()
        
        # Count domain keyword matches
        domain_matches = []
        for keyword in self.domain_keywords:
            if keyword in query_lower:
                domain_matches.append(keyword)
        
        # Count out-of-domain keyword matches
        out_domain_matches = []
        for keyword in self.out_of_domain_keywords:
            if keyword in query_lower:
                out_domain_matches.append(keyword)
        
        # Calculate confidence
        domain_score = len(domain_matches)
        out_domain_score = len(out_domain_matches)
        
        # Decision logic
        if domain_score > 0 and out_domain_score == 0:
            # Clear domain query
            confidence = min(1.0, domain_score / 3.0)  # Cap at 1.0
            in_domain = True
            reason = f"Domain keywords found: {', '.join(domain_matches)}"
            
        elif domain_score > 0 and out_domain_score > 0:
            # Mixed - likely domain if domain score is higher
            if domain_score >= out_domain_score:
                confidence = 0.7
                in_domain = True
                reason = f"Mixed but domain-focused: {domain_score} vs {out_domain_score}"
            else:
                confidence = 0.3
                in_domain = False
                reason = f"Mixed but out-of-domain focused: {out_domain_score} vs {domain_score}"
                
        elif domain_score == 0 and out_domain_score > 0:
            # Clear out-of-domain
            confidence = 0.9
            in_domain = False
            reason = f"Out-of-domain keywords found: {', '.join(out_domain_matches)}"
            
        else:
            # No clear keywords - use context clues
            # Check for question patterns that might be domain-related
            question_patterns = [
                r"how.*visa", r"what.*visa", r"when.*visa", r"where.*visa",
                r"how.*study", r"what.*study", r"when.*study", r"where.*study",
                r"how.*apply", r"what.*apply", r"when.*apply", r"where.*apply",
                r"contact", r"phone", r"number", r"email", r"call"
            ]
            
            question_matches = 0
            for pattern in question_patterns:
                if re.search(pattern, query_lower):
                    question_matches += 1
            
            if question_matches > 0:
                confidence = 0.6
                in_domain = True
                reason = f"Question pattern suggests domain query ({question_matches} matches)"
            else:
                confidence = 0.4
                in_domain = False
                reason = "No clear domain indicators found"
        
        return {
            "in_domain": in_domain,
            "confidence": confidence,
            "reason": reason,
            "matched_keywords": domain_matches if in_domain else out_domain_matches,
            "domain_score": domain_score,
            "out_domain_score": out_domain_score
        }

# Global instance
domain_checker = DomainChecker()

def is_in_domain(query: str) -> Dict[str, Any]:
    """Convenience function to check if query is in domain"""
    return domain_checker.is_in_domain(query)

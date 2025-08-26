#!/usr/bin/env python3
"""
Cleanup Duplicate Leads Script
This script will clean up the existing duplicate leads in your Supabase database.
Run this ONCE to fix the current mess, then the new logic will prevent it from happening again.
"""

import sys
import os
sys.path.append('.')

from app.tools.lead_capture_tool import LeadCaptureTool
from app.config import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_duplicate_leads():
    """Clean up duplicate leads and fix invalid data"""
    try:
        # Initialize lead capture tool
        config = {
            "supabase_url": settings.SUPABASE_URL,
            "supabase_service_role_key": settings.SUPABASE_SERVICE_ROLE_KEY
        }
        lead_tool = LeadCaptureTool(config)
        
        if not lead_tool.supabase:
            logger.error("❌ Cannot connect to Supabase. Check your credentials.")
            return False
        
        logger.info("🔍 Starting cleanup of duplicate leads...")
        
        # Get all leads
        result = lead_tool.search_leads({}, limit=1000)
        
        if not result.get('success'):
            logger.error(f"❌ Failed to get leads: {result.get('error')}")
            return False
        
        leads = result.get('data', [])
        logger.info(f"📊 Found {len(leads)} total leads")
        
        # Group leads by session_id
        session_groups = {}
        for lead in leads:
            session_id = lead.get('session_id', 'unknown')
            if session_id not in session_groups:
                session_groups[session_id] = []
            session_groups[session_id].append(lead)
        
        # Process each session group
        cleaned_count = 0
        for session_id, session_leads in session_groups.items():
            if len(session_leads) > 1:
                logger.info(f"🔍 Session {session_id} has {len(session_leads)} leads - cleaning up...")
                
                # Find the best lead (one with most complete info)
                best_lead = find_best_lead(session_leads)
                
                # Delete all other leads
                for lead in session_leads:
                    if lead['id'] != best_lead['id']:
                        logger.info(f"🗑️ Deleting duplicate lead {lead['id']}")
                        delete_result = lead_tool.delete_lead(lead['id'])
                        if delete_result.get('success'):
                            cleaned_count += 1
                        else:
                            logger.warning(f"⚠️ Failed to delete lead {lead['id']}: {delete_result.get('error')}")
                
                # Clean up the best lead if it has invalid data
                clean_lead_data(best_lead, lead_tool)
                
            elif len(session_leads) == 1:
                # Single lead - just clean up the data
                clean_lead_data(session_leads[0], lead_tool)
        
        logger.info(f"✅ Cleanup completed! Cleaned {cleaned_count} duplicate leads")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        return False

def find_best_lead(leads):
    """Find the lead with the most complete information"""
    best_lead = None
    best_score = -1
    
    for lead in leads:
        score = calculate_lead_score(lead)
        if score > best_score:
            best_score = score
            best_lead = lead
    
    return best_lead

def calculate_lead_score(lead):
    """Calculate how complete a lead is"""
    score = 0
    
    # Email quality
    if lead.get('email') and '@' in lead.get('email') and not lead['email'].startswith('no-email-'):
        score += 10
    
    # Phone quality
    if lead.get('phone') and lead['phone'] != 'EMPTY' and len(str(lead['phone'])) >= 10:
        score += 8
    
    # Name quality
    if lead.get('name') and is_valid_name(lead['name']):
        score += 6
    
    # Country
    if lead.get('target_country') and lead['target_country'] != 'EMPTY':
        score += 4
    
    # Other fields
    if lead.get('intake'):
        score += 2
    if lead.get('study_level'):
        score += 2
    
    return score

def is_valid_name(name):
    """Check if a name is valid"""
    if not name or len(name) < 2:
        return False
    
    # List of common words that are NOT names
    invalid_words = [
        'can', 'you', 'would', 'like', 'which', 'visas', 'need', 'ielts', 'okay', 'whats',
        'information', 'my', 'name', 'are', 'thank', 'the', 'and', 'or', 'but', 'in', 'on',
        'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'down', 'out', 'off', 'over',
        'under', 'above', 'below', 'between', 'among', 'through', 'during', 'before', 'after',
        'while', 'when', 'where', 'why', 'how', 'what', 'who', 'whom', 'whose', 'this', 'that',
        'these', 'those', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall'
    ]
    
    name_lower = name.lower().strip()
    words = name_lower.split()
    valid_words = [word for word in words if word not in invalid_words and len(word) > 1]
    
    return len(valid_words) > 0

def clean_lead_data(lead, lead_tool):
    """Clean up invalid data in a lead"""
    try:
        update_data = {}
        
        # Fix invalid names
        if lead.get('name') and not is_valid_name(lead['name']):
            update_data['name'] = None
            logger.info(f"🧹 Cleaning invalid name '{lead['name']}' from lead {lead['id']}")
        
        # Fix placeholder emails
        if lead.get('email') and lead['email'].startswith('no-email-'):
            update_data['email'] = None
            logger.info(f"🧹 Cleaning placeholder email from lead {lead['id']}")
        
        # Fix empty phone
        if lead.get('phone') == 'EMPTY':
            update_data['phone'] = None
            logger.info(f"🧹 Cleaning empty phone from lead {lead['id']}")
        
        # Fix empty country
        if lead.get('target_country') == 'EMPTY':
            update_data['target_country'] = None
            logger.info(f"🧹 Cleaning empty country from lead {lead['id']}")
        
        # Update if we have changes
        if update_data:
            update_data['updated_at'] = '2025-01-26T00:00:00Z'  # Set a fixed timestamp
            result = lead_tool.update_lead(lead['id'], update_data)
            if result.get('success'):
                logger.info(f"✅ Cleaned lead {lead['id']}: {update_data}")
            else:
                logger.warning(f"⚠️ Failed to clean lead {lead['id']}: {result.get('error')}")
                
    except Exception as e:
        logger.error(f"❌ Error cleaning lead {lead.get('id')}: {e}")

if __name__ == "__main__":
    print("🧹 Starting Duplicate Lead Cleanup...")
    print("=" * 50)
    
    success = cleanup_duplicate_leads()
    
    if success:
        print("\n✅ Cleanup completed successfully!")
        print("🚀 Your database is now clean and ready for the new logic!")
    else:
        print("\n❌ Cleanup failed. Check the logs above.")
    
    print("\n" + "=" * 50)

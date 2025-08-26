"""
Function Handlers for Clean Function-Calling Structure

Handles the execution of focused, deterministic tools:
- get_answer: Serve vetted content only
- qualify_interest: Lightweight lead intent capture
- request_consent: Explicit consent before PII collection
- save_lead: Store contact after consent
- schedule_callback: Optional immediate booking
- notify_human: CRM handoff
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.memory.session_memory import get_session_memory
from app.tools.lead_capture_tool import LeadCaptureTool

logger = logging.getLogger(__name__)

class FunctionHandler:
    """Handles execution of clean, focused tools"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.lead_capture_tool = LeadCaptureTool()
        self.session_memory = get_session_memory()
        
        # Vetted answer map - replace with your actual content
        self.answer_map = {
            "visa_overview": {
                "title": "Student Visa Overview",
                "body": "Student visas allow international students to study in foreign countries. Key requirements include acceptance letter, financial proof, and valid passport. Processing times vary by country.",
                "last_reviewed": "2025-01-01"
            },
            "usa_visa": {
                "title": "USA Student Visa (F-1)",
                "body": "F-1 visa requires: SEVIS fee payment, Form DS-160, financial documents showing $25,000+ annually, acceptance letter, and proof of ties to home country.",
                "last_reviewed": "2025-01-01"
            },
            "uk_visa": {
                "title": "UK Student Visa (Tier 4)",
                "body": "Tier 4 visa requires: CAS letter, financial evidence (£1,334/month for London, £1,023/month outside), English proficiency (IELTS 6.0+), and accommodation details.",
                "last_reviewed": "2025-01-01"
            },
            "australia_visa": {
                "title": "Australia Student Visa (Subclass 500)",
                "body": "Subclass 500 requires: CoE (Confirmation of Enrolment), financial capacity proof, English proficiency, health insurance (OSHC), and genuine temporary entrant statement.",
                "last_reviewed": "2025-01-01"
            },
            "south_korea_visa": {
                "title": "South Korea Student Visa (D-2)",
                "body": "D-2 visa requires: acceptance certificate, financial guarantee (minimum $10,000), health certificate, and proof of Korean language proficiency (TOPIK level 3+).",
                "last_reviewed": "2025-01-01"
            },
            "required_documents": {
                "title": "Required Documents",
                "body": "Standard documents: passport, photos, application form, acceptance letter, financial statements, academic transcripts, English test scores, and health insurance.",
                "last_reviewed": "2025-01-01"
            },
            "financial_proof_basics": {
                "title": "Financial Proof Requirements",
                "body": "Show sufficient funds for tuition + living expenses. Bank statements for 3-6 months, scholarship letters, or sponsor affidavits. Amount varies by country and city.",
                "last_reviewed": "2025-01-01"
            },
            "consultancy_services": {
                "title": "AI Consultancy Services",
                "body": "We provide end-to-end visa assistance: document preparation, application submission, interview coaching, and post-approval support. Our success rate is 95%+.",
                "last_reviewed": "2025-01-01"
            },
            "fees_and_packages": {
                "title": "Fees and Packages",
                "body": "Basic package: $500 (document review + application). Premium package: $1,200 (full service + interview prep). Payment plans available. No hidden fees.",
                "last_reviewed": "2025-01-01"
            },
            "office_locations": {
                "title": "Office Locations",
                "body": "Main office: Kathmandu, Nepal. Branch offices: Pokhara, Chitwan. Virtual consultations available worldwide. Office hours: 9 AM - 6 PM (NPT).",
                "last_reviewed": "2025-01-01"
            },
            "contact_options": {
                "title": "Contact Options",
                "body": "Phone: +977-1-4444444, WhatsApp: +977-9800000000, Email: info@aiconsultancy.com. Emergency line: +977-1-5555555. Response within 2 hours.",
                "last_reviewed": "2025-01-01"
            }
        }
    
    def get_answer(self, session_id: str, **kwargs) -> Dict[str, Any]:
        """Return vetted answer snippet about student visas or consultancy"""
        try:
            topic = kwargs.get('topic', '')
            locale = kwargs.get('locale', 'en-US')
            
            if topic not in self.answer_map:
                return {
                    "success": False,
                    "message": f"No vetted answer available for topic: {topic}",
                    "data": {
                        "suggestion": "An advisor can help with this specific question. Would you like a callback?",
                        "available_topics": list(self.answer_map.keys())
                    }
                }
            
            answer = self.answer_map[topic]
            
            return {
                "success": True,
                "message": "Vetted answer retrieved successfully",
                "data": {
                    "topic": topic,
                    "locale": locale,
                    "title": answer["title"],
                    "body": answer["body"],
                    "last_reviewed": answer["last_reviewed"],
                    "cta": "If you'd like personalized guidance, I can have an advisor reach out to you."
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in get_answer: {e}")
            return {
                "success": False,
                "message": f"Error retrieving answer: {str(e)}",
                "data": None
            }
    
    def qualify_interest(self, session_id: str, **kwargs) -> Dict[str, Any]:
        """Capture non-PII interest to personalize follow-ups"""
        try:
            study_country = kwargs.get('study_country', '')
            study_level = kwargs.get('study_level', '')
            target_intake = kwargs.get('target_intake', '')
            notes = kwargs.get('notes', '')
            
            # Store in session memory for later use
            session_info = self.session_memory.get_user_info(session_id)
            if session_info:
                session_info.study_country = study_country
                session_info.study_level = study_level
                session_info.target_intake = target_intake
                session_info.notes = notes
            
            return {
                "success": True,
                "message": "Interest qualified successfully",
                "data": {
                    "study_country": study_country,
                    "study_level": study_level,
                    "target_intake": target_intake,
                    "notes": notes,
                    "next_step": "Would you like to share your contact information so an advisor can guide you personally?"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in qualify_interest: {e}")
            return {
                "success": False,
                "message": f"Error qualifying interest: {str(e)}",
                "data": None
            }
    
    def request_consent(self, session_id: str, **kwargs) -> Dict[str, Any]:
        """Record explicit user consent to store and contact them"""
        try:
            consent_text_version = kwargs.get('consent_text_version', 'v1.0')
            consent = kwargs.get('consent', False)
            
            # Store consent in session memory
            session_info = self.session_memory.get_user_info(session_id)
            if session_info:
                session_info.consent_given = consent
                session_info.consent_version = consent_text_version
                session_info.consent_timestamp = datetime.now().isoformat()
            
            if consent:
                return {
                    "success": True,
                    "message": "Consent recorded successfully",
                    "data": {
                        "consent": True,
                        "consent_text_version": consent_text_version,
                        "consent_timestamp": datetime.now().isoformat(),
                        "next_step": "Great! Now I can help you save your contact information. What's your full name?"
                    }
                }
            else:
                return {
                    "success": True,
                    "message": "Consent declined - continuing without contact storage",
                    "data": {
                        "consent": False,
                        "consent_text_version": consent_text_version,
                        "consent_timestamp": datetime.now().isoformat(),
                        "message": "No problem! I'll continue answering your questions without storing contact details."
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Error in request_consent: {e}")
            return {
                "success": False,
                "message": f"Error recording consent: {str(e)}",
                "data": None
            }
    
    def save_lead(self, session_id: str, **kwargs) -> Dict[str, Any]:
        """Save lead with contact details after explicit consent"""
        try:
            # Check if consent was given
            session_info = self.session_memory.get_user_info(session_id)
            if not session_info or not getattr(session_info, 'consent_given', False):
                return {
                    "success": False,
                    "message": "Consent required before saving contact information",
                    "data": {
                        "error": "Please provide consent first using request_consent function"
                    }
                }
            
            full_name = kwargs.get('full_name', '')
            email = kwargs.get('email', '')
            phone_e164 = kwargs.get('phone_e164', '')
            preferred_channel = kwargs.get('preferred_channel', 'phone')
            study_country = kwargs.get('study_country', '') or getattr(session_info, 'study_country', '')
            study_level = kwargs.get('study_level', '') or getattr(session_info, 'study_level', '')
            target_intake = kwargs.get('target_intake', '') or getattr(session_info, 'target_intake', '')
            notes = kwargs.get('notes', '') or getattr(session_info, 'notes', '')
            consent_text_version = kwargs.get('consent_text_version', '') or getattr(session_info, 'consent_version', 'v1.0')
            consent_timestamp = kwargs.get('consent_timestamp', '') or getattr(session_info, 'consent_timestamp', datetime.now().isoformat())
            
            # Validate required fields
            if not full_name:
                return {
                    "success": False,
                    "message": "Full name is required",
                    "data": {
                        "error": "Please provide your full name"
                    }
                }
            
            # Save to database
            lead_data = {
                "session_id": session_id,
                "name": full_name,
                "email": email or '',
                "phone": phone_e164 or '',
                "target_country": study_country or '',
                "intake": target_intake or '',
                "status": "new_lead",
                "consent_version": consent_text_version,
                "consent_timestamp": consent_timestamp
            }
            
            lead_result = self.lead_capture_tool.create_lead(lead_data)
            
            if lead_result.get('success'):
                lead_id = lead_result.get('lead_id', f"lead_{session_id}")
                
                return {
                    "success": True,
                    "message": "Lead saved successfully",
                    "data": {
                        "lead_id": lead_id,
                        "full_name": full_name,
                        "contact_saved": True,
                        "next_step": "Perfect! Your information is saved. Would you like me to schedule a callback with one of our advisors?"
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to save lead: {lead_result.get('error')}",
                    "data": None
                }
                
        except Exception as e:
            self.logger.error(f"Error in save_lead: {e}")
            return {
                "success": False,
                "message": f"Error saving lead: {str(e)}",
                "data": None
            }
    
    def schedule_callback(self, session_id: str, **kwargs) -> Dict[str, Any]:
        """Create a callback task for a human advisor"""
        try:
            when_local = kwargs.get('when_local', '')
            timezone = kwargs.get('timezone', 'Asia/Kathmandu')
            channel = kwargs.get('channel', 'phone')
            priority = kwargs.get('priority', 'normal')
            
            # For now, just log the callback request
            # In production, integrate with your scheduling system
            callback_data = {
                "session_id": session_id,
                "when_local": when_local,
                "timezone": timezone,
                "channel": channel,
                "priority": priority,
                "status": "scheduled"
            }
            
            self.logger.info(f"Callback scheduled: {callback_data}")
            
            return {
                "success": True,
                "message": "Callback scheduled successfully",
                "data": {
                    "callback_id": f"cb_{session_id}_{int(datetime.now().timestamp())}",
                    "when_local": when_local,
                    "timezone": timezone,
                    "channel": channel,
                    "priority": priority,
                    "message": f"Callback scheduled for {channel}. An advisor will contact you soon!"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in schedule_callback: {e}")
            return {
                "success": False,
                "message": f"Error scheduling callback: {str(e)}",
                "data": None
            }
    
    def notify_human(self, session_id: str, **kwargs) -> Dict[str, Any]:
        """Ping advisors with a concise summary"""
        try:
            lead_id = kwargs.get('lead_id', '')
            summary = kwargs.get('summary', '')
            priority = kwargs.get('priority', 'normal')
            
            # For now, just log the notification
            # In production, integrate with Slack/email/Zapier
            notification_data = {
                "session_id": session_id,
                "lead_id": lead_id,
                "summary": summary,
                "priority": priority,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Human notification: {notification_data}")
            
            return {
                "success": True,
                "message": "Human advisor notified successfully",
                "data": {
                    "notification_id": f"notif_{session_id}_{int(datetime.now().timestamp())}",
                    "summary": summary,
                    "priority": priority,
                    "message": "Advisor has been notified and will follow up soon."
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in notify_human: {e}")
            return {
                "success": False,
                "message": f"Error notifying human: {str(e)}",
                "data": None
            }
    
    def execute_function(self, function_name: str, session_id: str, **kwargs) -> Dict[str, Any]:
        """Execute a function by name"""
        self.logger.info(f"Executing function {function_name} for session {session_id}")
        
        if function_name == "get_answer":
            return self.get_answer(session_id, **kwargs)
        elif function_name == "qualify_interest":
            return self.qualify_interest(session_id, **kwargs)
        elif function_name == "request_consent":
            return self.request_consent(session_id, **kwargs)
        elif function_name == "save_lead":
            return self.save_lead(session_id, **kwargs)
        elif function_name == "schedule_callback":
            return self.schedule_callback(session_id, **kwargs)
        elif function_name == "notify_human":
            return self.notify_human(session_id, **kwargs)
        else:
            return {
                "success": False,
                "message": f"Unknown function: {function_name}",
                "data": None
            }

# Global function handler instance
function_handler = FunctionHandler()

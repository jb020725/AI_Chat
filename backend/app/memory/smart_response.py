"""
Smart Response System for AI Consultancy Chatbot

Features:
- Answer visa questions directly
- Detect user interest and capture leads
- Save leads to Supabase database
- Send email notifications
- Use session memory for personalization
- No RAG - just direct LLM responses
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.memory.session_memory import get_session_memory
from app.tools.lead_capture_tool import LeadCaptureTool

logger = logging.getLogger(__name__)

class SmartResponse:
    """AI Consultancy chatbot with lead capture and database saving"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session_memory = get_session_memory()
        self.llm_model = None
        
        # Initialize lead capture tool with proper configuration
        from app.config import settings
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
        self.lead_capture_tool = LeadCaptureTool(config)
        
    def set_llm_model(self, llm_model):
        """Set the LLM model for responses"""
        try:
            self.llm_model = llm_model
            logger.info(f"LLM model set for AI Consultancy chatbot: {type(llm_model)}")
        except Exception as e:
            logger.error(f"Failed to set LLM model: {e}")
            self.llm_model = None
    
    def generate_smart_response(self, user_message: str, session_id: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Generate response and handle lead capture"""
        try:
            if not self.llm_model:
                return {
                    "response": "Hello! I'm your professional student visa consultant. I can help you with visa applications for USA, UK, Australia, and South Korea. What country are you interested in studying in?",
                    "success": True,
                    "function_calls": []
                }
            
            # First, check if we need to save a lead
            lead_saved = self._detect_and_save_lead(user_message, session_id)
            
            # Create response prompt
            prompt = self._create_response_prompt(user_message, session_id, conversation_history, lead_saved)
            
            # Get response from LLM
            try:
                response = self.llm_model.generate_content(prompt)
                if response and hasattr(response, 'text'):
                    ai_response = response.text
                else:
                    ai_response = "I understand your question. Let me help you with that."
                
                return {
                    "response": ai_response,
                    "success": True,
                    "function_calls": []
                }
                
            except Exception as e:
                logger.error(f"Error calling LLM: {e}")
                return {
                    "response": "I'm experiencing technical difficulties. Please try again or ask a different question.",
                    "success": False,
                    "error": str(e)
                }
                
        except Exception as e:
            logger.error(f"Error in generate_smart_response: {e}")
            return {
                "response": "I encountered an error. Please try again.",
                "success": False,
                "error": str(e)
            }
    
    def _detect_and_save_lead(self, user_message: str, session_id: str) -> bool:
        """Detect if user provided contact info and save lead"""
        try:
            logger.info(f"🔍 Lead detection started for message: '{user_message[:100]}...'")
            
            # Extract contact information from message
            contact_info = self._extract_contact_info(user_message)
            
            logger.info(f"🔍 Contact info extracted: {contact_info}")
            
            if not contact_info:
                logger.info("🔍 No contact info found, skipping lead creation")
                return False
            
            # Get session info for additional details
            session_info = self.session_memory.get_user_info(session_id)
            logger.info(f"🔍 Session info: {session_info}")
            
            # Prepare lead data
            lead_data = {
                "session_id": session_id,
                "name": contact_info.get('name', ''),
                "phone": contact_info.get('phone', ''),
                "email": contact_info.get('email', ''),
                "target_country": contact_info.get('country', ''),
                "intake": getattr(session_info, 'intake', '') if session_info else '',
                "study_level": getattr(session_info, 'study_level', '') if session_info else '',
                "status": "new_lead",
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"🔍 Lead data prepared: {lead_data}")
            
            # Save to database
            logger.info("🔍 Attempting to save lead to database...")
            result = self.lead_capture_tool.create_lead(lead_data)
            
            logger.info(f"🔍 Lead creation result: {result}")
            
            if result.get('success'):
                logger.info(f"✅ Lead saved successfully: {lead_data}")
                return True
            else:
                logger.error(f"❌ Failed to save lead: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error in lead detection and saving: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False
    
    def _extract_contact_info(self, message: str) -> Dict[str, str]:
        """Extract contact information from user message"""
        contact_info = {}
        message_lower = message.lower()
        
        # Extract email - More flexible pattern
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, message)
        if email_match:
            contact_info['email'] = email_match.group()
            logger.info(f"Extracted email: {contact_info['email']}")
        
        # Extract phone number - More flexible pattern
        phone_patterns = [
            r'\b\d{10,15}\b',  # Basic 10-15 digits
            r'\+?\d[\d\s().-]{6,}\d',  # International format
            r'\(\d{3}\)\s*\d{3}-\d{4}',  # US format (123) 456-7890
        ]
        
        for pattern in phone_patterns:
            phone_match = re.search(pattern, message)
            if phone_match:
                # Clean the phone number
                phone = re.sub(r'[^\d+]', '', phone_match.group())
                if len(phone) >= 10:  # Must be at least 10 digits
                    contact_info['phone'] = phone
                    logger.info(f"Extracted phone: {contact_info['phone']}")
                    break
        
        # Extract name - More flexible patterns
        name_patterns = [
            r'\bmy name is\s+([A-Za-z\s]+?)(?:\s*[,.]|$)',
            r'\bi\'m\s+([A-Za-z\s]+?)(?:\s*[,.]|$)',
            r'\bi am\s+([A-Za-z\s]+?)(?:\s*[,.]|$)',
            r'\bname\s*:\s*([A-Za-z\s]+?)(?:\s*[,.]|$)',
            r'\bcall me\s+([A-Za-z\s]+?)(?:\s*[,.]|$)',
            r'\bthis is\s+([A-Za-z\s]+?)(?:\s*[,.]|$)',
            r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)',  # First Last format
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, message_lower, re.IGNORECASE)
            if name_match:
                if len(name_match.groups()) == 1:
                    name = name_match.group(1).strip()
                else:
                    # Handle First Last format
                    name = ' '.join(name_match.groups()).strip()
                
                if name and len(name) > 1 and name.lower() not in ['user', 'test', 'example', 'sample', 'john', 'jane']:
                    contact_info['name'] = name.title()
                    logger.info(f"Extracted name: {contact_info['name']}")
                    break
        
        # Extract country - More flexible patterns
        country_patterns = {
            'usa': ['usa', 'united states', 'america', 'us', 'u.s.', 'u.s.a', 'states', 'united states of america'],
            'uk': ['uk', 'united kingdom', 'britain', 'england', 'great britain', 'british'],
            'australia': ['australia', 'aussie', 'australian'],
            'south_korea': ['south korea', 'korea', 'korean', 'seoul', 'republic of korea']
        }
        
        for country, patterns in country_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    contact_info['country'] = country
                    logger.info(f"Extracted country: {contact_info['country']}")
                    break
            if 'country' in contact_info:
                break
        
        # Log what we found
        if contact_info:
            logger.info(f"Contact info extracted: {contact_info}")
        else:
            logger.info("No contact info found in message")
        
        # Only return if we have at least some contact info
        if contact_info.get('email') or contact_info.get('phone') or contact_info.get('name'):
            return contact_info
        
        return {}
    
    def _create_response_prompt(self, user_message: str, session_id: str, conversation_history: List[Dict], lead_saved: bool) -> str:
        """Create response prompt for the chatbot"""
        
        # Get session context
        session_info = self.session_memory.get_user_info(session_id)
        session_context = ""
        if session_info:
            session_context = f"""
SESSION CONTEXT:
- Has contact info: {bool(session_info.email or session_info.phone)}
- Study country: {getattr(session_info, 'study_country', 'Not specified')}
- Study level: {getattr(session_info, 'study_level', 'Not specified')}
- Intake: {getattr(session_info, 'intake', 'Not specified')}
- Session ID: {session_id}
"""
        
        # Build conversation context - Last 5 exchanges instead of 3
        conversation_context = ""
        if conversation_history:
            recent_messages = conversation_history[-5:]  # Last 5 messages
            conversation_context = "\nRECENT CONVERSATION (Last 5 exchanges):\n"
            for i, msg in enumerate(recent_messages, 1):
                role = msg.get('role', 'user')
                content = msg.get('content', msg.get('user_message', msg.get('user_input', '')))
                conversation_context += f"{i}. {role.title()}: {content}\n"
        
        # Get lead table data for this session
        lead_table_data = ""
        try:
            if session_info and (session_info.email or session_info.phone):
                # Get leads for this session/user
                leads = self.lead_capture_tool.get_leads_by_session(session_id)
                if leads and leads.get('success') and leads.get('data'):
                    lead_table_data = "\nLEAD TABLE DATA (Current Session):\n"
                    lead_table_data += "=" * 50 + "\n"
                    for lead in leads['data']:
                        lead_table_data += f"""
Lead ID: {lead.get('id', 'N/A')}
- Email: {lead.get('email', 'N/A')}
- Name: {lead.get('name', 'N/A')}
- Phone: {lead.get('phone', 'N/A')}
- Target Country: {lead.get('target_country', 'N/A')}
- Intake: {lead.get('intake', 'N/A')}
- Status: {lead.get('status', 'N/A')}
- Created: {lead.get('created_at', 'N/A')}
- Session ID: {lead.get('session_id', 'N/A')}
{'-' * 30}
"""
                else:
                    lead_table_data = "\nLEAD TABLE DATA: No leads found for current session\n"
            else:
                lead_table_data = "\nLEAD TABLE DATA: User not yet identified (no email/phone)\n"
        except Exception as e:
            logger.error(f"Error getting lead table data: {e}")
            lead_table_data = "\nLEAD TABLE DATA: Error retrieving data\n"
        
        # Add lead status to prompt
        lead_status = ""
        if lead_saved:
            lead_status = "\nLEAD STATUS: Contact information has been saved and an advisor will contact you soon."
        
        # Import and use the new prompt orchestrator
        from app.prompts import get_prompt_orchestrator
        
        prompt_orchestrator = get_prompt_orchestrator()
        
        # Get user info for prompt
        user_info = {}
        if session_info:
            user_info = {
                'country': getattr(session_info, 'study_country', ''),
                'email': getattr(session_info, 'email', ''),
                'name': getattr(session_info, 'name', ''),
                'intake': getattr(session_info, 'intake', ''),
                'phone': getattr(session_info, 'phone', '')
            }
        
        # Create comprehensive prompt using the orchestrator
        prompt = prompt_orchestrator.create_comprehensive_prompt(
            user_question=user_message,
            user_info=user_info,
            conversation_history=conversation_history
        )
        
        # Add enhanced context sections
        enhanced_context = f"""
{conversation_context}

{session_context}

{lead_table_data}

{lead_status}
"""
        
        # Combine with the main prompt
        final_prompt = prompt + enhanced_context
        
        return final_prompt
    
    def update_session_memory(self, session_id: str, data: Dict[str, Any]):
        """Update session memory with new information"""
        try:
            self.session_memory.update_session(session_id, data)
            logger.info(f"Session memory updated for session {session_id}")
        except Exception as e:
            logger.error(f"Error updating session memory: {e}")
    
    def get_session_info(self, session_id: str) -> Optional[Any]:
        """Get current session information"""
        try:
            return self.session_memory.get_user_info(session_id)
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return None

# Global instance
smart_response = SmartResponse()
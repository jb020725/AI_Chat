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
        self.lead_capture_tool = LeadCaptureTool()
        
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
            # Extract contact information from message
            contact_info = self._extract_contact_info(user_message)
            
            if not contact_info:
                return False
            
            # Get session info for additional details
            session_info = self.session_memory.get_user_info(session_id)
            
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
            
            # Save to database
            result = self.lead_capture_tool.create_lead(lead_data)
            
            if result.get('success'):
                logger.info(f"Lead saved successfully: {lead_data}")
                # TODO: Send email notification here
                return True
            else:
                logger.error(f"Failed to save lead: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error in lead detection and saving: {e}")
            return False
    
    def _extract_contact_info(self, message: str) -> Dict[str, str]:
        """Extract contact information from user message"""
        contact_info = {}
        message_lower = message.lower()
        
        # Extract email
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, message)
        if email_match:
            contact_info['email'] = email_match.group()
        
        # Extract phone number
        phone_pattern = r'\b\d{10,15}\b'
        phone_match = re.search(phone_pattern, message)
        if phone_match:
            contact_info['phone'] = phone_match.group()
        
        # Extract name
        name_patterns = [
            r'\bmy name is\s+([A-Za-z\s]+?)(?:\s*[,.]|$)',
            r'\bi\'m\s+([A-Za-z\s]+?)(?:\s*[,.]|$)',
            r'\bi am\s+([A-Za-z\s]+?)(?:\s*[,.]|$)',
            r'\bname\s*:\s*([A-Za-z\s]+?)(?:\s*[,.]|$)',
            r'\bcall me\s+([A-Za-z\s]+?)(?:\s*[,.]|$)'
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, message_lower, re.IGNORECASE)
            if name_match:
                name = name_match.group(1).strip()
                if name and len(name) > 1 and name not in ['user', 'test', 'example', 'sample']:
                    contact_info['name'] = name.title()
                    break
        
        # Extract country
        country_patterns = {
            'usa': ['usa', 'united states', 'america', 'us', 'u.s.', 'u.s.a'],
            'uk': ['uk', 'united kingdom', 'britain', 'england', 'great britain'],
            'australia': ['australia', 'aussie'],
            'south_korea': ['south korea', 'korea', 'korean', 'seoul']
        }
        
        for country, patterns in country_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    contact_info['country'] = country
                    break
            if 'country' in contact_info:
                break
        
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
"""
        
        # Build conversation context
        conversation_context = ""
        if conversation_history:
            recent_messages = conversation_history[-3:]  # Last 3 messages
            conversation_context = "\nRECENT CONVERSATION:\n"
            for msg in recent_messages:
                role = msg.get('role', 'user')
                content = msg.get('content', msg.get('user_message', msg.get('user_input', '')))
                conversation_context += f"- {role.title()}: {content}\n"
        
        # Add lead status to prompt
        lead_status = ""
        if lead_saved:
            lead_status = "\nLEAD STATUS: Contact information has been saved and an advisor will contact you soon."
        
        prompt = f"""You are a professional student visa consultant representing AI Consultancy, specializing in helping Nepali students apply to USA, UK, Australia, and South Korea.

{session_context}

{conversation_context}

{lead_status}

Current user message: "{user_message}"

RESPONSE STRATEGY:
1. If user asks general visa questions → Provide helpful, accurate information about student visas
2. If user shows interest in applying ("I want to apply", "interested in UK", "thinking about Australia") → Politely ask for contact details explaining that physical application is required
3. If user provides contact info → Acknowledge and confirm you'll have an advisor contact them
4. Continue answering questions normally after lead capture

VISA KNOWLEDGE:
- USA: F-1 visa, SEVIS fee, Form DS-160, financial proof ($25,000+ annually)
- UK: Tier 4 visa, CAS letter, financial evidence (£1,334/month London, £1,023/month outside)
- Australia: Subclass 500, CoE, financial capacity, OSHC insurance
- South Korea: D-2 visa, acceptance certificate, financial guarantee ($10,000+), TOPIK level 3+

BEHAVIOR:
- Be professional, helpful, and informative
- Don't repeat information unnecessarily (use session context)
- When asking for contact, explain that physical office visit is required for application
- Stay concise and actionable
- Always maintain a helpful, professional tone

Remember: You are a visa consultant helping students. Be informative, professional, and guide them toward the next step when they show interest."""
        
        return prompt
    
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
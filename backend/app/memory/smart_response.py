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
            
            # Extract contact info for session memory update
            contact_info = self._extract_contact_info(user_message)
            
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
                    "function_calls": [],
                    "user_info_extracted": contact_info  # Return extracted info for session memory
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
        """Detect if user provided contact info and save/update lead - ONE PER CONVERSATION"""
        try:
            logger.info(f"🔍 Lead detection started for message: '{user_message[:100]}...'")
            
            # Extract contact information from message
            contact_info = self._extract_contact_info(user_message)
            
            logger.info(f"🔍 Contact info extracted: {contact_info}")
            
            # Proceed if we have ANY useful information (email, phone, study level, program, country)
            has_contact = contact_info.get('email') or contact_info.get('phone')
            has_academic_info = contact_info.get('study_level') or contact_info.get('program') or contact_info.get('country')
            
            if not has_contact and not has_academic_info:
                logger.info("🔍 No useful information (contact OR academic) found, skipping lead creation")
                return False
            
            logger.info(f"🔍 Proceeding with lead creation - Contact: {has_contact}, Academic: {has_academic_info}")
            
            # Get session info for additional details
            session_info = self.session_memory.get_user_info(session_id)
            logger.info(f"🔍 Session info: {session_info}")
            
            # Check if lead already exists for this session
            existing_lead = self._get_existing_lead(session_id)
            
            if existing_lead:
                logger.info(f"🔍 Updating existing lead for session {session_id}")
                # Update existing lead with new information
                return self._update_existing_lead(existing_lead, contact_info, session_info)
            else:
                logger.info(f"🔍 Creating new lead for session {session_id}")
                # Create new lead
                return self._create_new_lead(contact_info, session_info, session_id)
                
        except Exception as e:
            logger.error(f"❌ Error in lead detection and saving: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False
    
    def _get_existing_lead(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Check if a lead already exists for this session"""
        try:
            result = self.lead_capture_tool.get_leads_by_session(session_id)
            if result.get('success') and result.get('data'):
                # Return the first (and should be only) lead for this session
                return result['data'][0]
            return None
        except Exception as e:
            logger.error(f"Error checking existing lead: {e}")
            return None
    
    def _update_existing_lead(self, existing_lead: Dict[str, Any], contact_info: Dict[str, str], session_info: Any) -> bool:
        """Update existing lead with new information"""
        try:
            # Prepare update data - only update if we have better information
            update_data = {}
            
            # Only update name if we have a better one (not random words)
            if contact_info.get('name') and self._is_valid_name(contact_info['name']):
                if not existing_lead.get('name') or self._is_better_name(contact_info['name'], existing_lead['name']):
                    update_data['name'] = contact_info['name']
            
            # Update email if we have a real one
            if contact_info.get('email') and '@' in contact_info['email']:
                if not existing_lead.get('email') or existing_lead['email'].startswith('no-email-'):
                    update_data['email'] = contact_info['email']
            
            # Update phone if we have a real one
            if contact_info.get('phone') and len(contact_info['phone']) >= 10:
                if not existing_lead.get('phone') or existing_lead['phone'] == 'EMPTY':
                    update_data['phone'] = contact_info['phone']
            
            # Update country if we have one
            if contact_info.get('country'):
                if not existing_lead.get('target_country') or existing_lead['target_country'] == 'EMPTY':
                    update_data['target_country'] = contact_info['country']
            
            # Update other fields from contact info or session info
            if contact_info.get('intake'):
                if not existing_lead.get('intake') or existing_lead['intake'] == '':
                    update_data['intake'] = contact_info['intake']
            elif session_info and not existing_lead.get('intake') and getattr(session_info, 'intake', ''):
                update_data['intake'] = session_info.intake
                
            if contact_info.get('study_level'):
                if not existing_lead.get('study_level') or existing_lead['study_level'] == '':
                    update_data['study_level'] = contact_info['study_level']
            elif session_info and not existing_lead.get('study_level') and getattr(session_info, 'study_level', ''):
                update_data['study_level'] = session_info.study_level
                
            if contact_info.get('program'):
                if not existing_lead.get('program') or existing_lead['program'] == '':
                    update_data['program'] = contact_info['program']
            elif session_info and not existing_lead.get('program') and getattr(session_info, 'program', ''):
                update_data['program'] = session_info.program
            
            if not update_data:
                logger.info("🔍 No new information to update in existing lead")
                return True  # Success - no update needed
            
            # Add timestamp
            update_data['updated_at'] = datetime.now().isoformat()
            
            logger.info(f"🔍 Updating lead with: {update_data}")
            
            # Update the lead
            result = self.lead_capture_tool.update_lead(existing_lead['id'], update_data)
            
            if result.get('success'):
                logger.info(f"✅ Lead updated successfully: {update_data}")
                return True
            else:
                logger.error(f"❌ Failed to update lead: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating lead: {e}")
            return False
    
    def _create_new_lead(self, contact_info: Dict[str, str], session_info: Any, session_id: str) -> bool:
        """Create a new lead - only when we have real contact info"""
        try:
            # Prepare lead data - PRIORITIZE extracted contact info over session info
            lead_data = {
                "session_id": session_id,
                "name": contact_info.get('name', ''),
                "phone": contact_info.get('phone', ''),
                "email": contact_info.get('email', ''),
                "target_country": contact_info.get('country', ''),  # This should work now
                "intake": contact_info.get('intake', ''),  # This should work now
                "study_level": contact_info.get('study_level', ''),  # This should work now
                "program": contact_info.get('program', ''),  # This should work now
                "status": "new_lead",
                "created_at": datetime.now().isoformat()
            }
            
            # Log what we're actually creating
            logger.info(f"🔍 LEAD DATA TO BE CREATED: {lead_data}")
            logger.info(f"🔍 CONTACT INFO EXTRACTED: {contact_info}")
            
            logger.info(f"🔍 Creating new lead: {lead_data}")
            
            # Save to database
            result = self.lead_capture_tool.create_lead(lead_data)
            
            if result.get('success'):
                logger.info(f"✅ New lead created successfully: {lead_data}")
                
                # FORCE EMAIL NOTIFICATION - This should work now!
                try:
                    logger.info("📧 Attempting to send email notification...")
                    # The email should be sent automatically by LeadCaptureTool
                    # Let's verify the lead was created with all fields
                    created_lead = result.get('data', {})
                    logger.info(f"📧 Lead created with data: {created_lead}")
                    logger.info(f"📧 Email should be sent to: {self.lead_capture_tool.config.get('lead_notification_email', 'NOT SET')}")
                except Exception as e:
                    logger.error(f"❌ Error in email notification: {e}")
                
                return True
            else:
                logger.error(f"❌ Failed to create new lead: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error creating new lead: {e}")
            return False
    
    def _is_valid_name(self, name: str) -> bool:
        """Check if a name is valid (not random words)"""
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
        
        # Check if name contains only invalid words
        words = name_lower.split()
        valid_words = [word for word in words if word not in invalid_words and len(word) > 1]
        
        # Name is valid if it has at least one valid word
        return len(valid_words) > 0
    
    def _is_better_name(self, new_name: str, existing_name: str) -> bool:
        """Check if new name is better than existing name"""
        if not existing_name:
            return True
        
        # Prefer longer names (more complete)
        if len(new_name) > len(existing_name):
            return True
        
        # Prefer names that don't start with common question words
        question_words = ['can', 'would', 'which', 'what', 'how', 'when', 'where', 'why']
        if new_name.lower().split()[0] not in question_words and existing_name.lower().split()[0] in question_words:
            return True
        
        return False
    
    def _extract_contact_info(self, message: str) -> Dict[str, str]:
        """Extract contact information from user message - Enhanced extraction with country/level detection - FIXED PATTERNS AND DEBUG LOGGING - FORCE DEPLOYMENT"""
        try:
            print(f"🚀🚀🚀 EXTRACTION FUNCTION CALLED with message: '{message[:100]}...' 🚀🚀🚀")
            logger.info(f"🚀 EXTRACTION FUNCTION CALLED with message: '{message[:100]}...'")
            contact_info = {}
            message_lower = message.lower()
            
            print(f"🔍🔍🔍 MESSAGE TO PROCESS: '{message_lower}' 🔍🔍🔍")
            
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
            
            # Extract name - ONLY when explicitly stated, not random words
            name_patterns = [
                r'\bmy name is\s+([A-Za-z\s]+?)(?:\s*[,.]|$)',  # "My name is John Smith"
                r'\bi\'m\s+([A-Za-z\s]+?)(?:\s*[,.]|$)',         # "I'm John Smith"
                r'\bi am\s+([A-Za-z\s]+?)(?:\s*[,.]|$)',         # "I am John Smith"
                r'\bname\s*:\s*([A-Za-z\s]+?)(?:\s*[,.]|$)',     # "Name: John Smith"
                r'\bcall me\s+([A-Za-z\s]+?)(?:\s*[,.]|$)',      # "Call me John"
                r'\bthis is\s+([A-Za-z\s]+?)(?:\s*[,.]|$)',      # "This is John"
                r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)',              # "John Smith" (First Last format)
            ]
            
            for pattern in name_patterns:
                name_match = re.search(pattern, message_lower, re.IGNORECASE)
                if name_match:
                    if len(name_match.groups()) == 1:
                        name = name_match.group(1).strip()
                    else:
                        # Handle First Last format
                        name = ' '.join(name_match.groups()).strip()
                    
                    # Validate the extracted name
                    if self._is_valid_name(name):
                        contact_info['name'] = name.title()
                        logger.info(f"Extracted valid name: {contact_info['name']}")
                        break
                    else:
                        logger.info(f"Extracted name '{name}' but it's not valid (likely random words)")
            
            # Extract country - More flexible patterns
            country_patterns = {
                'usa': ['usa', 'united states', 'america', 'us', 'u.s.', 'u.s.a', 'states', 'united states of america'],
                'uk': ['uk', 'united kingdom', 'britain', 'england', 'great britain', 'british'],
                'australia': ['australia', 'aussie', 'australian'],
                'south_korea': ['south korea', 'korea', 'korean', 'seoul', 'republic of korea']
            }
            
            logger.info(f"🔍 DEBUG: Checking country patterns in message: '{message_lower}'")
            for country, patterns in country_patterns.items():
                for pattern in patterns:
                    if pattern in message_lower:
                        contact_info['country'] = country
                        logger.info(f"✅ MATCHED country '{country}' with pattern '{pattern}'")
                        break
                if 'country' in contact_info:
                    break
            
            # Extract study level - More flexible patterns
            study_level_patterns = {
                'bachelor': ['bachelor', 'bachelors', 'undergraduate', 'bachelor\'s', 'bachelors degree', 'bachelor degree', 'bachelor\'s degree'],
                'master': ['master', 'masters', 'graduate', 'master\'s', 'masters degree', 'master degree', 'ms', 'ma', 'mba'],
                'phd': ['phd', 'doctorate', 'doctoral', 'doctor of philosophy', 'ph.d', 'ph.d.'],
                'diploma': ['diploma', 'certificate', 'certification']
            }
            
            logger.info(f"🔍 DEBUG: Checking study level patterns in message: '{message_lower}'")
            print(f"🔍🔍🔍 CHECKING STUDY LEVEL PATTERNS: '{message_lower}' 🔍🔍🔍")
            for level, patterns in study_level_patterns.items():
                for pattern in patterns:
                    if pattern in message_lower:
                        contact_info['study_level'] = level
                        print(f"✅✅✅ MATCHED STUDY LEVEL '{level}' with pattern '{pattern}' ✅✅✅")
                        logger.info(f"✅ MATCHED study level '{level}' with pattern '{pattern}'")
                        break
                if 'study_level' in contact_info:
                    break
            
            # Extract program/field of study - SIMPLIFIED and more flexible
            program_keywords = [
                'computer science', 'cs', 'it', 'information technology', 'software engineering',
                'engineering', 'mechanical', 'electrical', 'civil', 'chemical', 'biomedical',
                'business', 'management', 'mba', 'finance', 'accounting', 'marketing', 'economics',
                'medicine', 'medical', 'health', 'nursing', 'pharmacy', 'public health',
                'arts', 'humanities', 'english', 'history', 'philosophy', 'psychology',
                'science', 'physics', 'chemistry', 'biology', 'mathematics', 'math', 'statistics',
                'architecture', 'design', 'fashion', 'music', 'film', 'journalism'
            ]
            
            logger.info(f"🔍 DEBUG: Checking program keywords in message: '{message_lower}'")
            print(f"🔍🔍🔍 CHECKING PROGRAM KEYWORDS: '{message_lower}' 🔍🔍🔍")
            for keyword in program_keywords:
                if keyword in message_lower:
                    contact_info['program'] = keyword.title()
                    print(f"✅✅✅ MATCHED PROGRAM '{keyword}' ✅✅✅")
                    logger.info(f"✅ MATCHED program '{keyword}'")
                    break
            
            # If no program found with keywords, try to extract from context
            if 'program' not in contact_info:
                logger.info(f"🔍 DEBUG: No direct keyword match, trying context patterns...")
                # Look for "study X" or "interested in X" patterns
                study_patterns = [
                    r'\b(?:study|studying|pursue|pursuing|interested in|want to study)\s+([a-zA-Z\s]+?)(?:\s+in|\s+for|\s*$|\.|,)',
                    r'\b(?:study|studying|pursue|pursuing|interested in|want to study)\s+([a-zA-Z\s]+?)(?:\s+degree|\s+program|\s+course)',
                ]
                
                for pattern in study_patterns:
                    program_match = re.search(pattern, message_lower, re.IGNORECASE)
                    if program_match:
                        program = program_match.group(1).strip()
                        # Clean up the program name
                        program = re.sub(r'\b(?:degree|program|course|in|for)\b', '', program).strip()
                        if program and len(program) > 2 and program not in ['a', 'an', 'the', 'my', 'your']:
                            contact_info['program'] = program.title()
                            logger.info(f"✅ MATCHED program from context: '{program}' with pattern '{pattern}'")
                            break
            
            # Extract intake period
            intake_patterns = {
                'fall': ['fall', 'autumn', 'september', 'october', 'november'],
                'spring': ['spring', 'march', 'april', 'may'],
                'summer': ['summer', 'june', 'july', 'august'],
                'winter': ['winter', 'december', 'january', 'february']
            }
            
            logger.info(f"🔍 DEBUG: Checking intake patterns in message: '{message_lower}'")
            for intake, patterns in intake_patterns.items():
                for pattern in patterns:
                    if pattern in message_lower:
                        contact_info['intake'] = intake.title()
                        logger.info(f"✅ MATCHED intake '{intake}' with pattern '{pattern}'")
                        break
                if 'intake' in contact_info:
                    break
            
            # Log what we found
            if contact_info:
                logger.info(f"🔍 FINAL CONTACT INFO EXTRACTED: {contact_info}")
                logger.info(f"🔍 Country detected: {contact_info.get('country', 'NOT FOUND')}")
                logger.info(f"🔍 Study level detected: {contact_info.get('study_level', 'NOT FOUND')}")
                logger.info(f"🔍 Program detected: {contact_info.get('program', 'NOT FOUND')}")
                logger.info(f"🔍 Intake detected: {contact_info.get('intake', 'NOT FOUND')}")
            else:
                logger.info("❌ No valid contact info found in message")
            
            # Return ALL extracted info, not just when there's email/phone
            # This allows us to capture study level, program, country even without contact details
            return contact_info
        except Exception as e:
            logger.error(f"❌ Error in _extract_contact_info: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
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

# Global instance - will be properly initialized after config is loaded
smart_response = None

def get_smart_response():
    """Get the properly configured smart_response instance"""
    global smart_response
    if smart_response is None:
        # Initialize with proper configuration
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
        smart_response = SmartResponse()
        # Initialize the lead capture tool with proper config
        smart_response.lead_capture_tool = LeadCaptureTool(config)
        logger.info("SmartResponse instance properly initialized with configuration")
    return smart_response
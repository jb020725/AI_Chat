"""
Smart Response System for AI Consultancy Chatbot

Features:
- Answer visa questions directly
- Detect user interest and capture leads
- Save leads to Supabase database
- Send email notifications
- Use session memory for personalization
- No RAG - just direct LLM responses
- PARALLEL 2-LLM processing for faster responses (contact extraction + response generation run simultaneously)
- BACKGROUND database operations for even faster responses while maintaining data integrity
- FULL context loading for better LLM responses (session memory + conversation history)
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import re
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
        """Generate response and handle lead capture using PARALLEL 2-LLM processing + BACKGROUND DB operations"""
        try:
            if not self.llm_model:
                return {
                    "response": "Hello! I'm your professional student visa consultant. I can help you with visa applications for USA, UK, Australia, and South Korea. What country are you interested in studying in?",
                    "success": True,
                    "function_calls": []
                }
            
            # ✅ PARALLEL PROCESSING: Run both LLM calls simultaneously
            import concurrent.futures
            
            # Create a thread pool for parallel LLM calls
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                # Submit both tasks simultaneously
                contact_extraction_future = executor.submit(
                    self._extract_contact_info_parallel, user_message
                )
                response_generation_future = executor.submit(
                    self._generate_response_parallel, user_message, session_id, conversation_history
                )
                
                # Wait for both to complete (they run in parallel)
                contact_info = contact_extraction_future.result()
                ai_response = response_generation_future.result()
            
            logger.info(f"🔍 PARALLEL PROCESSING COMPLETE: Contact info extracted, response generated")
            logger.info(f"🔍 Contact info extracted: {contact_info}")
            
            # ✅ BACKGROUND DATABASE OPERATIONS: Start DB operations in background (don't wait)
            # This makes responses faster while maintaining data integrity
            # Use a separate thread pool for background operations to avoid blocking
            import threading
            background_thread = threading.Thread(
                target=self._background_database_operations,
                args=(session_id, contact_info, user_message, ai_response),
                daemon=True  # Daemon thread so it doesn't block shutdown
            )
            background_thread.start()
            
            # Log that background operations started
            logger.info(f"🚀 Background database operations started for session {session_id}")
            
            # Return response immediately - database operations continue in background
            return {
                "response": ai_response,
                "success": True,
                "function_calls": [],
                "user_info_extracted": contact_info
            }
                
        except Exception as e:
            logger.error(f"Error in generate_smart_response: {e}")
            return {
                "response": "I encountered an error. Please try again.",
                "success": False,
                "error": str(e)
            }

    def _background_database_operations(self, session_id: str, contact_info: Dict[str, str], user_message: str, ai_response: str):
        """Run database operations in the background without blocking the response"""
        try:
            logger.info(f"🚀 BACKGROUND DB OPERATIONS STARTED for session {session_id}")
            
            # 1. Update session memory with extracted contact info
            if contact_info:
                self._update_session_memory_with_contact_info(session_id, contact_info)
                logger.info(f"✅ Background: Session memory updated with contact info")
            
            # 2. Update session memory with conversation exchange
            self._update_session_memory_with_exchange(session_id, user_message, ai_response)
            logger.info(f"✅ Background: Conversation exchange tracked")
            
            # 3. Detect and save lead (this includes database operations)
            lead_saved = self._detect_and_save_lead(user_message, session_id, contact_info)
            if lead_saved:
                logger.info(f"✅ Background: Lead saved/updated successfully")
            else:
                logger.info(f"ℹ️ Background: No lead action needed")
            
            logger.info(f"✅ BACKGROUND DB OPERATIONS COMPLETED for session {session_id}")
            
        except Exception as e:
            logger.error(f"❌ Background database operations failed: {e}")
            import traceback
            logger.error(f"❌ Background operations traceback: {traceback.format_exc()}")

    def _update_session_memory_with_contact_info(self, session_id: str, contact_info: Dict[str, str]):
        """Update session memory with extracted contact info"""
        try:
            update_data = {}
            
            if contact_info.get('name'):
                update_data['name'] = contact_info['name']
            if contact_info.get('email'):
                update_data['email'] = contact_info['email']
            if contact_info.get('phone'):
                update_data['phone'] = contact_info['phone']
            if contact_info.get('country'):
                update_data['country'] = contact_info['country']
            if contact_info.get('intake'):
                update_data['intake'] = contact_info['intake']
            if contact_info.get('study_level'):
                update_data['program_level'] = contact_info['study_level']  # ✅ Correct: Map to session memory field
            if contact_info.get('program'):
                update_data['field_of_study'] = contact_info['program']  # ✅ Correct: Map to session memory field
            
            if update_data:
                logger.info(f"🔍 Updating session memory with: {update_data}")
                self.session_memory.update_session(session_id, update_data)
            
        except Exception as e:
            logger.error(f"❌ Error updating session memory: {e}")

    def _update_session_memory_with_exchange(self, session_id: str, user_message: str, bot_response: str):
        """Update session memory with conversation exchange"""
        try:
            session_info = self.session_memory.get_user_info(session_id)
            if session_info:
                session_info.add_conversation_exchange(user_message, bot_response)
                logger.info(f"🔍 Session memory updated with exchange for session {session_id}")
        except Exception as e:
            logger.error(f"❌ Error updating session memory with exchange: {e}")
    
    def _create_new_lead_simple(self, contact_info: Dict[str, str], session_info: Any, session_id: str) -> bool:
        """Create a new lead with ANY information provided"""
        try:
            # Prepare lead data - save whatever info we have
            lead_data = {
                "session_id": session_id,
                "name": contact_info.get('name', ''),
                "phone": contact_info.get('phone', ''),
                "email": contact_info.get('email', ''),
                "target_country": contact_info.get('country', ''),
                "intake": contact_info.get('intake', ''),
                "study_level": contact_info.get('study_level', ''),
                "program": contact_info.get('program', ''),
                "status": "new_lead",
                "created_at": datetime.now().isoformat()
            }
            
            # Log what we're creating
            logger.info(f"🔍 LEAD DATA TO BE CREATED: {lead_data}")
            logger.info(f"🔍 INFO EXTRACTED: {contact_info}")
            
            # Save to database
            result = self.lead_capture_tool.create_lead(lead_data)
            
            if result.get('success'):
                logger.info(f"✅ New lead created successfully: {lead_data}")
                return True
            else:
                logger.error(f"❌ Failed to create new lead: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error creating new lead: {e}")
            return False
    
    def _update_existing_lead_simple(self, existing_lead: Dict[str, Any], contact_info: Dict[str, str], session_info: Any) -> bool:
        """Update existing lead with ANY new information"""
        try:
            # Prepare update data - update with any new info
            update_data = {}
            
            # Update name if we have one
            if contact_info.get('name'):
                update_data['name'] = contact_info['name']
                logger.info(f"🔍 Updating name to: {contact_info['name']}")
            
            # Update email if we have one
            if contact_info.get('email'):
                update_data['email'] = contact_info['email']
                logger.info(f"🔍 Updating email to: {contact_info['email']}")
            
            # Update phone if we have one
            if contact_info.get('phone'):
                update_data['phone'] = contact_info['phone']
                logger.info(f"🔍 Updating phone to: {contact_info['phone']}")
            
            # Update country if we have one
            if contact_info.get('country'):
                update_data['target_country'] = contact_info['country']
                logger.info(f"🔍 Updating country to: {contact_info['country']}")
            
            # Update intake if we have one
            if contact_info.get('intake'):
                update_data['intake'] = contact_info['intake']
                logger.info(f"🔍 Updating intake to: {contact_info['intake']}")
            
            # Update study level if we have one
            if contact_info.get('study_level'):
                update_data['study_level'] = contact_info['study_level']
                logger.info(f"🔍 Updating study_level to: {contact_info['study_level']}")
            
            # Update program if we have one
            if contact_info.get('program'):
                update_data['program'] = contact_info['program']
                logger.info(f"🔍 Updating program to: {contact_info['program']}")
            
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
    
    # ❌ REMOVED: Auto-close session methods (only frontend-triggered)
    
    def _detect_and_save_lead(self, user_message: str, session_id: str, contact_info: Dict[str, str] = None) -> bool:
        """Detect if user provided ANY info and save/update lead - ONE PER SESSION, AUTO-UPDATE"""
        try:
            logger.info(f"🔍 Lead detection started for message: '{user_message[:100]}...'")
            
            # Use provided contact_info if available, otherwise extract (fallback)
            if contact_info is None:
                contact_info = self._extract_contact_info(user_message)
                logger.info(f"🔍 Info extracted (fallback): {contact_info}")
            else:
                logger.info(f"🔍 Using provided contact info: {contact_info}")
            
            # ✅ NEW LOGIC: Save if ANY info is provided (not just contact info)
            has_any_info = any([
                contact_info.get('name'),
                contact_info.get('email'), 
                contact_info.get('phone'),
                contact_info.get('country'),
                contact_info.get('study_level'),
                contact_info.get('program'),
                contact_info.get('intake')
            ])
            
            if not has_any_info:
                logger.info("🔍 No information found, skipping lead creation/update")
                return False
            
            logger.info(f"🔍 Information found - proceeding with lead management")
            
            # Get session info for additional details
            session_info = self.session_memory.get_user_info(session_id)
            logger.info(f"🔍 Session info: {session_info}")
            
            # Check if lead already exists for this session
            existing_lead = self._get_existing_lead(session_id)
            
            if existing_lead:
                logger.info(f"🔍 Updating existing lead for session {session_id}")
                logger.info(f"🔍 Existing lead data: {existing_lead}")
                # Update existing lead with new information
                return self._update_existing_lead_simple(existing_lead, contact_info, session_info)
            else:
                logger.info(f"🔍 Creating new lead for session {session_id} - FIRST TIME with info")
                # Create new lead with ANY information
                return self._create_new_lead_simple(contact_info, session_info, session_id)
                
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
        
        # Name is valid if it has at least one valid word AND is not too long
        if len(valid_words) == 0:
            return False
        
        # Additional validation: name should not be too long (max 50 characters)
        if len(name) > 50:
            return False
        
        # Additional validation: name should not contain numbers or special characters
        if re.search(r'[0-9!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', name):
            return False
        
        return True
    
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
        """Extract contact information using AI - Much smarter than regex!"""
        try:
            if not self.llm_model:
                logger.warning("❌ No LLM model available for AI extraction, falling back to basic extraction")
                return self._extract_contact_info_basic(message)
            
            logger.info(f"🤖 AI EXTRACTION STARTED for message: '{message[:100]}...'")
            
            # Create AI extraction prompt
            extraction_prompt = f"""
            Extract information from this user message: "{message}"
            
            Return ONLY a valid JSON object with these exact fields:
            {{
                "name": "extracted name or null",
                "email": "extracted email or null",
                "phone": "extracted phone or null",
                "country": "extracted country or null",
                "study_level": "extracted study level or null",
                "program": "extracted program or null",
                "intake": "extracted intake or null"
            }}
            
            Extraction Rules:
            1. NAME: Look for "my name is", "i am", "i'm", "call me", "this is" patterns
            2. EMAIL: Find any valid email address format
            3. PHONE: Find phone numbers (digits, may include +, spaces, dashes, parentheses)
            4. COUNTRY: Look for USA, UK, Australia, South Korea (or variations)
            5. STUDY_LEVEL: Look for bachelor, master, masters, phd, diploma, etc.
            6. PROGRAM: Look for field of study like IT, computer science, engineering, business, etc.
            7. INTAKE: Look for fall, spring, summer, winter, or month names
            
            Examples:
            - "i am cursor bot" → name: "cursor bot"
            - "9999999999 is my contact" → phone: "9999999999"
            - "cursorgdh@gmail.com" → email: "cursorgdh@gmail.com"
            - "planning to apply for masters" → study_level: "master"
            - "apply in it sector" → program: "it"
            - "interested in usa" → country: "usa"
            
            Return ONLY the JSON, no other text.
            """
            
            # Use AI to extract information
            try:
                response = self.llm_model.generate_content(extraction_prompt)
                if response and hasattr(response, 'text'):
                    import json
                    # Clean the response to get just the JSON
                    response_text = response.text.strip()
                    # Remove any markdown formatting
                    if response_text.startswith('```json'):
                        response_text = response_text.replace('```json', '').replace('```', '').strip()
                    elif response_text.startswith('```'):
                        response_text = response_text.replace('```', '').strip()
                    
                    # Parse the JSON response
                    contact_info = json.loads(response_text)
                    
                    # Clean up the extracted data
                    cleaned_info = {}
                    for key, value in contact_info.items():
                        if value and value != "null" and value.lower() != "null":
                            cleaned_info[key] = value.strip()
                        else:
                            cleaned_info[key] = None
                    
                    logger.info(f"🤖 AI EXTRACTION SUCCESS: {cleaned_info}")
                    return cleaned_info
                    
                else:
                    logger.error("❌ AI extraction failed - no response text")
                    return self._extract_contact_info_basic(message)
                    
            except json.JSONDecodeError as e:
                logger.error(f"❌ AI extraction failed - invalid JSON: {e}")
                logger.error(f"❌ Raw AI response: {response.text if response else 'No response'}")
                return self._extract_contact_info_basic(message)
                
            except Exception as e:
                logger.error(f"❌ AI extraction failed: {e}")
                return self._extract_contact_info_basic(message)
                
        except Exception as e:
            logger.error(f"❌ Error in AI extraction: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return self._extract_contact_info_basic(message)

    def _extract_contact_info_parallel(self, message: str) -> Dict[str, str]:
        """Extract contact information using AI - PARALLEL VERSION"""
        try:
            if not self.llm_model:
                logger.warning("❌ No LLM model available for AI extraction, falling back to basic extraction")
                return self._extract_contact_info_basic(message)
            
            logger.info(f"🤖 PARALLEL AI EXTRACTION STARTED for message: '{message[:100]}...'")
            
            # Create AI extraction prompt
            extraction_prompt = f"""
            Extract information from this user message: "{message}"
            
            Return ONLY a valid JSON object with these exact fields:
            {{
                "name": "extracted name or null",
                "phone": "extracted phone or null",
                "email": "extracted email or null",
                "country": "extracted country or null",
                "study_level": "extracted study level or null",
                "program": "extracted program or null",
                "intake": "extracted intake or null"
            }}
            
            Extraction Rules:
            1. NAME: Look for "my name is", "i am", "i'm", "call me", "this is" patterns
            2. EMAIL: Find any valid email address format
            3. PHONE: Find phone numbers (digits, may include +, spaces, dashes, parentheses)
            4. COUNTRY: Look for USA, UK, Australia, South Korea (or variations)
            5. STUDY_LEVEL: Look for bachelor, master, masters, phd, diploma, etc.
            6. PROGRAM: Look for field of study like IT, computer science, engineering, business, etc.
            7. INTAKE: Look for fall, spring, summer, winter, or month names
            
            Examples:
            - "i am cursor bot" → name: "cursor bot"
            - "9999999999 is my contact" → phone: "9999999999"
            - "cursorgdh@gmail.com" → email: "cursorgdh@gmail.com"
            - "planning to apply for masters" → study_level: "master"
            - "apply in it sector" → program: "it"
            - "interested in usa" → country: "usa"
            
            Return ONLY the JSON, no other text.
            """
            
            # Use AI to extract information
            try:
                response = self.llm_model.generate_content(extraction_prompt)
                if response and hasattr(response, 'text'):
                    import json
                    # Clean the response to get just the JSON
                    response_text = response.text.strip()
                    # Remove any markdown formatting
                    if response_text.startswith('```json'):
                        response_text = response_text.replace('```json', '').replace('```', '').strip()
                    elif response_text.startswith('```'):
                        response_text = response_text.replace('```', '').strip()
                    
                    # Parse the JSON response
                    contact_info = json.loads(response_text)
                    
                    # Clean up the extracted data
                    cleaned_info = {}
                    for key, value in contact_info.items():
                        if value and value != "null" and value.lower() != "null":
                            cleaned_info[key] = value.strip()
                        else:
                            cleaned_info[key] = None
                    
                    logger.info(f"🤖 PARALLEL AI EXTRACTION SUCCESS: {cleaned_info}")
                    return cleaned_info
                    
                else:
                    logger.error("❌ AI extraction failed - no response text")
                    return self._extract_contact_info_basic(message)
                    
            except json.JSONDecodeError as e:
                logger.error(f"❌ AI extraction failed - invalid JSON: {e}")
                logger.error(f"❌ Raw AI response: {response.text if response else 'No response'}")
                return self._extract_contact_info_basic(message)
                
            except Exception as e:
                logger.error(f"❌ AI extraction failed: {e}")
                return self._extract_contact_info_basic(message)
                
        except Exception as e:
            logger.error(f"❌ Error in parallel AI extraction: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return self._extract_contact_info_basic(message)

    def _generate_response_parallel(self, user_message: str, session_id: str, conversation_history: List[Dict]) -> str:
        """Generate AI response - PARALLEL VERSION with FULL CONTEXT"""
        try:
            logger.info(f"🤖 PARALLEL RESPONSE GENERATION STARTED for message: '{user_message[:100]}...'")
            
            # ✅ ENHANCED: Get FULL context including session memory and conversation history
            # This ensures LLM has complete information for better responses
            session_info = self.session_memory.get_user_info(session_id)
            
            # Create response prompt with FULL context (including lead_saved status)
            # We pass lead_saved=False initially since we don't know yet, but LLM gets full context
            prompt = self._create_response_prompt(user_message, session_id, conversation_history, False)
            
            logger.info(f"🤖 PARALLEL RESPONSE GENERATION: Full context loaded for session {session_id}")
            logger.info(f"🤖 PARALLEL RESPONSE GENERATION: Session info available: {session_info is not None}")
            logger.info(f"🤖 PARALLEL RESPONSE GENERATION: Conversation history length: {len(conversation_history)}")
            
            # Get response from LLM with full context
            try:
                response = self.llm_model.generate_content(prompt)
                if response and hasattr(response, 'text'):
                    ai_response = response.text
                    logger.info(f"🤖 PARALLEL RESPONSE GENERATION SUCCESS: {len(ai_response)} characters")
                    logger.info(f"🤖 PARALLEL RESPONSE GENERATION: Response generated with full context")
                    return ai_response
                else:
                    logger.error("❌ AI response generation failed - no response text")
                    return "I understand your question. Let me help you with that."
                    
            except Exception as e:
                logger.error(f"Error calling LLM for response: {e}")
                return "I'm experiencing technical difficulties. Please try again or ask a different question."
                
        except Exception as e:
            logger.error(f"❌ Error in parallel response generation: {e}")
            return "I encountered an error. Please try again."
    
    def _extract_contact_info_basic(self, message: str) -> Dict[str, str]:
        """Fallback basic extraction if AI fails"""
        try:
            logger.info(f"🔄 Using basic extraction fallback for message: '{message[:100]}...'")
            contact_info = {}
            message_lower = message.lower()
            
            # Basic email extraction
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_match = re.search(email_pattern, message)
            if email_match:
                contact_info['email'] = email_match.group()
            
            # Basic phone extraction
            phone_pattern = r'\b\d{10,15}\b'
            phone_match = re.search(phone_pattern, message)
            if phone_match:
                contact_info['phone'] = phone_match.group()
            
            # Basic name extraction
            name_pattern = r'\b(?:my name is|i am|i\'m|call me|this is)\s+([a-zA-Z\s]+?)(?:\s*[,.]|$)'
            name_match = re.search(name_pattern, message_lower, re.IGNORECASE)
            if name_match:
                contact_info['name'] = name_match.group(1).strip().title()
            
            # Basic country extraction
            if 'usa' in message_lower or 'us' in message_lower:
                contact_info['country'] = 'usa'
            elif 'uk' in message_lower:
                contact_info['country'] = 'uk'
            elif 'australia' in message_lower:
                contact_info['country'] = 'australia'
            elif 'korea' in message_lower:
                contact_info['country'] = 'south_korea'
            
            # Basic study level extraction
            if 'master' in message_lower:
                contact_info['study_level'] = 'master'
            elif 'bachelor' in message_lower:
                contact_info['study_level'] = 'bachelor'
            elif 'phd' in message_lower:
                contact_info['study_level'] = 'phd'
            
            # Basic program extraction
            if 'it' in message_lower or 'information technology' in message_lower:
                contact_info['program'] = 'IT'
            elif 'computer' in message_lower:
                contact_info['program'] = 'Computer Science'
            elif 'engineering' in message_lower:
                contact_info['program'] = 'Engineering'
            
            logger.info(f"🔄 Basic extraction result: {contact_info}")
            return contact_info
            
        except Exception as e:
            logger.error(f"❌ Error in basic extraction: {e}")
            return {}
    
    def _create_response_prompt(self, user_message: str, session_id: str, conversation_history: List[Dict], lead_saved: bool) -> str:
        """Create response prompt for the chatbot"""
        
        # Get session info for additional details
        session_info = self.session_memory.get_user_info(session_id)
        session_context = ""
        if session_info:
            session_context = f"""
SESSION CONTEXT:
- Has contact info: {bool(session_info.email or session_info.phone)}
- Study country: {getattr(session_info, 'country', 'Not specified')}
- Study level: {getattr(session_info, 'program_level', 'Not specified')}  # ✅ Correct: Use session memory field
- Intake: {getattr(session_info, 'intake', 'Not specified')}
- Program: {getattr(session_info, 'field_of_study', 'Not specified')}  # ✅ Correct: Use session memory field
- Session ID: {session_id}
"""
        
        # CRITICAL FIX: Get existing lead data for this session
        existing_lead_data = ""
        try:
            existing_lead = self._get_existing_lead(session_id)
            if existing_lead:
                existing_lead_data = f"""
EXISTING LEAD DATA (DO NOT ASK FOR THIS INFORMATION AGAIN):
- Email: {existing_lead.get('email', 'N/A')}
- Name: {existing_lead.get('name', 'N/A')}
- Phone: {existing_lead.get('phone', 'N/A')}
- Target Country: {existing_lead.get('target_country', 'N/A')}
- Intake: {existing_lead.get('intake', 'N/A')}
- Study Level: {existing_lead.get('study_level', 'N/A')}
- Program: {existing_lead.get('program', 'N/A')}
- Status: {existing_lead.get('status', 'N/A')}

IMPORTANT: User has already provided this information. DO NOT ask for it again.
Focus on providing helpful visa information and guidance instead.
"""
            else:
                existing_lead_data = "\nEXISTING LEAD DATA: No lead found for this session yet.\n"
        except Exception as e:
            logger.error(f"Error getting existing lead data: {e}")
            existing_lead_data = "\nEXISTING LEAD DATA: Error retrieving data\n"
        
        # Build conversation context - Last 5 exchanges instead of 3
        conversation_context = ""
        if conversation_history:
            recent_messages = conversation_history[-5:]  # Last 5 messages
            conversation_context = "\nRECENT CONVERSATION (Last 5 exchanges):\n"
            for i, msg in enumerate(recent_messages, 1):
                role = msg.get('role', 'user')
                content = msg.get('content', msg.get('user_message', msg.get('user_input', '')))
                conversation_context += f"{i}. {role.title()}: {content}\n"
        
        # ✅ RESTORED: Lead table data is essential for LLM to see what's already saved
        # This prevents the LLM from asking for information already provided
        lead_table_data = ""
        try:
            if session_info and (session_info.email or session_info.phone):
                # Get leads for this session/user
                leads = self.lead_capture_tool.get_leads_by_session(session_id)
                if leads and leads.get('success') and leads.get('data'):
                    lead_table_data = "\nLEAD TABLE DATA (Already Saved in Database):\n"
                    lead_table_data += "=" * 50 + "\n"
                    for lead in leads['data']:
                        lead_table_data += f"""
Lead ID: {lead.get('id', 'N/A')}
- Email: {lead.get('email', 'N/A')}
- Name: {lead.get('name', 'N/A')}
- Phone: {lead.get('phone', 'N/A')}
- Target Country: {lead.get('target_country', 'N/A')}
- Intake: {lead.get('intake', 'N/A')}
- Study Level: {lead.get('study_level', 'N/A')}
- Program: {lead.get('program', 'N/A')}
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
                'country': getattr(session_info, 'country', ''),
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
        
        # Add enhanced context sections (CLEAN - no duplicates)
        enhanced_context = f"""
{existing_lead_data}

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
        try:
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
            
            # Create SmartResponse instance
            smart_response = SmartResponse()
            
            # Initialize the lead capture tool with proper config
            from app.tools.lead_capture_tool import LeadCaptureTool
            smart_response.lead_capture_tool = LeadCaptureTool(config)
            
            logger.info("✅ SmartResponse instance properly initialized with configuration")
            logger.info(f"✅ Lead capture tool initialized: {smart_response.lead_capture_tool is not None}")
            logger.info(f"✅ Session memory initialized: {smart_response.session_memory is not None}")
            
        except Exception as e:
            logger.error(f"❌ Error initializing SmartResponse: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            raise
    
    return smart_response
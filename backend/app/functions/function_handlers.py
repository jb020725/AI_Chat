"""
Function Handlers for Gemini Native Function Calling

Handles the execution of functions called by the LLM:
- Contact information collection
- Country-specific searches
- Lead qualification
"""

import logging
from typing import Dict, Any, Optional
from app.memory.session_memory import get_session_memory
from app.rag.retriever import retrieve
from app.tools.lead_capture_tool import LeadCaptureTool
import time

logger = logging.getLogger(__name__)

class FunctionHandler:
    """Handles execution of functions called by the LLM"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Initialize lead capture tool
        self.lead_capture_tool = LeadCaptureTool()
        # Initialize session memory
        self.session_memory = get_session_memory()
    

        
            
    def handle_contact_request(self, session_id: str, **kwargs) -> Dict[str, Any]:
        """
        Smart contact request handler - detects both lead opportunities and urgent contact needs
        """
        try:
            user_query = kwargs.get('user_query', '').lower()
            conversation_context = kwargs.get('conversation_context', {})
            detected_interests = kwargs.get('detected_interests', [])
            
            # AI Consultancy contact numbers dictionary
            AI_CONSULTANCY_NUMBERS = {
                "primary": "+977-1-4444444",
                "urgent": "+977-1-5555555", 
                "whatsapp": "+977-9800000000",
                "office": "+977-1-6666666"
            }
            
            # Interest detection keywords - BOTH SERIOUS INTENT AND URGENCY
            interest_keywords = [
                # Action-oriented phrases (normal lead opportunity)
                "i want to apply", "i am applying", "i will apply", "ready to apply",
                "looking for guidance", "need guidance", "want guidance",
                "help me apply", "assist me", "support me", "guide me through",
                
                # Company/service mentions (normal lead opportunity)
                "ai consultancy", "ai consultancy education", "your company", "your service",
                "you will help", "you can help", "you will process",
                
                # Contact expectations (normal lead opportunity)
                "call me", "contact me", "reach me", "follow up",
                "representative", "advisor", "counselor", "consultant",
                "office visit", "meet you", "come to office",
                
                # Commitment phrases (normal lead opportunity)
                "process my visa", "handle my application", "take care of",
                "manage my case", "work on my visa", "start my process",
                
                # Timeline commitment (normal lead opportunity)
                "march intake", "fall intake", "spring intake", "specific date",
                "when should i", "what's the timeline", "deadline"
            ]
            
            # URGENCY detection keywords (immediate human contact needed)
            urgency_keywords = [
                "urgent", "emergency", "extreme", "immediate", "now",
                "talk to someone", "need help now", "call me now", "immediately",
                "asap", "right now", "this instant", "critical", "desperate"
            ]
            
            # Check if user shows serious interest OR urgency
            shows_interest = any(keyword in user_query for keyword in interest_keywords)
            shows_urgency = any(keyword in user_query for keyword in urgency_keywords)
            
            # Check if we already have contact info
            session_info = self.session_memory.get_user_info(session_id)
            has_contact = session_info and (session_info.email or session_info.phone)
            
            if shows_urgency:
                # URGENT CONTACT NEEDED - Give AI Consultancy number immediately
                urgency_level = "extreme" if any(word in user_query for word in ["emergency", "extreme", "critical"]) else "urgent"
                contact_preference = "call" if "call" in user_query else "any"
                
                message = f"🚨 I understand this is {urgency_level}! Here's our direct contact:\n\n📞 **AI Consultancy**: {AI_CONSULTANCY_NUMBERS['urgent']}\n📱 **WhatsApp**: {AI_CONSULTANCY_NUMBERS['whatsapp']}\n🏢 **Office**: {AI_CONSULTANCY_NUMBERS['office']}\n\n**Someone from our team will call you immediately!** Please share your phone number so we can reach you right away."
                ask_for_contact = True
                request_type = "urgent_contact"
                
            elif shows_interest and not has_contact:
                # Normal lead opportunity detected
                message = "I can see you're serious about this! To give you personalized guidance and keep you updated, could you share your name and email/phone number? I'll send you detailed information and important updates."
                ask_for_contact = True
                request_type = "lead_opportunity"
                
            else:
                # No contact request needed
                message = "Continue with your question about student visas."
                ask_for_contact = False
                request_type = "none"
            
            self.logger.info(f"Contact request handling for session {session_id}: {request_type} - {message}")
            
            return {
                "success": True,
                "data": {
                    "request_type": request_type,
                    "urgency_level": urgency_level if shows_urgency else "normal",
                    "message": message,
                    "ask_for_contact": ask_for_contact,
                    "detected_interests": detected_interests,
                    "conversation_context": conversation_context,
                    "ai_consultancy_numbers": AI_CONSULTANCY_NUMBERS if shows_urgency else None
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in handle_contact_request: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "data": None
            }
    
    def handle_detect_and_save_contact_info(self, session_id: str, **kwargs) -> Dict[str, Any]:
        """
        Automatically detect, extract, and save contact information from user messages
        """
        try:
            user_query = kwargs.get('user_query', '').lower()
            conversation_context = kwargs.get('conversation_context', {})
            extraction_mode = kwargs.get('extraction_mode', 'auto_detect')
            
            # Get existing session info
            session_info = self.session_memory.get_user_info(session_id)
            
            # Initialize extracted data
            extracted_data = {}
            
            # Name extraction patterns - highly specific to avoid false matches
            name_patterns = [
                r"my name is ([A-Za-z]+(?:\s+[A-Za-z]+){0,3})(?:\s*[,.]|\s+and\s|$)",
                r"i am ([A-Za-z]+(?:\s+[A-Za-z]+){0,3})(?=\s*[,.]|\s+and\s|$)(?!.*(?:applying|studying|interested|going|planning))",
                r"i'm ([A-Za-z]+(?:\s+[A-Za-z]+){0,3})(?=\s*[,.]|\s+and\s|$)(?!.*(?:applying|studying|interested|going|planning))",
                r"([A-Za-z]+(?:\s+[A-Za-z]+){0,3}) here(?!.*(?:applying|studying|interested))",
                r"this is ([A-Za-z]+(?:\s+[A-Za-z]+){0,3})(?=\s*[,.]|\s+and\s|$)(?!.*(?:applying|studying|interested))",
                r"([A-Za-z]+(?:\s+[A-Za-z]+){0,3}) is my name",
                r"call me ([A-Za-z]+(?:\s+[A-Za-z]+){0,3})(?=\s*[,.]|\s+and\s|$)",
                r"name:\s*([A-Za-z]+(?:\s+[A-Za-z]+){0,3})(?=\s*[,.]|\s+and\s|$)"
            ]
            
            # Email extraction patterns
            email_patterns = [
                r"email is ([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                r"my email ([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                r"email: ([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
            ]
            
            # Phone extraction patterns
            phone_patterns = [
                r"phone is (\d+)",
                r"my phone (\d+)",
                r"number is (\d+)",
                r"my number (\d+)",
                r"call me at (\d+)",
                r"(\d{10,})"
            ]
            
            # Country extraction patterns
            country_patterns = [
                r"interested in (usa|uk|australia|south korea)",
                r"want to go to (usa|uk|australia|south korea)",
                r"planning for (usa|uk|australia|south korea)",
                r"for (usa|uk|australia|south korea)",
                r"(usa|uk|australia|south korea) for",
                r"studying in (usa|uk|australia|south korea)"
            ]
            
            # Intake extraction patterns
            intake_patterns = [
                r"for (fall|spring|summer|march|september|january) (\d{4})",
                r"(fall|spring|summer|march|september|january) (\d{4})",
                r"planning (fall|spring|summer|march|september|january)",
                r"(fall|spring|summer|march|september|january) intake",
                r"intake (fall|spring|summer|march|september|january)"
            ]
            
            # Program level extraction
            program_patterns = [
                r"(bachelor|master|phd|doctorate|undergraduate|graduate)",
                r"studying (bachelor|master|phd|doctorate|undergraduate|graduate)",
                r"(bachelor|master|phd|doctorate|undergraduate|graduate) degree"
            ]
            
            import re
            
            # Extract name
            for pattern in name_patterns:
                match = re.search(pattern, user_query)
                if match:
                    extracted_data['name'] = match.group(1).title()
                    break
            
            # Extract email
            for pattern in email_patterns:
                match = re.search(pattern, user_query)
                if match:
                    extracted_data['email'] = match.group(1).lower()
                    break
            
            # Extract phone
            for pattern in phone_patterns:
                match = re.search(pattern, user_query)
                if match:
                    extracted_data['phone'] = match.group(1)
                    break
            
            # Extract country
            for pattern in country_patterns:
                match = re.search(pattern, user_query)
                if match:
                    country = match.group(1).upper()
                    if country == "USA":
                        extracted_data['country'] = "USA"
                    elif country == "UK":
                        extracted_data['country'] = "UK"
                    elif country == "AUSTRALIA":
                        extracted_data['country'] = "Australia"
                    elif country == "SOUTH KOREA":
                        extracted_data['country'] = "South Korea"
                    break
            
            # Extract intake
            for pattern in intake_patterns:
                match = re.search(pattern, user_query)
                if match:
                    if len(match.groups()) == 2:
                        extracted_data['intake'] = f"{match.group(1).title()} {match.group(2)}"
                    else:
                        extracted_data['intake'] = match.group(1).title()
                    break
            
            # Extract program level
            for pattern in program_patterns:
                match = re.search(pattern, user_query)
                if match:
                    extracted_data['program_level'] = match.group(1).title()
                    break
            
            # Check if we extracted any new information
            if not extracted_data:
                return {
                    "success": True,
                    "data": {
                        "extracted": False,
                        "message": "No new contact information detected in this message",
                        "extracted_data": {},
                        "session_info": session_info.__dict__ if session_info else None
                    }
                }
            
            # Merge with existing session info
            if session_info:
                if 'name' in extracted_data and extracted_data['name']:
                    session_info.name = extracted_data['name']
                if 'email' in extracted_data and extracted_data['email']:
                    session_info.email = extracted_data['email']
                if 'phone' in extracted_data and extracted_data['phone']:
                    session_info.phone = extracted_data['phone']
                if 'country' in extracted_data and extracted_data['country']:
                    session_info.country = extracted_data['country']
                if 'intake' in extracted_data and extracted_data['intake']:
                    session_info.intake = extracted_data['intake']
                if 'program_level' in extracted_data and extracted_data['program_level']:
                    session_info.program_level = extracted_data['program_level']
            
            # Debug logging
            self.logger.info(f"DEBUG: extracted_data = {extracted_data}")
            self.logger.info(f"DEBUG: name = {extracted_data.get('name')}")
            self.logger.info(f"DEBUG: phone = {extracted_data.get('phone')}")
            self.logger.info(f"DEBUG: email = {extracted_data.get('email')}")
            self.logger.info(f"DEBUG: condition = {extracted_data.get('name') and (extracted_data.get('phone') or extracted_data.get('email'))}")
            
            # IMPROVED: Always check session memory for complete lead info
            # Get current session info
            session_name = session_info.name if session_info else None
            session_phone = session_info.phone if session_info else None
            session_email = session_info.email if session_info else None
            
            # Combine current extraction with session memory
            current_name = extracted_data.get('name') or session_name
            current_phone = extracted_data.get('phone') or session_phone
            current_email = extracted_data.get('email') or session_email
            current_country = extracted_data.get('country') or (session_info.country if session_info else None)
            current_intake = extracted_data.get('intake') or (session_info.intake if session_info else None)
            
            # Debug logging
            self.logger.info(f"LEAD SAVE CHECK - Name: {current_name}, Phone: {current_phone}, Email: {current_email}")
            
            # Check if we should ask for missing contact info FIRST
            should_ask_for_contact = False
            missing_contact_type = None
            
            # If we have a name but missing both email and phone, ask for contact
            if current_name and not current_phone and not current_email:
                should_ask_for_contact = True
                missing_contact_type = "email_or_phone"
            # If we have name and email but no phone, ask for phone
            elif current_name and current_email and not current_phone:
                should_ask_for_contact = True
                missing_contact_type = "phone"
            # If we have name and phone but no email, ask for email
            elif current_name and current_phone and not current_email:
                should_ask_for_contact = True
                missing_contact_type = "email"
            
            # Only save as lead if we have complete info AND we're not asking for contact
            if current_name and current_phone and current_email and not should_ask_for_contact:
                # Determine contact method for message
                contact_method = "phone" if extracted_data.get('phone') else "email"
                contact_value = extracted_data.get('phone') or extracted_data.get('email')
                
                lead_data = {
                    "session_id": session_id,
                    "name": current_name,
                    "email": current_email or '',
                    "phone": current_phone or '',
                    "target_country": current_country or '',
                    "intake": current_intake or '',
                    "status": "new_lead"
                }
                
                # Save to database
                lead_result = self.lead_capture_tool.create_lead(lead_data)
                
                if lead_result.get('success'):
                    lead_id = lead_result.get('lead_id', f"lead_{session_id}")
                    self.logger.info(f"Contact info automatically saved as lead: {lead_id}")
                    
                    return {
                        "success": True,
                        "data": {
                            "extracted": True,
                            "saved_as_lead": True,
                            "lead_id": lead_id,
                            "message": f"Perfect! I've saved your complete information: {current_name}, {current_phone or current_email}. You're all set!",
                            "extracted_data": extracted_data,
                            "session_info": session_info.__dict__ if session_info else None,
                            "combined_data": {
                                "name": current_name,
                                "phone": current_phone,
                                "email": current_email,
                                "country": current_country
                            }
                        }
                    }
                else:
                    self.logger.error(f"Failed to save lead automatically: {lead_result.get('error')}")
            
            # If we don't have complete lead info, update session and potentially ask for contact
            response_data = {
                "extracted": True,
                "saved_as_lead": False,
                "extracted_data": extracted_data,
                "session_info": session_info.__dict__ if session_info else None
            }
            
            if should_ask_for_contact:
                if missing_contact_type == "email_or_phone":
                    response_data["ask_for_contact"] = True
                    response_data["contact_message"] = "Great! I have your name saved. To help you better with your student visa journey, would you like to share your email address or phone number so our AI Consultancy can assist you?"
                elif missing_contact_type == "phone":
                    response_data["ask_for_contact"] = True
                    response_data["contact_message"] = "Perfect! I have your name and email. To provide you with the best assistance, would you like to share your phone number as well?"
                elif missing_contact_type == "email":
                    response_data["ask_for_contact"] = True
                    response_data["contact_message"] = "Great! I have your name and phone number. To help you better, would you like to share your email address as well?"
            else:
                response_data["message"] = f"I've updated your information with: {', '.join([f'{k}: {v}' for k, v in extracted_data.items() if v])}"
            
            return {
                "success": True,
                "data": response_data
            }
            
        except Exception as e:
            self.logger.error(f"Error in detect_and_save_contact_info: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "data": None
            }
    
    def handle_define_response_strategy(self, session_id: str, **kwargs) -> Dict[str, Any]:
        """
        Define response strategy when RAG has no results
        """
        try:
            user_query = kwargs.get('user_query', '').lower()
            rag_results_count = kwargs.get('rag_results_count', 0)
            session_memory = kwargs.get('session_memory', {})
            
            # Define student visa scope (Nepal to specific countries)
            student_visa_keywords = [
                # Core visa topics
                "student visa", "study visa", "education visa", "academic visa",
                "study", "education", "university", "college", "school",
                
                # Target countries
                "usa", "united states", "america", "us", "u.s.", "u.s.a",
                "uk", "united kingdom", "britain", "england", "great britain",
                "south korea", "korea", "korean", "seoul",
                "australia", "aussie", "australian",
                
                # Visa types
                "f-1", "m-1", "tier 4", "student route", "subclass 500", "d-2", "d-4",
                
                # Visa process
                "visa requirements", "visa application", "visa process", "visa documents",
                "financial requirements", "interview", "intake", "semester",
                
                # Nepal context
                "nepal", "nepali", "nepalese"
            ]
            
            # Check if query is on-topic
            is_on_topic = any(keyword in user_query for keyword in student_visa_keywords)
            
            # Determine strategy
            if rag_results_count > 0:
                strategy = "answer_with_rag"
                reason = "RAG has relevant results - use them"
                instruction = "Use the RAG results to answer this question"
                
            elif is_on_topic and rag_results_count == 0:
                strategy = "answer_with_memory"
                reason = "Student visa question but no RAG results - use session memory"
                instruction = "Use session memory and your knowledge to answer this student visa question"
                
            else:
                strategy = "redirect_to_topic"
                reason = "Question outside student visa scope - redirect to topic"
                instruction = "Redirect user to student visa topics"
            
            self.logger.info(f"Response strategy for session {session_id}: {strategy} - {reason}")
            
            return {
                "success": True,
                "data": {
                    "strategy": strategy,
                    "reason": reason,
                    "instruction": instruction,
                    "is_on_topic": is_on_topic,
                    "redirect_message": "Let's stay on topic. I can help with student visas from Nepal to USA, UK, South Korea, and Australia. What would you like to know about student visas?"
                }
            }
                
        except Exception as e:
            self.logger.error(f"Error in define_response_strategy: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "data": None
            }
    

    


    

    

    

    
    def execute_function(self, function_name: str, session_id: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a function by name
        
        Args:
            function_name: Name of function to execute
            session_id: Current session ID
            **kwargs: Function parameters
            
        Returns:
            Dict with function execution result
        """
        self.logger.info(f"Executing function {function_name} for session {session_id}")
        
        if function_name == "handle_contact_request":
            return self.handle_contact_request(session_id, **kwargs)
        elif function_name == "handle_contact_request":
            return self.handle_contact_request(session_id, **kwargs)
        elif function_name == "detect_and_save_contact_info":
            return self.handle_detect_and_save_contact_info(session_id, **kwargs)
        elif function_name == "define_response_strategy":
            return self.handle_define_response_strategy(session_id, **kwargs)
        else:
            return {
                "success": False,
                "message": f"Unknown function: {function_name}",
                "data": None
            }

# Global function handler instance
function_handler = FunctionHandler()

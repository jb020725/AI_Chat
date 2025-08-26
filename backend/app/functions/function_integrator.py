"""
Function Integrator for Clean Function-Calling Structure

Integrates LLM with focused, deterministic tools following best practices:
- Intent-based routing
- Consent-first approach
- Vetted content only
- Clean lead capture flow
"""

import logging
from typing import Dict, Any, List, Optional
from app.functions.function_definitions import FUNCTIONS

logger = logging.getLogger(__name__)

class FunctionIntegrator:
    """Integrates LLM with clean, focused tools"""
    
    def __init__(self, llm_model):
        self.llm_model = llm_model
        self.logger = logging.getLogger(__name__)
        # Import session memory when needed to avoid circular imports
        self._session_memory = None
    
    @property
    def session_memory(self):
        """Lazy load session memory to avoid circular imports"""
        if self._session_memory is None:
            from app.memory.session_memory import get_session_memory
            self._session_memory = get_session_memory()
        return self._session_memory
    
    def create_function_calling_prompt(self, user_message: str, session_id: str, conversation_history: List[Dict]) -> str:
        """Create the main prompt for function calling with clean structure"""
        
        # Get session context
        session_info = self.session_memory.get_user_info(session_id)
        session_context = ""
        if session_info:
            session_context = f"""
SESSION CONTEXT:
- Has contact info: {bool(session_info.email or session_info.phone)}
- Has consent: {getattr(session_info, 'consent_given', False)}
- Study country: {getattr(session_info, 'study_country', 'Not specified')}
- Study level: {getattr(session_info, 'study_level', 'Not specified')}
- Target intake: {getattr(session_info, 'target_intake', 'Not specified')}
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
        
        prompt = f"""You are an AI assistant representing AI Consultancy, specializing in student visa guidance for Nepali students applying to USA, UK, Australia, and South Korea.

{session_context}

{conversation_context}

Current user message: "{user_message}"

CONVERSATION POLICY - FOLLOW THIS EXACTLY:

1. INTENT ROUTING:
   - If user asks general visa/consultancy info → CALL get_answer(topic)
   - If user shows interest ("I want to apply...", "considering UK") and no PII yet → CALL qualify_interest, then ask for consent
   - If user consents → CALL save_lead (validate email/phone; ask for whichever is missing)
   - After save_lead → notify_human immediately

2. CONTENT POLICY:
   - Answers MUST come from get_answer only - do not invent policy or numbers
   - If topic isn't in answer map, say: "I don't have an approved answer on that. An advisor can clarify—would you like a callback?"

3. CONSENT POLICY:
   - NEVER store PII without request_consent(consent=true)
   - If phone/email shared before consent, keep in transient memory only; ask to confirm consent first
   - Always show: "With your permission, I'll store your contact details to have an advisor reach you. You can say 'no' and continue asking questions normally."

4. RESPONSE STRATEGY:
   - Be helpful and informative first
   - Answer visa questions with vetted content
   - Then politely offer: "If you'd like personalized guidance, I can have an advisor reach out to you."
   - Don't be pushy about contact info
   - Stay brief, actionable, and honest about limits

AVAILABLE FUNCTIONS:
- get_answer: Return vetted answer snippet about student visas or consultancy
- qualify_interest: Capture non-PII interest to personalize follow-ups
- request_consent: Record explicit user consent to store and contact them
- save_lead: Save lead with contact details after explicit consent

- notify_human: Ping advisors with a concise summary

EXAMPLES:
- "What documents are needed for USA student visa?" → CALL get_answer(topic="usa_visa")
- "I'm thinking UK Masters for 2026 Fall" → CALL qualify_interest(study_country="UK", study_level="Masters", target_intake="2026-Fall")
- "Yes, use +977123456789 and email me" → CALL request_consent(consent_text_version="v1.0", consent=true) THEN save_lead
- "Yes, save my contact" → CALL save_lead then notify_human

Remember: Only use approved content via get_answer. Do not invent policy or numbers. Always offer friendly CTA to share contact for an advisor. Never pressure."""
        
        return prompt
    
    def create_natural_response_prompt(self, user_message: str, function_name: str, function_result: Dict) -> str:
        """Create prompt for natural response after function execution"""
        
        natural_prompt = f"""You are a helpful visa consultant for AI Consultancy.

A function was just executed successfully: {function_name}

User's original question: {user_message}

Function result: {function_result.get('message', 'Success')}

Function data: {function_result.get('data', {})}

Please provide a natural, helpful response to the user based on the function result. Be conversational and informative. Follow these guidelines:

1. If get_answer was called: Present the vetted information clearly, then offer the CTA from the function result
2. If qualify_interest was called: Acknowledge their interest, then ask for consent to collect contact
3. If request_consent was called: Handle the consent response appropriately
4. If save_lead was called: Confirm their information is saved, then notify human advisor

6. If notify_human was called: Confirm the advisor has been notified

Keep responses brief (2-3 sentences max) and always maintain a helpful, professional tone."""
        
        return natural_prompt
    
    def create_failure_response_prompt(self, user_message: str, function_name: str, function_result: Dict) -> str:
        """Create prompt for helpful response when function fails"""
        
        failure_prompt = f"""You are a helpful visa consultant for AI Consultancy.

A function failed to execute: {function_name}

User's original question: {user_message}

Function error: {function_result.get('message', 'Unknown error')}

Please provide a helpful response that:
1. Acknowledges the issue politely
2. Offers alternatives when possible
3. Stays helpful and professional
4. Suggests next steps

For example, if get_answer fails due to unknown topic, say: "I don't have specific information about that topic yet. However, I can help you with student visas for USA, UK, Australia, and South Korea. Which of these countries interests you?"

Keep responses brief and solution-oriented."""
        
        return failure_prompt
    
    def execute_function_call(self, function_name: str, session_id: str, **kwargs) -> Dict[str, Any]:
        """Execute a function call and return result"""
        try:
            from app.functions.function_handlers import function_handler
            result = function_handler.execute_function(function_name, session_id, **kwargs)
            self.logger.info(f"Function {function_name} executed successfully: {result.get('success')}")
            return result
        except Exception as e:
            self.logger.error(f"Error executing function {function_name}: {e}")
            return {
                "success": False,
                "message": f"Function execution error: {str(e)}",
                "data": None
            }
    
    def get_function_declarations(self):
        """Get function declarations for LLM tools"""
        return FUNCTIONS

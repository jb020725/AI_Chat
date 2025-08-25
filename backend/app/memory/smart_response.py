#!/usr/bin/env python3
"""
Smart Response Generator
Integrates RAG results with session memory for intelligent responses
"""

import logging
from typing import Dict, List, Optional, Any
from .session_memory import get_session_memory

logger = logging.getLogger(__name__)

class SmartResponseGenerator:
    """Generates intelligent responses with smart question integration"""
    
    def __init__(self):
        self.memory = get_session_memory()
        self.rag_llm_integrator = None
        logger.info("Smart Response Generator initialized")
    
    def set_llm_model(self, llm_model):
        """Set the LLM model for RAG-LLM integration"""
        try:
            from app.rag.llm_integration import get_rag_llm_integrator
            self.rag_llm_integrator = get_rag_llm_integrator(llm_model)
            logger.info(f"LLM model set for RAG-LLM integration. Integrator: {self.rag_llm_integrator is not None}")
        except Exception as e:
            logger.error(f"Failed to set LLM model: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.rag_llm_integrator = None
    
    def generate_response(self, 
                         user_message: str, 
                         rag_context: str, 
                         session_id: str,
                         conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Generate smart response with LLM-first approach and smart functions
        
        Args:
            user_message: User's current message
            rag_context: RAG search results (legacy parameter, kept for compatibility)
            session_id: Current session ID
            conversation_history: Previous conversation messages
            
        Returns:
            str: Smart LLM response with intelligent functions
        """
        try:
            # Get current session info
            session_info = self.memory.get_user_info(session_id)
            
            # If no RAG context provided, try to get it from RAG system
            if not rag_context or rag_context.strip() == "":
                try:
                    from app.rag.retriever import retrieve
                    # Get relevant RAG context for the user message
                    rag_results = retrieve(user_message, top_k=3)
                    if rag_results:
                        rag_context = "\n\n".join([
                            f"Source: {r.get('title', 'Unknown')}\n{r.get('content', '')[:300]}..."
                            for r in rag_results[:3]
                        ])
                    else:
                        rag_context = "No specific information found in knowledge base."
                except Exception as e:
                    logger.warning(f"Failed to get RAG context: {e}")
                    rag_context = "No specific information found in knowledge base."
            
            # Build the response
            response_parts = []
            
            # Import domain checker
            from app.utils.domain_checker import is_in_domain
            
            # Debug: Check if RAG-LLM integrator is available
            logger.info(f"RAG-LLM integrator available: {self.rag_llm_integrator is not None}")
            logger.info(f"User message: {user_message}")
            logger.info(f"RAG context: {rag_context[:100]}...")
            logger.info(f"Session info: {session_info.__dict__ if hasattr(session_info, '__dict__') else session_info}")
            
            # Clean Loop Implementation
            rag_results_count = len(rag_context) if rag_context else 0
            logger.info(f"RAG results count: {rag_results_count}")
            
            # Option 1: RAG has results - use them
            if rag_results_count > 0:
                logger.info("✅ RAG has results - using RAG + LLM")
                if self.rag_llm_integrator:
                    try:
                        result = self.rag_llm_integrator.process_query(
                            user_message=user_message,
                            session_info=session_info.__dict__ if hasattr(session_info, '__dict__') else session_info,
                            conversation_history=conversation_history,
                            top_k=3,
                            session_id=session_id
                        )
                        
                        if result.get('processing_successful') and result.get('llm_response'):
                            return result.get('llm_response')
                        else:
                            # Fallback to simple RAG response
                            return self._generate_simple_rag_response(user_message, rag_context)
                    except Exception as e:
                        logger.error(f"RAG-LLM processing failed: {e}")
                        return self._generate_simple_rag_response(user_message, rag_context)
                else:
                    return self._generate_simple_rag_response(user_message, rag_context)
            
            # Option 2: No RAG - check if in domain
            else:
                logger.info("❌ No RAG results - checking domain")
                domain_check = is_in_domain(user_message)
                logger.info(f"Domain check result: {domain_check}")
                
                if domain_check.get('in_domain', False):
                    logger.info("✅ In domain - using functions")
                    # Use functions to handle domain questions
                    return self._handle_domain_query_with_functions(
                        user_message, session_id, conversation_history, session_info
                    )
                else:
                    logger.info("❌ Out of domain - redirecting")
                    # Outside domain - redirect to better LLM
                    return self._generate_out_of_domain_response(domain_check)
            
        except Exception as e:
            logger.error(f"Error in smart response generation: {e}")
            return "I'm having technical difficulties. Please try again."

    def _generate_simple_rag_response(self, user_message: str, rag_context: List[Dict]) -> str:
        """Generate simple response when RAG has results but LLM integration fails"""
        try:
            # Use the first RAG result to generate a simple response
            if rag_context and len(rag_context) > 0:
                first_result = rag_context[0]
                content = first_result.get('content', '')
                title = first_result.get('title', '')
                
                return f"Based on the information I have: {content[:200]}... For more detailed guidance, please contact our team."
            else:
                return "I have some information about that. Please contact our team for detailed guidance."
        except Exception as e:
            logger.error(f"Error generating simple RAG response: {e}")
            return "I have information about that topic. Please contact our team for assistance."

    def _handle_domain_query_with_functions(self, user_message: str, session_id: str, 
                                          conversation_history: List[Dict], session_info: Any) -> str:
        """Handle domain queries using functions when RAG has no results"""
        try:
            logger.info("Handling domain query with functions")
            
            # Try to use function integrator if available
            if self.rag_llm_integrator:
                try:
                    result = self.rag_llm_integrator.process_query(
                        user_message=user_message,
                        session_info=session_info.__dict__ if hasattr(session_info, '__dict__') else session_info,
                        conversation_history=conversation_history,
                        top_k=0,  # No RAG results
                        session_id=session_id
                    )
                    
                    if result.get('processing_successful') and result.get('llm_response'):
                        return result.get('llm_response')
                    
                except Exception as e:
                    logger.error(f"Function processing failed: {e}")
            
            # Fallback to basic domain response
            return self._generate_basic_domain_response(user_message)
            
        except Exception as e:
            logger.error(f"Error handling domain query with functions: {e}")
            return self._generate_basic_domain_response(user_message)

    def _generate_basic_domain_response(self, user_message: str) -> str:
        """Generate basic response for domain queries"""
        message_lower = user_message.lower()
        
        # Check for specific patterns and provide appropriate responses
        if any(word in message_lower for word in ['contact', 'phone', 'number', 'call', 'reach']):
            return "I'd be happy to connect you with our team! Please provide your contact information (name, email, and phone number) so we can reach out to you with personalized guidance."
        
        elif any(word in message_lower for word in ['apply', 'application', 'process']):
            return "I can help you with the application process! To provide you with the most accurate guidance, could you share your contact details and let me know which country you're interested in studying in?"
        
        elif any(word in message_lower for word in ['requirements', 'documents', 'needed']):
            return "I can help you understand the requirements! To give you specific guidance, please share your contact information and tell me which country you're planning to study in."
        
        else:
            return "I can help you with student visa information! To provide personalized guidance, please share your contact details and let me know which country you're interested in."

    def _generate_out_of_domain_response(self, domain_check: Dict) -> str:
        """Generate response for out-of-domain queries"""
        confidence = domain_check.get('confidence', 0.0)
        reason = domain_check.get('reason', '')
        
        if confidence > 0.8:
            # High confidence out-of-domain
            return "I specialize in student visas for USA, UK, Australia, and South Korea. Your question appears to be outside my area of expertise. For general questions, I recommend using a general AI assistant like ChatGPT or Google's Gemini."
        else:
            # Lower confidence - try to redirect to student visa topics
            return "I specialize in student visa guidance for USA, UK, Australia, and South Korea. If you have questions about studying abroad, I'd be happy to help! Otherwise, for general questions, I recommend using a general AI assistant."

    def _create_tool_response_prompt(self, user_message: str, function_name: str, 
                                    function_result: Dict, conversation_history: List[Dict]) -> str:
        """Create a prompt for Gemini to generate a response using tool results"""
        try:
            prompt_parts = []
            
            # System context with policy rules
            prompt_parts.append("You are an AI assistant for AI Consultancy, specializing in student visas.")
            prompt_parts.append("A function has been executed successfully. Generate a natural, helpful response.")
            prompt_parts.append("")
            prompt_parts.append("SYSTEM POLICY RULES:")
            
            prompt_parts.append("2. Ask for lead fields only after you've helped OR user shows interest; ask 1-2 max with explicit opt-in")
            
            
            prompt_parts.append("5. If no KB match above threshold, say what's missing and ask a disambiguating question")
            prompt_parts.append("6. Be conversational and natural - don't be overly formal")
            prompt_parts.append("7. Keep responses concise and helpful")
            prompt_parts.append("")
            
            # User's original question
            prompt_parts.append(f"User Question: {user_message}")
            
            # Function context
            prompt_parts.append(f"Function Executed: {function_name}")
            
            # Function result
            if function_result.get('data'):
                prompt_parts.append(f"Function Result Data: {function_result['data']}")
            
            # Function message
            if function_result.get('message'):
                prompt_parts.append(f"Function Message: {function_result['message']}")
            
            # CRITICAL: Handle function failures gracefully
            if function_result.get('success') == False:
                prompt_parts.append("\n⚠️ FUNCTION FAILED - Generate helpful response:")
                prompt_parts.append("1. Acknowledge what the user asked for")
                prompt_parts.append("2. Explain why it couldn't be processed (briefly)")
                prompt_parts.append("3. Offer alternatives or supported options")
                prompt_parts.append("4. Keep the conversation flowing naturally")
                prompt_parts.append("5. Never leave the user with no information")
            
            # Conversation history (last 2 messages for context)
            if conversation_history:
                prompt_parts.append("\nRecent Conversation:")
                for msg in conversation_history[-2:]:
                    content = msg.get('content', msg.get('user_message', msg.get('user_input', '')))
                    prompt_parts.append(f"- User: {content}")
            
            # Instructions based on function type


            elif function_name == "detect_and_save_contact_info":
                prompt_parts.append("\nInstructions:")
                prompt_parts.append("1. Acknowledge what information was automatically detected and saved")
                prompt_parts.append("2. Confirm the information was recorded correctly")
                prompt_parts.append("3. Continue helping with the user's questions naturally")
                prompt_parts.append("4. Be brief and conversational")
                

            else:
                prompt_parts.append("\nInstructions:")
                prompt_parts.append("1. Acknowledge the function was successful")
                prompt_parts.append("2. Continue helping the user naturally")
                prompt_parts.append("3. Keep the conversation flowing")
            
            return "\n".join(prompt_parts)
            
        except Exception as e:
            self.logger.error(f"Error creating tool response prompt: {e}")
            # Fallback prompt
            return f"User asked: {user_message}\n\nFunction {function_name} executed successfully. Generate a natural response."

    def _generate_helpful_response(self, user_message: str, session_info) -> str:
        """DEPRECATED: This method is no longer used - LLM handles everything"""
        # This method is deprecated - LLM now handles all responses
        return "I understand you're interested in UK student visa for bachelor's degree. Let me help you with that information. Email: info@ai consultancyeducation.com | Phone: +1-234-567-8900"
    
    def _get_question_intro(self, session_info) -> str:
        """DEPRECATED: This method is no longer used - LLM handles everything"""
        # This method is deprecated - LLM now handles all follow-ups
        return ""
    
    def _should_ask_question_smart(self, session_info, rag_context: str, user_message: str) -> bool:
        """DEPRECATED: This method is no longer used - LLM handles everything"""
        # This method is deprecated - LLM now decides when to ask questions
        return False
    
    def get_response_metadata(self, session_id: str) -> Dict[str, Any]:
        """Get metadata about the response generation"""
        session_info = self.memory.get_user_info(session_id)
        return {
            "session_id": session_id,
            "user_profile_complete": session_info.is_complete(),
            "conversation_summary": session_info.conversation_summary,
            "exchange_count": session_info.exchange_count
        }

# Global instance
_smart_response_generator = SmartResponseGenerator()

def get_smart_response_generator() -> SmartResponseGenerator:
    """Get global smart response generator instance"""
    return _smart_response_generator
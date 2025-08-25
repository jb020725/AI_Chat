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
            
            # Debug: Check if RAG-LLM integrator is available
            logger.info(f"RAG-LLM integrator available: {self.rag_llm_integrator is not None}")
            logger.info(f"User message: {user_message}")
            logger.info(f"RAG context: {rag_context[:100]}...")
            logger.info(f"Session info: {session_info.__dict__ if hasattr(session_info, '__dict__') else session_info}")
            
            # Use RAG-LLM integration if available
            if self.rag_llm_integrator:
                logger.info("Using RAG-LLM integration for response generation")
                print("🔍 [DEBUG] RAG-LLM integrator is available - proceeding with LLM generation")
                try:
                    # Process query through RAG-LLM pipeline with smart functions
                    result = self.rag_llm_integrator.process_query(
                        user_message=user_message,
                        session_info=session_info.__dict__ if hasattr(session_info, '__dict__') else session_info,
                        conversation_history=conversation_history,
                        top_k=3,
                        session_id=session_id
                    )
                    
                    print("🔍 [DEBUG] === RAG-LLM RESULT DEBUG ===")
                    print(f"🔍 [DEBUG] Full result: {result}")
                    print(f"🔍 [DEBUG] Result keys: {list(result.keys()) if result else 'None'}")
                    print(f"🔍 [DEBUG] Processing successful: {result.get('processing_successful')}")
                    print(f"🔍 [DEBUG] LLM response key exists: {'llm_response' in result}")
                    print(f"🔍 [DEBUG] LLM response value: {result.get('llm_response')}")
                    print(f"🔍 [DEBUG] Metadata: {result.get('metadata', {})}")
                    
                    logger.info(f"=== RAG-LLM RESULT DEBUG ===")
                    logger.info(f"Full result: {result}")
                    logger.info(f"Result keys: {list(result.keys()) if result else 'None'}")
                    logger.info(f"Processing successful: {result.get('processing_successful')}")
                    logger.info(f"LLM response key exists: {'llm_response' in result}")
                    logger.info(f"LLM response value: {result.get('llm_response')}")
                    logger.info(f"Metadata: {result.get('metadata', {})}")
                    
                    if result.get('processing_successful'):
                        print("✅ [DEBUG] RAG-LLM processing was successful - now validating LLM response")
                        # Add LLM-generated response (which now includes intelligent follow-ups)
                        llm_response = result.get('llm_response', '')
                        print(f"🔍 [DEBUG] === LLM RESPONSE VALIDATION DEBUG ===")
                        print(f"🔍 [DEBUG] Raw LLM response: '{llm_response}'")
                        print(f"🔍 [DEBUG] LLM response type: {type(llm_response)}")
                        print(f"🔍 [DEBUG] LLM response length: {len(llm_response) if llm_response else 0}")
                        print(f"🔍 [DEBUG] LLM response is None: {llm_response is None}")
                        print(f"🔍 [DEBUG] LLM response is empty string: {llm_response == ''}")
                        
                        logger.info(f"=== LLM RESPONSE VALIDATION DEBUG ===")
                        logger.info(f"Raw LLM response: '{llm_response}'")
                        logger.info(f"LLM response type: {type(llm_response)}")
                        logger.info(f"LLM response length: {len(llm_response) if llm_response else 0}")
                        logger.info(f"LLM response is None: {llm_response is None}")
                        logger.info(f"LLM response is empty string: {llm_response == ''}")
                        
                        if llm_response:
                            stripped_response = llm_response.strip()
                            logger.info(f"Stripped response: '{stripped_response}'")
                            logger.info(f"Stripped length: {len(stripped_response)}")
                        else:
                            stripped_response = ""
                            logger.info(f"Stripped response: '{stripped_response}'")
                            logger.info(f"Stripped length: {len(stripped_response)}")
                        
                        # Much more lenient validation - accept any reasonable LLM response
                        print(f"🔍 [DEBUG] Final validation check:")
                        print(f"🔍 [DEBUG] - llm_response exists: {bool(llm_response)}")
                        print(f"🔍 [DEBUG] - stripped length: {len(stripped_response)}")
                        print(f"🔍 [DEBUG] - validation condition: {llm_response and len(stripped_response) > 0}")
                        
                        # Check if we have a valid LLM response OR successful function calls
                        has_valid_response = llm_response and len(stripped_response) > 0
                        has_function_calls = result.get('function_calls') and len(result['function_calls']) > 0
                        
                        if has_valid_response:
                            print("✅ [DEBUG] SUCCESS: LLM response validation passed - using LLM response")
                            response_parts.append(llm_response)
                            logger.info("✅ SUCCESS: Added LLM-generated response to response parts")
                            logger.info(f"   - Response length: {len(stripped_response)} characters")
                            
                            # CRITICAL: If LLM response is successful, return ONLY that response
                            # Do NOT fall back to templates or add anything else
                            final_response = llm_response
                            logger.info(f"Returning ONLY LLM response: {len(final_response)} characters")
                            return final_response
                        elif has_function_calls:
                            print("✅ [DEBUG] SUCCESS: Function calls executed successfully")
                            logger.info("✅ SUCCESS: Function calls executed successfully")
                            
                            # Check if we have a valid LLM response from tool response generation
                            if llm_response and len(llm_response.strip()) > 0:
                                print("✅ [DEBUG] SUCCESS: Tool response generated - using LLM response")
                                logger.info("✅ SUCCESS: Tool response generated - using LLM response")
                                logger.info(f"   - Tool response length: {len(llm_response)} characters")
                                
                                # Return the tool response generated by Gemini
                                final_response = llm_response
                                logger.info(f"Returning tool response: {len(final_response)} characters")
                                return final_response
                            else:
                                # No tool response generated - let the system handle it naturally
                                logger.info("Function calls executed but no tool response generated - allowing natural flow")
                                return ""
                        else:
                            print("❌ [DEBUG] FAILED: No valid LLM response or function calls found")
                            print(f"❌ [DEBUG] - llm_response exists: {bool(llm_response)}")
                            print(f"❌ [DEBUG] - stripped length: {len(stripped_response)}")
                            print(f"❌ [DEBUG] - function_calls count: {len(result.get('function_calls', []))}")
                            print(f"❌ [DEBUG] - Final decision: SIMPLE FALLBACK")
                            logger.warning(f"❌ FAILED: No valid LLM response or function calls found")
                            logger.warning(f"   - llm_response exists: {bool(llm_response)}")
                            logger.warning(f"   - stripped length: {len(stripped_response)}")
                            logger.warning(f"   - function_calls count: {len(result.get('function_calls', []))}")
                            logger.warning(f"   - Final decision: SIMPLE FALLBACK")
                            # Simple fallback - only when LLM fails
                            return "I understand you're interested in UK student visa for bachelor's degree. Let me help you with that information. Email: info@aiconsultancy.com | Phone: +1-234-567-8900"
                    else:
                        # LLM processing failed - simple fallback
                        print("❌ [DEBUG] RAG-LLM processing failed (processing_successful=False) - using simple fallback")
                        logger.warning("RAG-LLM processing failed, using simple fallback")
                        return "I understand you're interested in UK student visa for bachelor's degree. Let me help you with that information. Email: info@aiconsultancy.com | Phone: +1-234-567-8900"
                        
                except Exception as e:
                    print(f"💥 [DEBUG] RAG-LLM integration EXCEPTION: {e}")
                    print(f"💥 [DEBUG] Using simple fallback")
                    logger.error(f"RAG-LLM integration failed: {e}, using simple fallback")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return "I understand you're interested in UK student visa for bachelor's degree. Let me help you with that information. Email: info@aiconsultancy.com | Phone: +1-234-567-8900"
            else:
                print("⚠️ [DEBUG] No RAG-LLM integrator available - using simple fallback")
                logger.warning("No RAG-LLM integrator available, using simple fallback")
                return "I understand you're interested in UK student visa for bachelor's degree. Let me help you with that information. Email: info@aiconsultancy.com | Phone: +1-234-567-8900"
            
        except Exception as e:
            logger.error(f"Error generating smart response: {e}")
            # Simple fallback - no templates
            return "I understand you're interested in UK student visa for bachelor's degree. Let me help you with that information. Email: info@aiconsultancy.com | Phone: +1-234-567-8900"

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
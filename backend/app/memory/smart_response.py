"""
Smart Response System for Clean Function-Calling Structure

Manages intelligent response generation and memory integration:
- Function calling integration
- Session memory management
- Natural response generation
- No RAG integration (disabled)
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.memory.session_memory import get_session_memory

logger = logging.getLogger(__name__)

class SmartResponse:
    """Manages smart response generation and memory integration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session_memory = get_session_memory()
        self.function_integrator = None
        self.llm_model = None
        
    def set_llm_model(self, llm_model):
        """Set the LLM model for function calling only (RAG disabled)"""
        try:
            self.llm_model = llm_model
            # Import here to avoid circular imports
            from app.functions.function_integrator import FunctionIntegrator
            self.function_integrator = FunctionIntegrator(llm_model)
            logger.info(f"LLM model set for function calling. Integrator: {self.function_integrator is not None}")
        except Exception as e:
            logger.error(f"Failed to set LLM model for function calling: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.function_integrator = None
    
    def generate_smart_response(self, user_message: str, session_id: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Generate intelligent response using function calling and memory"""
        try:
            if not self.function_integrator:
                return {
                    "response": "I'm having technical difficulties. Please try again.",
                    "success": False,
                    "error": "Function integrator not available"
                }
            
            # Create function calling prompt
            prompt = self.function_integrator.create_function_calling_prompt(
                user_message, session_id, conversation_history
            )
            
            # Call LLM with function calling
            try:
                response = self.llm_model.generate_content(
                    prompt,
                    tools=[{"function_declarations": self.function_integrator.get_function_declarations()}]
                )
                
                # Process function calls if any
                result = self._process_function_response(response, user_message, session_id, conversation_history)
                return result
                
            except Exception as e:
                logger.error(f"Error calling LLM with functions: {e}")
                # Fallback to basic response
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
    
    def _process_function_response(self, response, user_message: str, session_id: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Process LLM response and execute function calls"""
        try:
            # Initialize result
            result = {
                "response": "",
                "function_calls": [],
                "success": True
            }
            
            # Check for function calls
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            # Execute function call
                            function_call = part.function_call
                            function_name = getattr(function_call, 'name', '')
                            function_args = getattr(function_call, 'args', {})
                            
                            if function_name:
                                logger.info(f"Executing function: {function_name} with args: {function_args}")
                                
                                # Execute the function
                                function_result = self.function_integrator.execute_function_call(
                                    function_name, session_id, **function_args
                                )
                                
                                # Add to results
                                result["function_calls"].append({
                                    "function_name": function_name,
                                    "arguments": function_args,
                                    "result": function_result
                                })
                                
                                # Generate natural response
                                if function_result.get('success'):
                                    natural_response = self._generate_natural_response(
                                        user_message, function_name, function_result, conversation_history
                                    )
                                    result["response"] = natural_response
                                else:
                                    # Handle function failure
                                    failure_response = self._generate_failure_response(
                                        user_message, function_name, function_result
                                    )
                                    result["response"] = failure_response
                                
                                return result
            
            # No function calls - generate basic response
            if hasattr(response, 'text'):
                result["response"] = response.text
            else:
                result["response"] = "I understand your question. Let me help you with that."
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing function response: {e}")
            return {
                "response": "I encountered an error processing the response. Please try again.",
                "success": False,
                "error": str(e)
            }
    
    def _generate_natural_response(self, user_message: str, function_name: str, function_result: Dict, conversation_history: List[Dict]) -> str:
        """Generate natural response after successful function execution"""
        try:
            if not self.function_integrator:
                return "Function executed successfully. How can I help you further?"
            
            # Create natural response prompt
            prompt = self.function_integrator.create_natural_response_prompt(
                user_message, function_name, function_result
            )
            
            # Generate response
            response = self.llm_model.generate_content(prompt)
            if response and hasattr(response, 'text'):
                return response.text
            else:
                return "Function completed successfully. How can I assist you further?"
                
        except Exception as e:
            logger.error(f"Error generating natural response: {e}")
            return "Function executed successfully. How can I help you further?"
    
    def _generate_failure_response(self, user_message: str, function_name: str, function_result: Dict) -> str:
        """Generate helpful response when function fails"""
        try:
            if not self.function_integrator:
                return "I encountered an issue. Please try again or ask a different question."
            
            # Create failure response prompt
            prompt = self.function_integrator.create_failure_response_prompt(
                user_message, function_name, function_result
            )
            
            # Generate response
            response = self.llm_model.generate_content(prompt)
            if response and hasattr(response, 'text'):
                return response.text
            else:
                return "I encountered an issue. Please try again or ask a different question."
                
        except Exception as e:
            logger.error(f"Error generating failure response: {e}")
            return "I encountered an issue. Please try again or ask a different question."
    
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
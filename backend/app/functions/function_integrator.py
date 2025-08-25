"""
Function Integrator for Gemini Native Function Calling

Integrates function calling with the existing LLM pipeline:
- Connects Gemini function calling with our handlers
- Processes function calls and responses
- Integrates with RAG-LLM pipeline
"""

import logging
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from .function_definitions import FUNCTIONS
from .function_handlers import function_handler
from ..memory.session_memory import SessionMemory
import logging
import time

logger = logging.getLogger(__name__)

class FunctionIntegrator:
    """Integrates Gemini function calling with custom function handlers"""
    
    def __init__(self, llm_model=None):
        self.llm_model = llm_model
        self.logger = logging.getLogger(__name__)
        self.session_memory = SessionMemory()
        
        # Get all function declarations from function_definitions.py
        self.function_declarations = FUNCTIONS
        
        # Debug: Log what functions we loaded
        self.logger.info(f"FunctionIntegrator initialized with {len(self.function_declarations)} functions:")
        for func in self.function_declarations:
            self.logger.info(f"  - {func['name']}: {func['description'][:50]}...")
        
        # Validate function schemas
        self._validate_function_schemas()
        
    def set_llm_model(self, llm_model):
        """Set the LLM model for function calling"""
        self.llm_model = llm_model
        self.logger.info("LLM model set for function calling")
        
    def process_with_functions(self, 
                             user_message: str,
                             session_id: str,
                             rag_context: List[Dict[str, Any]] = None,
                             conversation_history: List[Dict[str, str]] = None,
                             session_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process user message with function calling enabled
        
        Args:
            user_message: User's input message
            session_id: Current session ID
            rag_context: RAG search results
            conversation_history: Previous conversation
            session_info: Current session information (country, email, etc.)
            
        Returns:
            Dict with LLM response and function call results
        """
        try:
            if not self.llm_model:
                self.logger.warning("No LLM model available for function calling")
                return {
                    "llm_response": "I'm having technical difficulties. Please try again.",
                    "function_calls": [],
                    "processing_successful": False
                }
            
            # Build prompt for function calling
            prompt = self._build_function_prompt(
                user_message, conversation_history, session_info
            )
            
            self.logger.info(f"Processing with function calling for session {session_id}")
            
            # Call Gemini with function calling
            try:
                # Try the new format first
                response = self.llm_model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        top_p=0.8,
                        top_k=40
                    ),
                    tools=self.function_declarations
                )
            except Exception as e:
                self.logger.warning(f"New function calling format failed: {e}")
                # Fallback to basic generation without function calling
                self.logger.info("Falling back to basic generation without function calling")
                try:
                    response = self.llm_model.generate_content(prompt)
                    # Mark that no functions were called
                    response._no_function_calling = True
                except Exception as fallback_error:
                    self.logger.error(f"Fallback generation also failed: {fallback_error}")
                    # Return a basic response
                    return {
                        "llm_response": "I am unable to process request for this question, please move on if you have any other questions.",
                        "function_calls": [],
                        "processing_successful": False,
                        "error": str(fallback_error)
                    }
            
            # Debug: Log the raw response structure
            self.logger.info(f"Raw response type: {type(response)}")
            self.logger.info(f"Raw response attributes: {dir(response)}")
            self.logger.info(f"Response has candidates: {hasattr(response, 'candidates')}")
            
            # Check if function calling failed and we're using fallback
            if hasattr(response, '_no_function_calling'):
                self.logger.info("Using fallback response processing (no function calling)")
                
                # Try to parse function calls from the text response
                try:
                    # Check if response was filtered/blocked
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 12:
                            self.logger.warning("Response was filtered by Gemini API (finish_reason=12)")
                            llm_text = "I am unable to process request for this question, please move on if you have any other questions."
                        else:
                            llm_text = response.text if hasattr(response, 'text') else str(response)
                    else:
                        llm_text = response.text if hasattr(response, 'text') else str(response)
                except Exception as text_error:
                    self.logger.error(f"Failed to get response text: {text_error}")
                    llm_text = "I am unable to process request for this question, please move on if you have any other questions."
                
                parsed_functions = self._parse_function_calls_from_text(llm_text)
                
                if parsed_functions:
                    self.logger.info(f"Found {len(parsed_functions)} function calls in text response")
                    # Execute the parsed functions
                    executed_functions = []
                    final_response = llm_text
                    
                    for func_call in parsed_functions:
                        try:
                            result = self._execute_parsed_function(func_call, session_id)
                            executed_functions.append(result)
                            
                            # If function executed successfully, generate a natural response
                            if result.get('success') and result.get('result', {}).get('success'):
                                function_result = result.get('result', {})
                                function_data = function_result.get('data', {})
                                
                                # Check if we need to ask for contact info
                                ask_for_contact = function_data.get('ask_for_contact', False)
                                contact_message = function_data.get('contact_message', '')
                                
                                if ask_for_contact and contact_message:
                                    final_response = contact_message
                                else:
                                    # Generate natural response for successful function
                                    natural_prompt = f"""You are a helpful visa consultant for AI Consultancy.

A function was just executed successfully: {func_call.get('function_name')}

User's original question: {user_message}

Function result: {function_result.get('message', 'Success')}

Please provide a natural, helpful response to the user based on the function result. Be conversational and informative."""
                                    
                                    try:
                                        natural_response = self.llm_model.generate_content(natural_prompt)
                                        if natural_response and natural_response.text:
                                            final_response = natural_response.text
                                    except Exception as resp_error:
                                        self.logger.error(f"Error generating natural response: {resp_error}")
                                        
                        except Exception as e:
                            self.logger.error(f"Failed to execute parsed function {func_call}: {e}")
                    
                    return {
                        "llm_response": final_response,
                        "function_calls": executed_functions,
                        "processing_successful": True,
                        "fallback_mode": True,
                        "parsed_functions": True
                    }
                
                return {
                    "llm_response": llm_text,
                    "function_calls": [],
                    "processing_successful": True,
                    "fallback_mode": True
                }
            
            if hasattr(response, 'candidates') and response.candidates:
                self.logger.info(f"First candidate type: {type(response.candidates[0])}")
                self.logger.info(f"First candidate attributes: {dir(response.candidates[0])}")
            
            # Process the response
            result = self._process_function_response(response, user_message, conversation_history, session_id)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in function calling: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                "llm_response": "I am unable to process request for this question, please move on if you have any other questions.",
                "function_calls": [],
                "processing_successful": False,
                "error": str(e)
            }
    
    def _build_function_prompt(self, user_message: str, conversation_history: List[Dict], user_info: Dict = None) -> str:
        """Build the function calling prompt for Gemini"""
        try:
            prompt_parts = []
            
            # System context
            prompt_parts.append("You are an AI assistant for AI Consultancy, specializing in student visas.")
            prompt_parts.append("You have access to several functions to help users effectively.")
            prompt_parts.append("")
            
            # Function descriptions
            prompt_parts.append("AVAILABLE FUNCTIONS:")
            prompt_parts.append("")
            prompt_parts.append("[ALERT] FUNCTION CALLING RULES:")
    
            prompt_parts.append("- If user shows serious intent (wants to apply, needs guidance) OR shows urgency (critical, immediate help), call handle_contact_request")
            prompt_parts.append("- If RAG has no results, call define_response_strategy to determine how to respond")
    
            prompt_parts.append("")
            
            prompt_parts.append("1. handle_contact_request(user_query, conversation_context, detected_interests?) - Smart contact handler for both lead opportunities (serious intent) and urgent contact needs (critical, immediate help). Routes appropriately based on urgency level.")
            prompt_parts.append("2. detect_and_save_contact_info(user_query, conversation_context, extraction_mode?) - Automatically detect, extract, and save contact information from user messages. Use when user provides any contact details.")
            prompt_parts.append("3. define_response_strategy(user_query, rag_results_count, session_memory?) - Define response strategy when RAG has no results. Use when RAG returns 0 results.")
            prompt_parts.append("")
            

            prompt_parts.append("")
            
    
            prompt_parts.append("")
            
            prompt_parts.append("CRITICAL RULES:")
    
            prompt_parts.append("- MANDATORY: When user shows serious intent (wants to apply, needs guidance) OR shows urgency (critical, immediate help), call handle_contact_request")
            prompt_parts.append("- MANDATORY: When user provides ANY contact information (name, email, phone, country, intake), call detect_and_save_contact_info to automatically extract and save it")
            prompt_parts.append("- MANDATORY: If RAG has no results, call define_response_strategy to determine how to respond")
    
            prompt_parts.append("- RESPONSE STRATEGIES: Follow the strategy defined by define_response_strategy function exactly")
            prompt_parts.append("- LEAD GENERATION: Always detect opportunities to collect contact information when users show serious intent")
            prompt_parts.append("")
            
            # User message
            prompt_parts.append(f"USER MESSAGE: {user_message}")
            prompt_parts.append("")
            
            # Check if contact info is provided and add explicit instruction
            message_lower = user_message.lower()
            has_email = "@" in user_message
            has_name = any(phrase in message_lower for phrase in ["my name is", "i'm", "i am", "call me", "name is", "name's"])
            has_phone = any(char.isdigit() for char in user_message) and len([c for c in user_message if c.isdigit()]) >= 7
            
            # More aggressive pattern matching for contact info
            if "email" in message_lower or "phone" in message_lower or "contact" in message_lower:
                has_email = True
                has_phone = True
            
            if has_email or has_name or has_phone:
                prompt_parts.append("[ALERT] CONTACT INFO DETECTED: Call detect_and_save_contact_info function to automatically extract and save the information!")
                prompt_parts.append("")
            
            # Conversation history
            if conversation_history:
                prompt_parts.append("CONVERSATION HISTORY:")
                for i, msg in enumerate(conversation_history[-3:], 1):
                    user_msg = msg.get('user_input') or msg.get('user_message', 'Unknown')
                    bot_msg = msg.get('bot_response', 'Unknown')
                    prompt_parts.append(f"{i}. User: {user_msg}")
                    prompt_parts.append(f"   Assistant: {bot_msg}")
                prompt_parts.append("")
            
            # User info context
            if user_info:
                prompt_parts.append("USER CONTEXT:")
                if user_info.get('country'):
                    prompt_parts.append(f"- Target Country: {user_info['country']}")
                if user_info.get('name'):
                    prompt_parts.append(f"- Name: {user_info['name']}")
                if user_info.get('email'):
                    prompt_parts.append(f"- Email: {user_info['email']}")
                if user_info.get('phone'):
                    prompt_parts.append(f"- Phone: {user_info['phone']}")
                if user_info.get('intake'):
                    prompt_parts.append(f"- Intake: {user_info['intake']}")
                prompt_parts.append("")
            
            prompt_parts.append("INSTRUCTIONS:")
            prompt_parts.append("1. Analyze the user's message and conversation context")
            prompt_parts.append("2. Determine if you need to call any functions")
            prompt_parts.append("3. If calling functions, provide ALL required parameters")
            prompt_parts.append("4. Be natural and conversational in your response")
            prompt_parts.append("5. Use functions to provide accurate information and save leads when appropriate")
            prompt_parts.append("")
            prompt_parts.append("COUNTRY EXTRACTION EXAMPLES:")
            prompt_parts.append("- 'i wanna go to uk' → country: 'uk'")
            prompt_parts.append("- 'USA student visa' → country: 'usa'")
            prompt_parts.append("- 'Australia requirements' → country: 'australia'")
            prompt_parts.append("- 'South Korea process' → country: 'south_korea'")
            prompt_parts.append("")
            prompt_parts.append("RESPOND WITH:")
            prompt_parts.append("- Function calls if needed (with proper parameters)")
            prompt_parts.append("- Natural, helpful response to the user")
            prompt_parts.append("- Continue the conversation naturally")
            
            return "\n".join(prompt_parts)
            
        except Exception as e:
            self.logger.error(f"Error building function prompt: {e}")
            return f"User message: {user_message}\n\nPlease help the user with their student visa questions."
    
    def _process_function_response(self, response, user_message: str, conversation_history: List[Dict], session_id: str) -> Dict[str, Any]:
        """Process Gemini response and execute function calls"""
        
        try:
            # [DEBUG] DETAILED GEMINI RESPONSE DEBUGGING
            self.logger.info("=" * 80)
            self.logger.info("[DEBUG] GEMINI RESPONSE STRUCTURE DEBUG")
            self.logger.info("=" * 80)
            self.logger.info(f"Raw response type: {type(response)}")
            self.logger.info(f"Raw response dir: {dir(response)}")
            
            # Try to get text - this fails when there's a function call
            try:
                llm_text = response.text if hasattr(response, 'text') else ""
                self.logger.info(f"[PASS] LLM text extracted: '{llm_text[:100]}...'")
            except Exception as text_error:
                self.logger.info(f"[FAIL] Could not get text (probably function call): {text_error}")
                llm_text = ""
            
            # Check candidates structure
            if hasattr(response, 'candidates'):
                self.logger.info(f"[PASS] Has candidates: {len(response.candidates)}")
                
                for cand_idx, candidate in enumerate(response.candidates):
                    self.logger.info(f"--- Candidate {cand_idx} ---")
                    self.logger.info(f"Candidate type: {type(candidate)}")
                    self.logger.info(f"Candidate dir: {dir(candidate)}")
                    
                    if hasattr(candidate, 'content'):
                        self.logger.info(f"[PASS] Candidate has content")
                        self.logger.info(f"Content type: {type(candidate.content)}")
                        self.logger.info(f"Content dir: {dir(candidate.content)}")
                        
                        if hasattr(candidate.content, 'parts'):
                            self.logger.info(f"[PASS] Content has parts: {len(candidate.content.parts)}")
                            
                            for part_idx, part in enumerate(candidate.content.parts):
                                self.logger.info(f"--- Part {part_idx} ---")
                                self.logger.info(f"Part type: {type(part)}")
                                self.logger.info(f"Part dir: {dir(part)}")
                                
                                # Check all possible attributes
                                for attr in ['text', 'function_call', 'function_response']:
                                    if hasattr(part, attr):
                                        attr_value = getattr(part, attr)
                                        self.logger.info(f"[PASS] Part has {attr}: {attr_value}")
                                        
                                        # If it's function_call, dig deeper
                                        if attr == 'function_call' and attr_value:
                                            self.logger.info(f"[FOUND] FUNCTION CALL FOUND!")
                                            self.logger.info(f"Function call type: {type(attr_value)}")
                                            self.logger.info(f"Function call dir: {dir(attr_value)}")
                                            
                                            # Try to access name and args
                                            for fc_attr in ['name', 'args', 'arguments']:
                                                if hasattr(attr_value, fc_attr):
                                                    fc_value = getattr(attr_value, fc_attr)
                                                    self.logger.info(f"[PASS] Function call has {fc_attr}: {fc_value}")
                                    else:
                                        self.logger.info(f"[FAIL] Part does not have {attr}")
                        else:
                            self.logger.info(f"[FAIL] Content does not have parts")
                    else:
                        self.logger.info(f"[FAIL] Candidate does not have content")
            else:
                self.logger.info(f"[FAIL] Response does not have candidates")
            
            self.logger.info("=" * 80)
            self.logger.info("[DEBUG] END GEMINI RESPONSE DEBUG")
            self.logger.info("=" * 80)
            
            # Extract LLM response text (safely)
            llm_response = llm_text
            
            self.logger.info(f"Processing function response for session {session_id}")
            self.logger.info(f"LLM response: {llm_response[:200]}...")
            
            # Initialize result
            result = {
                "llm_response": llm_response,
                "function_calls": [],
                "processing_successful": True
            }
            
            # Process function calls if any
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    self.logger.info(f"Found {len(candidate.content.parts)} content parts")
                    for i, part in enumerate(candidate.content.parts):
                        self.logger.info(f"Processing part {i}: {type(part)}")
                        self.logger.info(f"Part {i} attributes: {dir(part)}")
                        self.logger.info(f"Part {i} content: {part}")
                        
                        # Check if this part has a function call
                        if hasattr(part, 'function_call') and part.function_call:
                            try:
                                function_call = part.function_call
                                self.logger.info(f"Function call detected: {function_call}")
                                
                                # Try to access function call properties safely
                                function_name = getattr(function_call, 'name', None)
                                function_args = getattr(function_call, 'args', {})
                                
                                # Validate function call
                                if not function_name:
                                    self.logger.warning("Function call detected but no name found")
                                    continue
                                    
                                # Validate function exists
                                if not hasattr(function_handler, f'handle_{function_name}'):
                                    self.logger.error(f"Function handler not found for: {function_name}")
                                    continue
                                
                                # Validate arguments and convert protobuf to dict
                                if function_args and not isinstance(function_args, dict):
                                    self.logger.warning(f"Function args not a dict: {type(function_args)}")
                                    function_args = self._normalize_args(function_args)
                                    self.logger.info(f"Normalized args to dict: {function_args}")
                                
                                self.logger.info(f"Executing function: {function_name} with args: {function_args}")
                            
                                # Execute the function
                                function_result = function_handler.execute_function(
                                    function_name,
                                    session_id,
                                    **function_args
                                )
                                
                                # Validate function result
                                if not isinstance(function_result, dict):
                                    self.logger.error(f"Function {function_name} returned invalid result type: {type(function_result)}")
                                    function_result = {"success": False, "message": "Invalid function result", "data": None}
                                
                                # Add to results
                                result["function_calls"].append({
                                    "function_name": function_name,
                                    "arguments": function_args,
                                    "result": function_result
                                })
                                
                                # Sync tool results back to session memory for lead capture
                                if function_name == "detect_and_save_contact_info" and function_result.get("success"):
                                    try:
                                        slots = function_result.get("data", {})
                                        if slots:
                                            self.session_memory.update_session(session_id, {
                                                k: v for k, v in slots.items() 
                                                if k in ("name", "email", "phone", "preferred_intake", "target_country")
                                            })
                                            self.logger.info(f"[PASS] Synced {function_name} results to session memory: {list(slots.keys())}")
                                    except Exception as sync_error:
                                        self.logger.warning(f"Failed to sync {function_name} results: {sync_error}")
                                
                                self.logger.info(f"Function {function_name} executed successfully: {function_result.get('success', False)}")
                                
                                # After function execution, generate a natural response using the main system prompt
                                if function_result.get('success', False):
                                    self.logger.info(f"Function {function_name} succeeded - generating natural response")
                                    
                                    # Check if we need to ask for contact info
                                    function_data = function_result.get('data', {})
                                    ask_for_contact = function_data.get('ask_for_contact', False)
                                    contact_message = function_data.get('contact_message', '')
                                    
                                    if ask_for_contact and contact_message:
                                        # Use the pre-defined contact message
                                        result["llm_response"] = contact_message
                                        self.logger.info(f"Using contact message: {contact_message}")
                                        # Skip natural response generation since we have a specific message
                                        continue
                                    
                                    # Create a simple, natural prompt for the LLM to respond
                                    natural_prompt = f"""You are a helpful visa consultant for AI Consultancy.

A function was just executed successfully: {function_name}

User's original question: {user_message}

Function result: {function_result.get('message', 'Success')}

Please provide a natural, helpful response to the user based on the function result. Be conversational and informative."""
                                    
                                    try:
                                        # Generate natural response
                                        natural_response = self.llm_model.generate_content(natural_prompt)
                                        if natural_response and natural_response.text:
                                            result["llm_response"] = natural_response.text
                                            self.logger.info(f"Generated natural response: {len(natural_response.text)} chars")
                                        else:
                                            self.logger.warning(f"Natural response generation failed")
                                    except Exception as resp_error:
                                        self.logger.error(f"Error generating natural response: {resp_error}")
                                else:
                                    self.logger.warning(f"Function {function_name} failed: {function_result.get('message', 'Unknown error')}")
                                    
                                    # Generate graceful response for failed functions
                                    failure_prompt = f"""You are a helpful visa consultant for AI Consultancy.

A function failed to execute: {function_name}

User's original question: {user_message}

Function error: {function_result.get('message', 'Unknown error')}

Please provide a helpful response that:
1. Acknowledges the issue politely
2. Offers alternatives when possible
3. Stays helpful and professional

For example, if someone asks about an unsupported country, say: "I'm sorry, but I don't have specific information about that country's student visas. However, I can help you with student visas for USA, UK, Australia, and South Korea. Which of these countries interests you?"""

                                    try:
                                        # Generate failure response
                                        failure_response = self.llm_model.generate_content(failure_prompt)
                                        if failure_response and failure_response.text:
                                            result["llm_response"] = failure_response.text
                                            self.logger.info(f"Generated failure response: {len(failure_response.text)} chars")
                                        else:
                                            self.logger.warning(f"Failure response generation failed")
                                    except Exception as fail_error:
                                        self.logger.error(f"Error generating failure response: {fail_error}")
                                    
                            except Exception as func_error:
                                self.logger.error(f"Error processing function call: {func_error}")
                                # Add failed function call to results for debugging
                                result["function_calls"].append({
                                    "function_name": function_name if 'function_name' in locals() else "unknown",
                                    "arguments": function_args if 'function_args' in locals() else {},
                                    "result": {"success": False, "message": f"Error: {str(func_error)}", "data": None}
                                })
                        else:
                            self.logger.info(f"Part {i} is text content, not a function call")
                else:
                    self.logger.info("No content parts found in candidate")
            else:
                self.logger.info("No candidates found in response")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing function response: {e}")
            return {
                "llm_response": llm_response if 'llm_response' in locals() else "Error processing response",
                "function_calls": [],
                "processing_successful": False,
                "error": str(e)
            }
    
    def _parse_function_calls_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse function calls from LLM text response"""
        import re
        
        function_calls = []
        
        # Look for function call patterns in the text
        # Pattern: function_name(param1="value1", param2="value2")
        pattern = r'(\w+)\(([^)]+)\)'
        
        matches = re.findall(pattern, text)
        
        for func_name, params_str in matches:
            try:
                # Parse parameters
                params = {}
                if params_str.strip():
                    # Split by comma and parse each parameter
                    param_parts = params_str.split(',')
                    for part in param_parts:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')
                            
                            # Convert value types
                            if value.lower() in ['true', 'false']:
                                value = value.lower() == 'true'
                            elif value.isdigit():
                                value = int(value)
                            elif value.startswith('{') and value.endswith('}'):
                                # Try to parse as dict
                                try:
                                    import ast
                                    value = ast.literal_eval(value)
                                except:
                                    pass
                            
                            params[key] = value
                
                function_calls.append({
                    "function_name": func_name,
                    "arguments": params
                })
                
            except Exception as e:
                self.logger.warning(f"Failed to parse function call {func_name}: {e}")
                continue
        
        return function_calls
    
    def _execute_parsed_function(self, func_call: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Execute a parsed function call"""
        try:
            func_name = func_call.get("function_name")
            arguments = func_call.get("arguments", {})
            
            if not func_name:
                return {"success": False, "error": "No function name"}
            
            # Execute the function using the function handler
            from .function_handlers import function_handler
            
            result = function_handler.execute_function(func_name, session_id, **arguments)
            
            return {
                "function_name": func_name,
                "arguments": arguments,
                "result": result,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to execute parsed function {func_call}: {e}")
            return {
                "function_name": func_call.get("function_name", "unknown"),
                "arguments": func_call.get("arguments", {}),
                "error": str(e),
                "success": False
            }
    
    def _create_tool_response_prompt(self, user_message: str, function_name: str, 
                                    function_result: Dict, conversation_history: List[Dict]) -> str:
        """Create a prompt for Gemini to generate a response using tool results"""
        try:
            prompt_parts = []
            
            # System context
            prompt_parts.append("You are an AI assistant for AI Consultancy, specializing in student visas.")
            prompt_parts.append("A function has been executed successfully. Generate a natural, helpful response.")
            
            # User's original question
            prompt_parts.append(f"\nUser Question: {user_message}")
            
            # Function context
            prompt_parts.append(f"\nFunction Executed: {function_name}")
            
            # Function result
            if function_result.get('data'):
                prompt_parts.append(f"\nFunction Result Data: {function_result['data']}")
            
            # Function message
            if function_result.get('message'):
                prompt_parts.append(f"\nFunction Message: {function_result['message']}")
            
            # Conversation history (last 2 messages for context)
            if conversation_history:
                prompt_parts.append("\nRecent Conversation:")
                for msg in conversation_history[-2:]:
                    content = msg.get('content', msg.get('user_message', msg.get('user_input', '')))
                    prompt_parts.append(f"- User: {content}")
            
            # Instructions based on function type


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
    
    def is_available(self) -> bool:
        """Check if function calling is available"""
        return self.llm_model is not None

    def _normalize_args(self, raw_args):
        """Normalize Gemini function call args from protobuf to dict"""
        import json
        try:
            # Try Gemini SDK helper if available
            from google.generativeai import to_json as gem_to_json
            return json.loads(gem_to_json(raw_args))
        except Exception:
            # Manual conversion for MapComposite
            if hasattr(raw_args, "items"):
                return dict(raw_args.items())
            try:
                return dict(raw_args)  # last resort
            except Exception:
                return {}

    def _validate_function_schemas(self):
        """Validate that all function schemas are properly formatted"""
        try:
            for func in self.function_declarations:
                name = func.get('name', 'Unknown')
                params = func.get('parameters', {})
                
                # Check required fields
                if 'type' not in params:
                    self.logger.warning(f"Function {name} missing 'type' in parameters")
                if 'properties' not in params:
                    self.logger.warning(f"Function {name} missing 'properties' in parameters")
                if 'required' not in params:
                    self.logger.warning(f"Function {name} missing 'required' in parameters")
                
                # Check properties
                properties = params.get('properties', {})
                for prop_name, prop_def in properties.items():
                    if 'type' not in prop_def:
                        self.logger.warning(f"Function {name}, property {prop_name} missing 'type'")
                
                self.logger.info(f"[PASS] Function {name} schema validated")
                
        except Exception as e:
            self.logger.error(f"Error validating function schemas: {e}")

# No global instance needed - created per RAGLLMIntegrator instance

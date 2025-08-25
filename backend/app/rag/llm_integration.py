#!/usr/bin/env python3
"""
RAG-LLM Integration Module
Handles the complete flow from RAG retrieval to LLM response generation
"""

import logging
from typing import Dict, List, Optional, Any
from .retriever import retrieve
from .prompt_orchestrator import get_prompt_orchestrator
from app.functions.function_integrator import FunctionIntegrator

logger = logging.getLogger(__name__)

class RAGLLMIntegrator:
    """Integrates RAG retrieval with LLM generation for intelligent responses"""
    
    def __init__(self, llm_model=None):
        self.llm_model = llm_model
        self.prompt_orchestrator = get_prompt_orchestrator()
        self.function_integrator = None
        
        # Initialize function calling
        if llm_model:
            self.function_integrator = FunctionIntegrator(llm_model)
            logger.info("Function calling initialized with LLM model")
        
        logger.info("RAG-LLM Integrator initialized with Prompt Orchestrator and Function Calling")
    
    def process_query(self, 
                     user_message: str, 
                     session_info: Dict[str, Any] = None,
                     conversation_history: List[Dict[str, str]] = None,
                     top_k: int = 3,
                     session_id: str = None,
                     rag_context: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Complete LLM-first processing pipeline with optional RAG support
        
        Args:
            user_message: User's query
            session_info: Current session information (country, email, etc.)
            conversation_history: Previous conversation messages
            top_k: Number of RAG results to retrieve (if needed)
            session_id: Session ID for function calling
            rag_context: Optional pre-retrieved RAG context (supplementary)
            
        Returns:
            Dict containing:
                - llm_response: Generated LLM response
                - rag_context: Retrieved RAG chunks (if any)
                - prompt_used: The prompt sent to LLM
                - function_calls: Function calls made by LLM
                - metadata: Additional processing info
        """
        try:
            # Step 1: Use provided RAG context or retrieve only if LLM needs support
            if rag_context is not None:
                rag_results = rag_context
                logger.info(f"Using provided RAG context: {len(rag_results)} results")
            else:
                # Only retrieve RAG if explicitly needed (LLM-first approach)
                rag_results = []
                logger.info("LLM-first approach: No RAG context provided, using LLM knowledge only")
            
            # Step 2: Try function calling first, fallback to regular LLM
            if self.function_integrator and session_id:
                logger.info("Attempting function calling for enhanced response")
                try:
                    function_result = self.function_integrator.process_with_functions(
                        user_message=user_message,
                        session_id=session_id,
                        conversation_history=conversation_history,
                        session_info=session_info
                    )
                    
                    if function_result.get("processing_successful"):
                        # Add metadata to function result (RAG-free)
                        function_result["prompt_used"] = "Function calling prompt"
                        function_result["metadata"] = {
                            "rag_results_count": 0,  # RAG disabled
                            "has_country_info": bool(session_info.get('country') if session_info else False),
                            "has_conversation_history": bool(conversation_history),
                            "function_calls_made": len(function_result.get("function_calls", [])),
                            "processing_method": "function_calling"
                        }
                        
                        logger.info(f"Function calling successful with {len(function_result.get('function_calls', []))} function calls")
                        return function_result
                    else:
                        logger.warning("Function calling failed, falling back to regular LLM")
                        
                except Exception as e:
                    logger.error(f"Function calling error: {e}, falling back to regular LLM")
            
            # Step 3: Fallback to regular LLM processing
            logger.info("Using regular LLM processing (no function calling)")
            prompt = self.prompt_orchestrator.create_comprehensive_prompt(
                user_question=user_message,
                rag_context=rag_results,
                user_info=session_info,
                conversation_history=conversation_history
            )
            
            # Step 4: Generate LLM response
            logger.info("Step 4: Generating LLM response...")
            llm_response = self._generate_llm_response(prompt)
            
            # Step 5: Return complete result
            logger.info(f"Step 5: LLM response generated, length: {len(llm_response) if llm_response else 0}")
            
            result = {
                "llm_response": llm_response,
                "rag_context": rag_results,
                "prompt_used": prompt,
                "function_calls": [],
                "processing_successful": True,
                "metadata": {
                    "rag_results_count": len(rag_results) if rag_results else 0,
                    "has_country_info": bool(session_info.get('country') if session_info else False),
                    "has_conversation_history": bool(conversation_history),
                    "processing_method": "regular_llm"
                }
            }
            
            logger.info(f"RAG-LLM processing completed successfully. Response length: {len(llm_response) if llm_response else 0}")
            return result
            
        except Exception as e:
            logger.error(f"Error in RAG-LLM integration: {str(e)}")
            return {
                "processing_successful": False,
                "error": str(e),
                "llm_response": None,
                "function_calls": [],
                "rag_context": [],
                "prompt_used": "Error in RAG-LLM integration",
                "metadata": {
                    "error": str(e),
                    "processing_method": "error"
                }
            }
    
    def _retrieve_rag_context(self, query: str, top_k: int, session_info: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Retrieve relevant context from RAG system"""
        try:
            # Check if this is a general greeting or non-specific query
            general_queries = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'how are you', 'what can you do']
            if query.lower().strip() in general_queries:
                return []
            
            # Determine country for targeted search
            country_filter = None
            if session_info and session_info.get('country'):
                country_name = session_info['country'].lower()
                # Map country names to RAG country codes
                country_mapping = {
                    'usa': 'usa',
                    'uk': 'uk', 
                    'australia': 'australia',
                    'south korea': 'south_korea'
                }
                for display_name, rag_code in country_mapping.items():
                    if display_name in country_name or country_name in display_name:
                        country_filter = rag_code
                        break
            
            # Perform RAG retrieval
            results = retrieve(query, top_k=top_k, country=country_filter)
            
            if results:
                logger.info(f"RAG retrieval returned {len(results)} results for query: '{query}'")
                return results
            else:
                logger.info(f"No RAG results found for query: '{query}'")
                return []
                
        except Exception as e:
            logger.error(f"Error in RAG retrieval: {e}")
            return []
    
    # Prompt building is now handled by the Prompt Orchestrator
    # This method has been replaced with prompt_orchestrator.create_comprehensive_prompt()
    
    def _generate_llm_response(self, prompt: str) -> str:
        """Generate response using the LLM model"""
        try:
            if not self.llm_model:
                logger.error("LLM model is None - cannot generate response")
                return "I apologize, but the AI model is not available at the moment. Please try again later."
            
            logger.info(f"Generating LLM response with prompt length: {len(prompt)}")
            
            # Generate response using the LLM
            response = self.llm_model.generate_content(prompt)
            
            # Check if response has content
            if response and hasattr(response, 'text') and response.text:
                logger.info(f"LLM response generated successfully, length: {len(response.text)}")
                return response.text
            elif response and hasattr(response, 'candidates') and response.candidates:
                # Try to get text from candidates
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                logger.info(f"LLM response generated from candidate, length: {len(part.text)}")
                                return part.text
                
                logger.error("LLM response has candidates but no text content")
                return "I apologize, but the AI model returned an empty response. Please try again."
            else:
                logger.error("LLM response is empty or None")
                return "I apologize, but the AI model returned an empty response. Please try again."
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return f"I apologize, but I encountered an error generating a response. Please try again."

# Global integrator instance
_integrator = None

def get_rag_llm_integrator(llm_model=None):
    """Get or create the global RAG-LLM integrator instance"""
    global _integrator
    if _integrator is None:
        _integrator = RAGLLMIntegrator(llm_model=llm_model)
    return _integrator

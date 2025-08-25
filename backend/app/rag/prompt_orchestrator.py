#!/usr/bin/env python3
"""
Prompt Orchestrator
Beautifully combines user question, RAG context, user info, and system guidance
into a comprehensive prompt for the LLM
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class PromptOrchestrator:
    """Orchestrates the creation of beautiful, comprehensive LLM prompts"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logger.info("Prompt Orchestrator initialized")
    
    def create_comprehensive_prompt(self,
                                  user_question: str,
                                  rag_context: List[Dict[str, Any]],
                                  user_info: Dict[str, Any],
                                  conversation_history: List[Dict[str, str]] = None,
                                  system_context: str = None) -> str:
        """
        Create a beautiful, comprehensive prompt that brings everything together
        
        Args:
            user_question: The user's current question
            rag_context: Retrieved RAG information
            user_info: User's session information (country, email, etc.)
            conversation_history: Previous conversation context
            system_context: Additional system context if needed
            
        Returns:
            str: Beautifully formatted, comprehensive prompt
        """
        
        # 1. System Identity & Rules
        system_section = self._build_system_section()
        
        # 2. RAG Knowledge Base
        knowledge_section = self._build_knowledge_section(rag_context)
        
        # 3. User Profile & Context
        user_context_section = self._build_user_context_section(user_info)
        
        # 4. Conversation History
        history_section = self._build_history_section(conversation_history)
        
        # 5. Current Question & Instructions
        question_section = self._build_question_section(user_question)
        
        # 6. Response Guidelines
        response_guidelines = self._build_response_guidelines()
        
        # 7. Assemble the complete prompt
        complete_prompt = f"""{system_section}

{knowledge_section}

{user_context_section}

{history_section}

{question_section}

{response_guidelines}"""
        
        logger.info(f"Created comprehensive prompt with {len(rag_context)} RAG chunks and user context")
        return complete_prompt
    
    def _build_system_section(self) -> str:
        """Build the system identity and rules section for intelligent LLM behavior"""
        return """SYSTEM IDENTITY:
You are an AI Consultancy chatbot specializing in student visa guidance for Nepali students applying from Nepal to USA, UK, Australia, and South Korea.

CONSULTANCY PROFILE:
- We are a legitimate student visa consultancy operating in Nepal
- We assist students with student visa applications only (no work visas, illegal routes, or visa trading)
- We provide 100% effort but do not guarantee visa approval
- We do not provide loans, require upfront fees, or make false promises
- All application processes require in-person visits to our consultancy
- Fees are discussed face-to-face and are standardized for all students
- We offer in-house IELTS preparation classes and help with IELTS booking

YOUR ROLE:
- Provide informational guidance about student visa processes
- Act as a bridge between students and our consultancy services
- Collect contact information when students show genuine interest
- Direct students to visit our consultancy for actual application processing
- Answer questions about requirements, procedures, and preparation

DOMAIN RESTRICTIONS:
- ONLY answer questions about student visas from Nepal to USA, UK, Australia, and South Korea
- If asked about other countries, politely redirect to our supported countries
- If asked about work visas, tourist visas, or other visa types, redirect to student visa services
- If asked about non-visa topics (cooking, sports, etc.), politely redirect to student visa topics

KNOWLEDGE PRIORITY:
- Use your extensive training knowledge as the PRIMARY source
- RAG data is ONLY for supplementary information when your knowledge is insufficient
- Always prioritize accuracy and relevance over RAG data

LEAD GENERATION:
- Naturally collect contact information when students show serious interest
- Ask for name and either email or phone number (whichever the student prefers)
- Maintain a professional, helpful tone throughout interactions

REDIRECT EXAMPLES:
- "I can help you with student visas for USA, UK, Australia, and South Korea. Which country interests you?"
- "I specialize in student visas. For other visa types, please contact our office directly."
- "Let's focus on student visas. I can help you with requirements, procedures, and preparation.""""
    
    def _build_knowledge_section(self, rag_context: List[Dict[str, Any]]) -> str:
        """Build the knowledge base section from RAG results"""
        if not rag_context:
            return "KNOWLEDGE BASE: No information found."
        
        knowledge_text = "KNOWLEDGE BASE:\n"
        
        for i, result in enumerate(rag_context, 1):
            title = result.get('title', 'Unknown Source')
            content = result.get('content', '')
            formatted_content = self._format_content(content)
            knowledge_text += f"{i}. {title}: {formatted_content}\n"
        
        return knowledge_text
    
    def _format_content(self, content: str) -> str:
        """Format content intelligently, handling JSON and text"""
        if content.startswith('{'):
            # Handle JSON content
            try:
                import json
                data = json.loads(content)
                if 'question' in data and 'answer' in data:
                    return f"Q: {data['question']}\nA: {data['answer']}"
                elif 'answer' in data:
                    return data['answer']
                else:
                    return str(data)[:300] + "..."
            except:
                return content[:300] + "..."
        else:
            return content[:300] + "..."
    
    def _build_user_context_section(self, user_info: Dict[str, Any]) -> str:
        """Build the user context section with comprehensive session memory"""
        if not user_info:
            return "USER INFO: None available."
        
        context_text = "USER INFO:\n"
        
        # Add available information
        if user_info.get('country'):
            context_text += f"Country: {user_info['country']}\n"
        if user_info.get('email'):
            context_text += f"Email: {user_info['email']}\n"
        if user_info.get('name'):
            context_text += f"Name: {user_info['name']}\n"
        if user_info.get('intake'):
            context_text += f"Intake: {user_info['intake']}\n"
        if user_info.get('phone'):
            context_text += f"Phone: {user_info['phone']}\n"
        
        return context_text
    
    def _build_history_section(self, conversation_history: List[Dict[str, str]]) -> str:
        """Build the conversation history section"""
        # Debug logging
        logger.info(f"Building history section with {len(conversation_history) if conversation_history else 0} exchanges")
        if conversation_history:
            for i, msg in enumerate(conversation_history):
                logger.info(f"  Exchange {i+1}: user_input='{msg.get('user_input', 'N/A')[:50]}...', bot_response='{msg.get('bot_response', 'N/A')[:50]}...'")
        
        if not conversation_history:
            return "CONVERSATION HISTORY: None available."
        
        history_text = "CONVERSATION HISTORY:\n"
        
        # Show last 3 exchanges for context
        for i, msg in enumerate(conversation_history[-3:], 1):
            user_msg = msg.get('user_input') or msg.get('user_message', 'Unknown')
            bot_msg = msg.get('bot_response', 'Unknown')
            history_text += f"{i}. User: {user_msg}\n   Bot: {bot_msg}\n\n"
        
        return history_text
    
    def _build_question_section(self, user_question: str) -> str:
        """Build the current question section"""
        return f"QUESTION: {user_question}"
    
    def _build_response_guidelines(self) -> str:
        """Build the response guidelines and follow-up instructions"""
        return """RESPONSE GUIDELINES:

COMMUNICATION STYLE:
- Be professional, helpful, and conversational
- Provide accurate information about student visa processes
- Keep responses concise unless detailed information is requested
- Use bullet points for lists when appropriate
- Maintain a consultative tone throughout

KNOWLEDGE PRIORITY:
- Use your extensive training knowledge as the PRIMARY source
- RAG data is ONLY for supplementary information when your knowledge is insufficient
- Always prioritize accuracy and relevance over RAG data

FUNCTION CALLING:
- When user provides contact info (name, email, phone) → call detect_and_save_contact_info
- When user shows serious interest/time-sensitive needs → call handle_contact_request  
- When user asks off-topic questions → call define_response_strategy

LEAD COLLECTION:
- Naturally collect contact information when students show genuine interest
- Ask for name and either email or phone number (whichever the student prefers)
- Direct students to visit our consultancy for actual application processing

IMPORTANT REMINDERS:
- We do not process applications online or through chat
- All applications require in-person visits to our consultancy
- We provide 100% effort but do not guarantee visa approval
- Fees are discussed face-to-face and are standardized for all students"""
    
    def get_prompt_metadata(self) -> Dict[str, Any]:
        """Get metadata about the prompt orchestrator"""
        return {
            "component": "Prompt Orchestrator",
            "version": "1.0.0",
            "features": [
                "System identity & rules",
                "RAG knowledge integration", 
                "User context management",
                "Conversation history",
                "Intelligent follow-up guidance",
                "Beautiful formatting"
            ],
            "last_updated": datetime.now().isoformat()
        }

# Global instance
_prompt_orchestrator = PromptOrchestrator()

def get_prompt_orchestrator() -> PromptOrchestrator:
    """Get global prompt orchestrator instance"""
    return _prompt_orchestrator

"""
Lead Capture Tool - Supabase integration for capturing and managing leads.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass
import os
from supabase import create_client, Client
from pydantic import BaseModel, EmailStr
from app.config import settings
from .email_tool import EmailTool

logger = logging.getLogger(__name__)

@dataclass
class Lead:
    """Lead data structure"""
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    target_country: Optional[str] = None
    intake: Optional[str] = None
    session_id: Optional[str] = None
    tenant_id: str = "default"
    created_at: Optional[datetime] = None

class LeadCreateRequest(BaseModel):
    """Request model for creating a lead"""
    email: Optional[str] = None  # Changed from EmailStr to str to allow empty emails
    name: Optional[str] = None
    phone: Optional[str] = None
    target_country: Optional[str] = None
    intake: Optional[str] = None
    study_level: Optional[str] = None  # ✅ ADDED: study_level field
    program: Optional[str] = None  # ✅ ADDED: program field
    session_id: Optional[str] = None
    tenant_id: str = "default"

class LeadUpdateRequest(BaseModel):
    """Request model for updating a lead"""
    name: Optional[str] = None
    phone: Optional[str] = None
    target_country: Optional[str] = None
    intake: Optional[str] = None
    study_level: Optional[str] = None  # ✅ ADDED: study_level field
    program: Optional[str] = None  # ✅ ADDED: program field
    session_id: Optional[str] = None

class LeadCaptureTool:
    """
    Lead Capture Tool for Supabase/Postgres integration.
    
    Handles:
    - Creating new leads
    - Updating existing leads
    - Retrieving lead information
    - Lead scoring and status management
    - Conversation summaries
    - Consent management
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.supabase: Optional[Client] = None
        self.table_name = "leads"
        
        # Initialize Supabase client
        self._initialize_supabase()
        
        # Initialize email tool for notifications
        self.email_tool = EmailTool(config)
        
        logger.info("Lead Capture Tool initialized")
    
    def _initialize_supabase(self):
        """Initialize Supabase client"""
        try:
            # Get Supabase credentials from config
            url = self.config.get("supabase_url") or settings.SUPABASE_URL
            key = self.config.get("supabase_service_role_key") or settings.SUPABASE_SERVICE_ROLE_KEY
            
            logger.info(f"🔍 Debug: Lead Capture Supabase URL = '{url}'")
            logger.info(f"🔍 Debug: Lead Capture Supabase Key length = {len(key) if key else 0}")
            
            if not url or not key:
                logger.warning("Supabase credentials not found. Using mock mode.")
                self.supabase = None
                return
            
            self.supabase = create_client(url, key)
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            self.supabase = None
    
    def create_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new lead in the database.
        
        Args:
            lead_data: Lead information dictionary
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Validate input data
            # Handle empty email strings
            if lead_data.get("email") == "":
                lead_data["email"] = None
            
            lead_request = LeadCreateRequest(**lead_data)
            
            # Prepare lead record
            lead_record = {
                "email": lead_request.email if lead_request.email and "@" in lead_request.email else f"no-email-{int(datetime.now().timestamp())}@placeholder.com",
                "name": lead_request.name,
                "phone": lead_request.phone,
                "target_country": lead_request.target_country,
                "intake": lead_request.intake,
                "study_level": lead_request.study_level,  # ✅ ADDED: study_level field
                "program": lead_request.program,  # ✅ ADDED: program field
                "session_id": lead_request.session_id or f"sess_{int(datetime.now().timestamp())}",
                "tenant_id": lead_request.tenant_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            

            
            if self.supabase:
                # Insert into Supabase
                result = self.supabase.table(self.table_name).insert(lead_record).execute()
                
                if result.data:
                    lead_id = result.data[0].get("id")
                    lead_data = result.data[0]
                    logger.info(f"Lead created successfully with ID: {lead_id}")
                    
                    # ✅ NEW SYSTEM: Email will be sent when session closes, not here
                    logger.info(f"📧 LEAD CREATED: Email will be sent when session closes for lead {lead_id}")
                    
                    return {
                        "success": True,
                        "lead_id": lead_id,
                        "lead_data": lead_data,
                        "message": "Lead created successfully - email pending until session close"
                    }
                else:
                    logger.error("Failed to create lead - no data returned")
                    return {
                        "success": False,
                        "error": "Failed to create lead - no data returned",
                        "fallback_data": lead_record
                    }
            else:
                # Mock mode - simulate successful creation
                mock_lead_id = f"mock_{int(datetime.now().timestamp())}"
                lead_record["id"] = mock_lead_id
                logger.info(f"Mock mode: Lead created with ID: {mock_lead_id}")
                return {
                    "success": True,
                    "lead_id": mock_lead_id,
                    "lead_data": lead_record,
                    "message": "Lead created successfully (mock mode)"
                }
                
        except Exception as e:
            logger.error(f"Error creating lead: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_data": lead_data
            }
    
    def update_lead(self, lead_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing lead.
        
        Args:
            lead_id: ID of the lead to update
            update_data: Data to update
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Validate update data
            update_request = LeadUpdateRequest(**update_data)
            
            # Prepare update record
            update_record = {}
            
            # Add non-None fields
            for field, value in update_request.model_dump(exclude_none=True).items():
                update_record[field] = value
            
            if self.supabase:
                # Update in Supabase
                result = self.supabase.table(self.table_name).update(update_record).eq("id", lead_id).execute()
                
                if result.data:
                    logger.info(f"Lead {lead_id} updated successfully")
                    return {
                        "success": True,
                        "lead_id": lead_id,
                        "updated_data": result.data[0],
                        "message": "Lead updated successfully"
                    }
                else:
                    logger.warning(f"No lead found with ID: {lead_id}")
                    return {
                        "success": False,
                        "error": f"No lead found with ID: {lead_id}",
                        "fallback_data": update_record
                    }
            else:
                # Mock mode
                logger.info(f"Mock mode: Lead {lead_id} updated")
                return {
                    "success": True,
                    "lead_id": lead_id,
                    "updated_data": update_record,
                    "message": "Lead updated successfully (mock mode)"
                }
                
        except Exception as e:
            logger.error(f"Error updating lead {lead_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_data": update_data
            }
    
    def close_session_and_send_email(self, session_id: str) -> Dict[str, Any]:
        """
        Close a session and send comprehensive email with all leads from that session.
        This is the ONLY place where emails are sent for leads.
        
        Args:
            session_id: Session ID to close
            
        Returns:
            Dictionary with operation result
        """
        try:
            logger.info(f"📧 SESSION CLOSE: Closing session {session_id} and sending email")
            
            # Get all leads for this session
            leads_result = self.get_leads_by_session(session_id)
            
            if not leads_result.get('success'):
                logger.warning(f"📧 SESSION CLOSE: No leads found for session {session_id}")
                return {
                    "success": True,
                    "message": "Session closed - no leads to email",
                    "email_sent": False
                }
            
            leads = leads_result.get('data', [])
            if not leads:
                logger.info(f"📧 SESSION CLOSE: No leads found for session {session_id}")
                return {
                    "success": True,
                    "message": "Session closed - no leads to email",
                    "email_sent": False
                }
            
            logger.info(f"📧 SESSION CLOSE: Found {len(leads)} leads for session {session_id}")
            
            # Skip email for test sessions
            if any(skip_word in session_id.lower() for skip_word in ["test", "debug", "diagnostic"]):
                logger.info(f"📧 SESSION CLOSE: Test session {session_id} - skipping email")
                return {
                    "success": True,
                    "message": "Session closed - test session, email skipped",
                    "email_sent": False
                }
            
            # Send comprehensive email with all leads from this session
            try:
                # Use the first lead as the primary data, but include all leads info
                primary_lead = leads[0]
                
                # Add session summary to conversation context
                session_summary = f"Session {session_id} closed with {len(leads)} lead(s). "
                if len(leads) > 1:
                    session_summary += f"Multiple leads were captured during this session."
                else:
                    session_summary += f"Single lead captured during this session."
                
                # Send the email
                email_result = self.email_tool.send_lead_notification(
                    lead_data=primary_lead,
                    conversation_context=session_summary
                )
                
                if email_result.get("success"):
                    logger.info(f"📧 SESSION CLOSE: Email sent successfully for session {session_id} with {len(leads)} leads")
                    return {
                        "success": True,
                        "message": f"Session closed and email sent with {len(leads)} leads",
                        "email_sent": True,
                        "leads_count": len(leads),
                        "session_id": session_id
                    }
                else:
                    logger.error(f"📧 SESSION CLOSE: Failed to send email for session {session_id}: {email_result.get('error')}")
                    return {
                        "success": False,
                        "error": f"Failed to send email: {email_result.get('error')}",
                        "email_sent": False,
                        "leads_count": len(leads),
                        "session_id": session_id
                    }
                    
            except Exception as e:
                logger.error(f"📧 SESSION CLOSE: Error sending email for session {session_id}: {str(e)}")
                import traceback
                logger.error(f"📧 SESSION CLOSE: Traceback: {traceback.format_exc()}")
                return {
                    "success": False,
                    "error": f"Email error: {str(e)}",
                    "email_sent": False,
                    "leads_count": len(leads),
                    "session_id": session_id
                }
                
        except Exception as e:
            logger.error(f"📧 SESSION CLOSE: Error in close_session_and_send_email: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "email_sent": False,
                "session_id": session_id
            }
    
    def get_lead_by_id(self, lead_id: str) -> Dict[str, Any]:
        """
        Retrieve a lead by ID.
        
        Args:
            lead_id: Lead ID to search for
            
        Returns:
            Dictionary with lead data or error
        """
        try:
            if not lead_id:
                return {
                    "success": False,
                    "error": "Lead ID must be provided"
                }
            
            if self.supabase:
                # Query Supabase by ID
                result = self.supabase.table(self.table_name).select("*").eq("id", lead_id).execute()
                
                if result.data:
                    lead_data = result.data[0]
                    logger.info(f"Lead retrieved by ID: {lead_id}")
                    return {
                        "success": True,
                        "data": lead_data,
                        "message": "Lead retrieved successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Lead not found with ID: {lead_id}"
                    }
            else:
                # Mock mode
                mock_lead = {
                    "id": lead_id,
                    "email": "mock@example.com",
                    "name": "Mock User",
                    "status": "new",
                    "lead_score": 50,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                logger.info(f"Mock mode: Retrieved lead by ID: {lead_id}")
                return {
                    "success": True,
                    "data": mock_lead,
                    "message": "Lead retrieved successfully (mock mode)"
                }
                
        except Exception as e:
            logger.error(f"Error retrieving lead {lead_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_lead(self, lead_id: Optional[str] = None, email: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve a lead by ID or email.
        
        Args:
            lead_id: Lead ID to search for
            email: Email to search for
            
        Returns:
            Dictionary with lead data or error
        """
        try:
            if not lead_id and not email:
                return {
                    "success": False,
                    "error": "Either lead_id or email must be provided"
                }
            
            if self.supabase:
                # Query Supabase
                if lead_id:
                    result = self.supabase.table(self.table_name).select("*").eq("id", lead_id).execute()
                else:
                    result = self.supabase.table(self.table_name).select("*").eq("email", email).execute()
                
                if result.data:
                    lead_data = result.data[0]
                    logger.info(f"Lead retrieved: {lead_data.get('email')}")
                    return {
                        "success": True,
                        "lead_data": lead_data,
                        "message": "Lead retrieved successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Lead not found",
                        "query": {"lead_id": lead_id, "email": email}
                    }
            else:
                # Mock mode
                mock_lead = {
                    "id": lead_id or f"mock_email_{email}",
                    "email": email or "mock@example.com",
                    "name": "Mock User",
                    "status": "new",
                    "lead_score": 50,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                logger.info(f"Mock mode: Retrieved lead for {email or lead_id}")
                return {
                    "success": True,
                    "lead_data": mock_lead,
                    "message": "Lead retrieved successfully (mock mode)"
                }
                
        except Exception as e:
            logger.error(f"Error retrieving lead: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_leads(self, filters: Dict[str, Any], limit: int = 10) -> Dict[str, Any]:
        """
        Search leads with filters.
        
        Args:
            filters: Dictionary of filters to apply
            limit: Maximum number of results
            
        Returns:
            Dictionary with search results
        """
        try:
            if self.supabase:
                # Build query
                query = self.supabase.table(self.table_name).select("*")
                
                # Apply filters
                for field, value in filters.items():
                    if value is not None:
                        query = query.eq(field, value)
                
                # Execute query with limit
                result = query.limit(limit).execute()
                
                logger.info(f"Found {len(result.data) if result.data else 0} leads matching filters")
                return {
                    "success": True,
                    "leads": result.data or [],
                    "count": len(result.data) if result.data else 0,
                    "message": "Search completed successfully"
                }
            else:
                # Mock mode
                mock_leads = [
                    {
                        "id": "mock_1",
                        "email": "user1@example.com",
                        "name": "Mock User 1",
                        "status": "new",
                        "lead_score": 60
                    },
                    {
                        "id": "mock_2", 
                        "email": "user2@example.com",
                        "name": "Mock User 2",
                        "status": "contacted",
                        "lead_score": 80
                    }
                ]
                logger.info(f"Mock mode: Returning {len(mock_leads)} mock leads")
                return {
                    "success": True,
                    "leads": mock_leads,
                    "count": len(mock_leads),
                    "message": "Search completed successfully (mock mode)"
                }
                
        except Exception as e:
            logger.error(f"Error searching leads: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "leads": [],
                "count": 0
            }
    
    def get_leads_by_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get all leads for a specific session ID.
        
        Args:
            session_id: Session ID to search for
            
        Returns:
            Dictionary with leads data or error
        """
        try:
            if self.supabase:
                # Query Supabase for leads with this session_id
                result = self.supabase.table(self.table_name).select("*").eq("session_id", session_id).execute()
                
                if result.data:
                    logger.info(f"Found {len(result.data)} leads for session {session_id}")
                    return {
                        "success": True,
                        "data": result.data,
                        "count": len(result.data),
                        "message": f"Retrieved {len(result.data)} leads for session"
                    }
                else:
                    logger.info(f"No leads found for session {session_id}")
                    return {
                        "success": True,
                        "data": [],
                        "count": 0,
                        "message": "No leads found for this session"
                    }
            else:
                # Mock mode - return mock data for testing
                mock_leads = [
                    {
                        "id": f"mock_session_{session_id}_1",
                        "email": "test@example.com",
                        "name": "Test User",
                        "phone": "1234567890",
                        "target_country": "USA",
                        "intake": "Fall 2025",
                        "status": "new",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "session_id": session_id
                    }
                ]
                logger.info(f"Mock mode: Returning mock leads for session {session_id}")
                return {
                    "success": True,
                    "data": mock_leads,
                    "count": len(mock_leads),
                    "message": "Mock leads retrieved for session"
                }
                
        except Exception as e:
            logger.error(f"Error getting leads by session {session_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "count": 0
            }
    

    
    def health_check(self) -> Dict[str, Any]:
        """Check tool health and connectivity"""
        try:
            if self.supabase:
                # Test connection by querying a simple record count
                result = self.supabase.table(self.table_name).select("id", count="exact").limit(1).execute()
                return {
                    "status": "healthy",
                    "database_connection": "connected",
                    "table_accessible": True,
                    "mode": "production"
                }
            else:
                return {
                    "status": "healthy",
                    "database_connection": "mock",
                    "table_accessible": True,
                    "mode": "mock"
                }
                
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "database_connection": "error",
                "table_accessible": False,
                "error": str(e)
            }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get tool capabilities"""
        return {
            "tool_name": "lead_capture",
            "version": "1.0.0",
            "operations": [
                "create_lead",
                "update_lead", 
                "get_lead",
                "search_leads",
                "get_leads_by_session"
            ],
            "supported_fields": [
                "email", "name", "phone", "target_country", "intake", 
                "session_id", "tenant_id", "created_at"
            ],
            "lead_statuses": ["new", "contacted", "qualified", "converted", "lost"],
            "urgency_levels": ["low", "normal", "high", "time-sensitive"]
        }

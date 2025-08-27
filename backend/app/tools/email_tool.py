"""
Email Tool - Handles email notifications and communications.

This tool sends:
- Lead capture notifications
- System alerts
- User communications
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

class EmailTool:
    """Email notification and communication tool"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.smtp_server = self.config.get("smtp_server") or settings.SMTP_SERVER
        self.smtp_port = self.config.get("smtp_port") or settings.SMTP_PORT
        self.username = self.config.get("username") or settings.SMTP_USERNAME
        self.password = self.config.get("password") or settings.SMTP_PASSWORD
        self.from_email = self.config.get("from_email") or settings.FROM_EMAIL
        self.from_name = self.config.get("from_name") or settings.FROM_NAME
        
        # Check if email is configured
        self.email_configured = bool(
            self.smtp_server and 
            self.smtp_port and 
            self.username and 
            self.password and 
            self.from_email
        )
        
        if not self.email_configured:
            logger.warning(f"📧 EMAIL DEBUG: Email not configured - missing: server={bool(self.smtp_server)}, port={bool(self.smtp_port)}, username={bool(self.username)}, password={bool(self.password)}, from_email={bool(self.from_email)}")
        else:
            logger.info(f"📧 EMAIL DEBUG: Email configured successfully - server: {self.smtp_server}:{self.smtp_port}")
    
    @staticmethod
    def configured() -> bool:
        """Check if email is configured and ready to send"""
        from app.config import settings
        return bool(settings.SMTP_USERNAME and settings.SMTP_PASSWORD and settings.FROM_EMAIL)
    
    def send_lead_notification(self, lead_data: Dict[str, Any], conversation_context: Optional[str] = None, 
                              lead_id: Optional[str] = None, summary: Optional[str] = None, 
                              priority: str = "normal") -> Dict[str, Any]:
        """
        Send lead notification email to configured email address.
        
        Args:
            lead_data: Lead information dictionary
            conversation_context: Optional conversation context/summary
            lead_id: Optional lead ID for new notification format
            summary: Optional summary for new notification format
            priority: Priority level (low, normal, high)
            
        Returns:
            Dictionary with operation result
        """
        try:
            logger.info(f"📧 EMAIL DEBUG: send_lead_notification called with lead_data: {lead_data}")
            logger.info(f"📧 EMAIL DEBUG: self.email_configured = {self.email_configured}")
            logger.info(f"📧 EMAIL DEBUG: self.username = {self.username}")
            logger.info(f"📧 EMAIL DEBUG: self.password = {'SET' if self.password else 'NOT SET'}")
            logger.info(f"📧 EMAIL DEBUG: self.from_email = {self.from_email}")
            logger.info(f"📧 EMAIL DEBUG: LEAD_NOTIFICATION_EMAIL = {settings.LEAD_NOTIFICATION_EMAIL}")
            
            if not self.email_configured:
                logger.warning(f"📧 EMAIL DEBUG: Email not configured - would send lead notification for {lead_data.get('email', 'unknown')}")
                return {
                    "success": False,
                    "error": "Email not configured",
                    "would_send_to": settings.LEAD_NOTIFICATION_EMAIL
                }
            
            # Handle new notification format
            if lead_id and summary:
                return self._send_human_notification(lead_id, summary, priority)
            
            # Prepare email content
            subject = f"New Lead Captured: {lead_data.get('name', 'Unknown')}"
            
            # Build email body
            body = self._build_lead_notification_body(lead_data, conversation_context)
            
            # Send email
            result = self._send_email(
                to_email=settings.LEAD_NOTIFICATION_EMAIL,
                subject=subject,
                body=body,
                is_html=True
            )
            
            if result["success"]:
                logger.info(f"Lead notification sent successfully to {settings.LEAD_NOTIFICATION_EMAIL}")
            else:
                logger.error(f"Failed to send lead notification: {result['error']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending lead notification: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_human_notification_body(self, lead_id: str, summary: str, priority: str, ticket_id: str) -> str:
        """Build HTML email body for human notification"""
        
        # Priority color mapping
        priority_colors = {
            "low": "#28a745",      # Green
            "normal": "#ffc107",   # Yellow
            "high": "#dc3545"      # Red
        }
        
        priority_color = priority_colors.get(priority.lower(), "#ffc107")
        
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: {priority_color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .ticket {{ background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .priority {{ display: inline-block; background-color: {priority_color}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold; }}
                .summary {{ background-color: #fff; border: 1px solid #dee2e6; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Human Notification Required</h1>
                <p>Lead requires human counselor attention</p>
            </div>
            
            <div class="content">
                <div class="ticket">
                    <h3>Ticket Information</h3>
                    <p><strong>Ticket ID:</strong> {ticket_id}</p>
                    <p><strong>Lead ID:</strong> {lead_id}</p>
                    <p><strong>Priority:</strong> <span class="priority">{priority.upper()}</span></p>
                    <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="summary">
                    <h3>Lead Summary</h3>
                    <pre style="white-space: pre-wrap; font-family: inherit;">{summary}</pre>
                </div>
                
                <p><strong>Action Required:</strong> Please review this lead and take appropriate action based on the priority level.</p>
                
                <p><em>This notification was automatically generated by the AI Consultancy AI system.</em></p>
            </div>
        </body>
        </html>
        """
        
        return body
    
    def _send_human_notification(self, lead_id: str, summary: str, priority: str = "normal") -> Dict[str, Any]:
        """Send human notification with priority and summary"""
        try:
            if not self.email_configured:
                return {
                    "success": False,
                    "error": "Email not configured",
                    "ticket_id": None
                }
            
            # Generate ticket ID
            import time
            ticket_id = f"TICKET-{int(time.time())}"
            
            # Prepare email content
            subject = f"Human Notification Required - Lead {lead_id} (Priority: {priority.upper()})"
            
            # Build email body
            body = self._build_human_notification_body(lead_id, summary, priority, ticket_id)
            
            # Send email
            result = self._send_email(
                to_email=settings.LEAD_NOTIFICATION_EMAIL,
                subject=subject,
                body=body,
                is_html=True
            )
            
            if result["success"]:
                logger.info(f"Human notification sent successfully, ticket: {ticket_id}")
                return {
                    "success": True,
                    "ticket_id": ticket_id,
                    "message": "Human notification sent successfully"
                }
            else:
                logger.error(f"Failed to send human notification: {result['error']}")
                return {
                    "success": False,
                    "error": result['error'],
                    "ticket_id": None
                }
                
        except Exception as e:
            logger.error(f"Error sending human notification: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "ticket_id": None
            }
    
    def _build_lead_notification_body(self, lead_data: Dict[str, Any], conversation_context: Optional[str] = None) -> str:
        """Build HTML email body for lead notification with Gmail management options"""
        
        # Lead details section
        lead_details = f"""
        <h2>New Lead Captured!</h2>
        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h3>Lead Information</h3>
        <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
            <tr style="background-color: #f8f9fa;">
                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Email</td>
                <td style="padding: 12px; border: 1px solid #dee2e6;">{lead_data.get('email', 'N/A')}</td>
            </tr>
            <tr>
                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Name</td>
                <td style="padding: 12px; border: 1px solid #dee2e6;">{lead_data.get('name', 'N/A')}</td>
            </tr>
            <tr style="background-color: #f8f9fa;">
                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Phone</td>
                <td style="padding: 12px; border: 1px solid #dee2e6;">{lead_data.get('phone', 'N/A')}</td>
            </tr>
            <tr>
                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Target Country</td>
                <td style="padding: 12px; border: 1px solid #dee2e6;">{lead_data.get('target_country', 'N/A')}</td>
            </tr>
            <tr style="background-color: #f8f9fa;">
                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Intake</td>
                <td style="padding: 12px; border: 1px solid #dee2e6;">{lead_data.get('intake', 'N/A')}</td>
            </tr>
            <tr>
                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Study Level</td>
                <td style="padding: 12px; border: 1px solid #dee2e6;">{lead_data.get('study_level', 'N/A')}</td>
            </tr>
            <tr style="background-color: #f8f9fa;">
                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Program</td>
                <td style="padding: 12px; border: 1px solid #dee2e6;">{lead_data.get('program', 'N/A')}</td>
            </tr>
            <tr>
                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">Session ID</td>
                <td style="padding: 12px; border: 1px solid #dee2e6;">{lead_data.get('session_id', 'N/A')}</td>
            </tr>
        </table>
        """
        
        # Conversation context section
        if conversation_context:
            lead_details += f"""
            <h3>Conversation Context</h3>
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; font-style: italic;">{conversation_context}</p>
            </div>
            """
        
        # Lead Management Actions
        lead_details += f"""
        <h3>Lead Management Actions</h3>
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h4 style="margin: 0 0 15px 0; color: #495057;">Quick Actions:</h4>
            
            <div style="margin-bottom: 15px;">
                <a href="mailto:{lead_data.get('email', '')}?subject=Re: Visa Consultation Inquiry" 
                   style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
                   📧 Reply to Lead
                </a>
                <a href="tel:{lead_data.get('phone', '')}" 
                   style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
                   📞 Call Lead
                </a>
            </div>
            
            <h4 style="margin: 20px 0 15px 0; color: #495057;">Lead Status Management:</h4>
            <p style="margin: 0 0 15px 0; color: #6c757d; font-size: 14px;">
                <strong>Gmail Labels to Use:</strong>
            </p>
            
            <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px;">
                <span style="background-color: #d4edda; color: #155724; padding: 5px 12px; border-radius: 15px; font-size: 12px; font-weight: bold;">
                    ✅ Qualified
                </span>
                <span style="background-color: #fff3cd; color: #856404; padding: 5px 12px; border-radius: 15px; font-size: 12px; font-weight: bold;">
                    ⏳ Follow Up
                </span>
                <span style="background-color: #f8d7da; color: #721c24; padding: 5px 12px; border-radius: 15px; font-size: 12px; font-weight: bold;">
                    ❌ Not Qualified
                </span>
                <span style="background-color: #d1ecf1; color: #0c5460; padding: 5px 12px; border-radius: 15px; font-size: 12px; font-weight: bold;">
                    📅 {lead_data.get('intake', 'Unknown')} Intake
                </span>
                <span style="background-color: #e2e3e5; color: #383d41; padding: 5px 12px; border-radius: 15px; font-size: 12px; font-weight: bold;">
                    🌍 {lead_data.get('target_country', 'Unknown')}
                </span>
            </div>
            
            <p style="margin: 0; color: #6c757d; font-size: 12px;">
                <strong>Tip:</strong> Create Gmail filters to automatically apply these labels based on email content or sender.
            </p>
        </div>
        
        <h3>Lead Qualification Checklist</h3>
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h4 style="margin: 0 0 15px 0; color: #495057;">Check these before qualifying:</h4>
            <ul style="margin: 0; padding-left: 20px;">
                <li>✅ Valid email address</li>
                <li>✅ Clear country preference</li>
                <li>✅ Realistic intake timeline</li>
                <li>✅ Genuine interest (not spam)</li>
                <li>✅ Contactable (phone/email works)</li>
            </ul>
            
            <div style="margin-top: 20px; padding: 15px; background-color: #e7f3ff; border-left: 4px solid #007bff; border-radius: 4px;">
                <p style="margin: 0; color: #004085; font-weight: bold;">
                    <strong>Qualification Criteria:</strong>
                </p>
                <p style="margin: 5px 0 0 0; color: #004085;">
                    • <strong>Qualified:</strong> Meets all checklist items, ready for consultation<br>
                    • <strong>Follow Up:</strong> Missing some info, needs more contact<br>
                    • <strong>Not Qualified:</strong> Spam, wrong target, or unrealistic expectations
                </p>
            </div>
        </div>
        
        <h3>Next Steps</h3>
        <ul>
            <li>Review lead information above</li>
            <li>Contact lead within 24 hours</li>
            <li>Apply appropriate Gmail label (Qualified/Follow Up/Not Qualified)</li>
            <li>Move to appropriate Gmail folder</li>
            <li>Schedule follow-up if needed</li>
        </ul>
        
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
        <p style="color: #6c757d; font-size: 12px;">
            This notification was automatically generated by the AI Chatbot Lead Capture System.<br>
            Lead ID: {lead_data.get('id', 'N/A')} | Generated: {datetime.now().isoformat()}
        </p>
        """
        
        return lead_details
    
    def _send_email(self, to_email: str, subject: str, body: str, is_html: bool = False) -> Dict[str, Any]:
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server with timeout
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=5) as server:
                server.starttls()
                server.login(self.username, self.password)
                
                # Send email
                text = msg.as_string()
                server.sendmail(self.from_email, to_email, text)
                
                logger.info(f"Email sent successfully to {to_email}")
                return {
                    "success": True,
                    "message": "Email sent successfully",
                    "to": to_email,
                    "subject": subject
                }
                
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "to": to_email,
                "subject": subject
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Check email tool health"""
        return {
            "status": "healthy" if self.email_configured else "not_configured",
            "email_configured": self.email_configured,
            "smtp_server": self.smtp_server,
            "smtp_port": self.smtp_port,
            "from_email": self.from_email
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get tool capabilities"""
        return {
            "tool_name": "email_notifications",
            "version": "1.0.0",
            "operations": [
                "send_lead_notification",
                "send_general_email"
            ],
            "features": [
                "HTML email support",
                "Lead notification templates",
                "Lead qualification checklist",
                "Gmail management guidance",
                "SMTP integration",
                "Error handling and logging"
            ],
            "configured": self.email_configured
        }
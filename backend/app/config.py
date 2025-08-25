import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Environment variables are set in Cloud Run deployment
# No local file loading needed for production
print("Loading environment variables from Cloud Run configuration")

class Settings:
	# API Configuration
	GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
	GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
	EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
	
	# Application Settings
	ALLOW_GENERAL_FALLBACK: bool = os.getenv("ALLOW_GENERAL_FALLBACK", "1").lower() == "1"
	DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
	
	# Student Visa Settings
	SUPPORTED_COUNTRIES: list = ["USA", "UK", "South Korea", "Australia"]  # Canada removed - no data available
	REQUIRED_LEAD_FIELDS: list = ["name", "email", "phone", "target_country"]
	OPTIONAL_LEAD_FIELDS: list = ["preferred_intake", "study_level", "gpa_grades", "study_field"]
	
	# RAG Settings
	TOP_K_RETRIEVAL: int = int(os.getenv("TOP_K_RETRIEVAL", "3"))
	LOW_SCORE_THRESHOLD: float = float(os.getenv("LOW_SCORE_THRESHOLD", "0.22"))

	# Cloud Retrieval (Vertex AI Vector Search)
	USE_VERTEX: bool = os.getenv("USE_VERTEX", "true").lower() == "true"
	VERTEX_PROJECT_ID: str = os.getenv("VERTEX_PROJECT_ID", os.getenv("GCP_PROJECT_ID", ""))
	VERTEX_LOCATION: str = os.getenv("VERTEX_LOCATION", "us-central1")
	VERTEX_INDEX_ENDPOINT: str = os.getenv("VERTEX_INDEX_ENDPOINT", "")
	VERTEX_DEPLOYED_INDEX_ID: str = os.getenv("VERTEX_DEPLOYED_INDEX_ID", "")

	# CORS Settings
	CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")
	
	# Rate Limiting - Updated for Gemini 2.5 Flash
	RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
	RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "2000"))
	
	# Platform Configuration
	# WhatsApp Business API Configuration
	WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
	WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
	WHATSAPP_BUSINESS_ACCOUNT_ID: str = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "")
	
	# Telegram Bot Configuration
	TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
	TELEGRAM_WEBHOOK_URL: str = os.getenv("TELEGRAM_WEBHOOK_URL", "")
	
	# Email Notification Configuration
	SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
	SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
	SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
	SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
	FROM_EMAIL: str = os.getenv("FROM_EMAIL", "")
	FROM_NAME: str = os.getenv("FROM_EMAIL", "Visa Consultation Bot")
	
	# Lead Notification Settings
	LEAD_NOTIFICATION_EMAIL: str = os.getenv("LEAD_NOTIFICATION_EMAIL", "")
	ENABLE_LEAD_NOTIFICATIONS: bool = os.getenv("ENABLE_LEAD_NOTIFICATIONS", "true").lower() == "true"
	
	# Slack Notification Configuration
	SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
	SLACK_CHANNEL: str = os.getenv("SLACK_CHANNEL", "#leads")
	
	# Agent Configuration
	AGENT_EMAILS: Dict[str, list] = {
		"primary": os.getenv("PRIMARY_AGENT_EMAILS", "").split(",") if os.getenv("PRIMARY_AGENT_EMAILS") else [],
		"secondary": os.getenv("SECONDARY_AGENT_EMAILS", "").split(",") if os.getenv("SECONDARY_AGENT_EMAILS") else [],
		"manager": os.getenv("MANAGER_EMAILS", "").split(",") if os.getenv("MANAGER_EMAILS") else []
	}
	
	# Platform Settings
	ENABLE_WHATSAPP: bool = os.getenv("ENABLE_WHATSAPP", "false").lower() == "true"
	ENABLE_TELEGRAM: bool = os.getenv("ENABLE_TELEGRAM", "false").lower() == "true"
	ENABLE_EMAIL_NOTIFICATIONS: bool = os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "true").lower() == "true"
	ENABLE_SLACK_NOTIFICATIONS: bool = os.getenv("ENABLE_SLACK_NOTIFICATIONS", "false").lower() == "true"
	
	# Webhook Configuration
	WEBHOOK_BASE_URL: str = os.getenv("WEBHOOK_BASE_URL", "https://yourdomain.com")
	WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")
	
	# Lead Management
	AUTO_ASSIGN_LEADS: bool = os.getenv("AUTO_ASSIGN_LEADS", "false").lower() == "true"
	LEAD_ASSIGNMENT_STRATEGY: str = os.getenv("LEAD_ASSIGNMENT_STRATEGY", "round_robin")  # round_robin, load_balance, manual
	URGENT_LEAD_THRESHOLD: int = int(os.getenv("URGENT_LEAD_THRESHOLD", "24"))  # hours
	
	# Notification Settings
	NOTIFY_ON_NEW_LEAD: bool = os.getenv("NOTIFY_ON_NEW_LEAD", "true").lower() == "true"
	NOTIFY_ON_LEAD_UPDATE: bool = os.getenv("NOTIFY_ON_LEAD_UPDATE", "true").lower() == "true"
	NOTIFY_ON_URGENT_LEAD: bool = os.getenv("NOTIFY_ON_URGENT_LEAD", "true").lower() == "true"
	DAILY_SUMMARY_TIME: str = os.getenv("DAILY_SUMMARY_TIME", "09:00")  # 24-hour format
	
	# Hybrid Search Configuration
	HYBRID_WEIGHT_BM25: float = 0.3
	HYBRID_WEIGHT_DENSE: float = 0.7
	CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
	
	# Supabase Configuration
	SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
	SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
	SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
	ADMIN_KEY: str = os.getenv("ADMIN_KEY", "")
	
	def validate(self) -> None:
		"""Validate required environment variables"""
		if not self.GEMINI_API_KEY:
			raise ValueError("GEMINI_API_KEY environment variable is required")
		if self.USE_VERTEX and not (self.VERTEX_INDEX_ENDPOINT and self.VERTEX_DEPLOYED_INDEX_ID and self.VERTEX_PROJECT_ID):
			raise ValueError("Vertex AI settings missing: VERTEX_INDEX_ENDPOINT, VERTEX_DEPLOYED_INDEX_ID, VERTEX_PROJECT_ID")
	
	def validate_whatsapp_config(self) -> bool:
		"""Validate WhatsApp configuration"""
		if not self.ENABLE_WHATSAPP:
			return True
		
		required_fields = [
			self.WHATSAPP_ACCESS_TOKEN,
			self.WHATSAPP_PHONE_NUMBER_ID,
			self.WHATSAPP_BUSINESS_ACCOUNT_ID
		]
		
		return all(required_fields)
	
	def validate_telegram_config(self) -> bool:
		"""Validate Telegram configuration"""
		if not self.ENABLE_TELEGRAM:
			return True
		
		required_fields = [
			self.TELEGRAM_BOT_TOKEN,
			self.TELEGRAM_WEBHOOK_URL
		]
		
		return all(required_fields)
	
	def validate_email_config(self) -> bool:
		"""Validate email configuration"""
		if not self.ENABLE_EMAIL_NOTIFICATIONS:
			return True
		
		required_fields = [
			self.SMTP_SERVER,
			self.SMTP_USERNAME,
			self.SMTP_PASSWORD,
			self.FROM_EMAIL
		]
		
		return all(required_fields)
	
	def validate_slack_config(self) -> bool:
		"""Validate Slack configuration"""
		if not self.ENABLE_SLACK_NOTIFICATIONS:
			return True
		
		required_fields = [
			self.SLACK_WEBHOOK_URL
		]
		
		return all(required_fields)
	
	def validate_supabase_config(self) -> bool:
		"""Validate Supabase configuration"""
		required_fields = [
			self.SUPABASE_URL,
			self.SUPABASE_SERVICE_ROLE_KEY,
			self.SUPABASE_ANON_KEY
		]
		
		return all(required_fields)
	
	def validate_all_platforms(self) -> Dict[str, bool]:
		"""Validate all platform configurations"""
		return {
			"whatsapp": self.validate_whatsapp_config(),
			"telegram": self.validate_telegram_config(),
			"email": self.validate_email_config(),
			"slack": self.validate_slack_config()
		}
	
	def get_enabled_platforms(self) -> list:
		"""Get list of enabled platforms"""
		enabled = []
		
		if self.ENABLE_WHATSAPP and self.validate_whatsapp_config():
			enabled.append("whatsapp")
		
		if self.ENABLE_TELEGRAM and self.validate_telegram_config():
			enabled.append("telegram")
		
		return enabled
	
	def get_agent_emails(self) -> list:
		"""Get all agent emails"""
		all_emails = []
		for emails in self.AGENT_EMAILS.values():
			all_emails.extend([email.strip() for email in emails if email.strip()])
		return all_emails
	
	def get_webhook_urls(self) -> Dict[str, str]:
		"""Get webhook URLs for all platforms"""
		base_url = self.WEBHOOK_BASE_URL.rstrip('/')
		
		return {
			"whatsapp": f"{base_url}/chat/platform/whatsapp/webhook",
			"telegram": f"{base_url}/chat/platform/telegram/webhook"
		}

# Global settings instance
settings = Settings()

# Don't validate on import - let the application validate when it's ready



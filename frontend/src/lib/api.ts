// src/lib/api.ts
import { config, getApiUrl } from './config';

export type Source = { title: string; url?: string; chunk_id: string };

// Enhanced types for our integrated backend v2.0
export type ChatResponse = {
  response: string;
  session_id: string;
  lead_captured: boolean;
  lead_data?: Record<string, any>;
  next_action?: string;
  confidence: number;
  timestamp: string;
  safety_violation?: SafetyViolation;
  risk_level?: string;
};

export type SafetyViolation = {
  description: string;
  suggested_response: string;
  escalation: string;
  tone: string;
  requires_blocking: boolean;
};

export type LeadData = {
  email: string;
  name?: string;
  phone?: string;
  target_country?: string;
  intake?: string;
  session_id?: string;
};

export type LeadResponse = {
  success: boolean;
  lead_id?: string;
  message: string;
};

export type CountriesResponse = {
  countries: string[];
  count: number;
};

export type HealthResponse = {
  status: string;
  components: Record<string, string>;
  timestamp: string;
  version: string;
  uptime?: number;
};

export type SystemStatusResponse = {
  status: string;
  timestamp: string;
  version: string;
  components: Record<string, any>;
  uptime?: number;
};

// Legacy types for backward compatibility
export type ChatReply = {
  success?: boolean;
  session_id?: string;
  reply: string;
  intent?: string;
  lead_fields?: Record<string, unknown>;
  sources?: Source[];
  metadata?: Record<string, unknown>;
};

// Enhanced API client with automatic configuration
class APIClient {
  private baseUrl: string;
  private retryCount: number = 0;
  
  constructor() {
    this.baseUrl = this.determineBaseUrl();
    this.logConfiguration();
  }
  
  private determineBaseUrl(): string {
    if (config.isProduction) {
      // Production: use the deployed backend URL
      return 'https://ai-chatbot-backend-irsvqln4dq-uc.a.run.app';
    } else {
      // Development: use proxy (no base URL needed)
      return '';
    }
  }
  
  private logConfiguration(): void {
    console.log('🚀 API Client Configuration:');
    console.log('   Mode:', config.isProduction ? 'Production' : 'Development');
    console.log('   Version:', config.appVersion);
    console.log('   Base URL:', this.baseUrl || 'Proxy (Development)');
    console.log('   Features:', Object.keys(config.features).join(', '));
  }
  
  protected async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = this.baseUrl + endpoint;
    
    // Inject persistent session header if available
    const sessionId = typeof window !== 'undefined' ? localStorage.getItem("session_id") : undefined;
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
      ...(sessionId ? { "X-Session-ID": sessionId } : {}),
    };
    
    const requestOptions: RequestInit = {
      ...options,
      headers,
      credentials: "omit",
    };
    
    try {
      console.log(`🌐 Making request to: ${url}`);
      
      const response = await fetch(url, requestOptions);
      
      if (!response.ok) {
        const errorText = await response.text().catch(() => response.statusText);
        throw new Error(`API ${response.status} ${endpoint}: ${errorText}`);
      }
      
      const data = await response.json();
      console.log(`✅ Response received from: ${endpoint}`);
      return data;
      
    } catch (error) {
      console.error(`❌ API request failed: ${endpoint}`, error);
      
      // Retry logic for non-production environments
      if (!config.isProduction && this.retryCount < config.retry.maxAttempts) {
        this.retryCount++;
        const delay = config.retry.retryDelay * Math.pow(config.retry.backoffMultiplier, this.retryCount - 1);
        
        console.log(`🔄 Retrying in ${delay}ms... (Attempt ${this.retryCount}/${config.retry.maxAttempts})`);
        
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.makeRequest<T>(endpoint, options);
      }
      
      throw error;
    }
  }
  
  // Public method for legacy functions
  async makeLegacyRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    return this.makeRequest<T>(endpoint, options);
  }
  
  // Enhanced chat endpoint with safety and risk assessment
  async sendMessage(message: string, sessionId?: string): Promise<ChatResponse> {
    console.log("💬 Sending message:", message.substring(0, 50) + "...");
    
    const payload = {
      message,
      session_id: sessionId || localStorage.getItem("session_id"),
      user_id: "anonymous"
    };
    
    const response = await this.makeRequest<ChatResponse>(config.endpoints.chat, {
      method: "POST",
      body: JSON.stringify(payload)
    });
    
    // Store session ID for future requests
    if (response.session_id) {
      localStorage.setItem("session_id", response.session_id);
    }
    
    // Log safety violations and risk levels for monitoring
    if (response.safety_violation) {
      console.warn("🚨 Safety violation detected:", response.safety_violation);
    }
    
    if (response.risk_level) {
      console.log("⚠️ Risk level:", response.risk_level);
    }
    
    return response;
  }
  
  // Enhanced lead creation with validation
  async createLead(payload: LeadPayload): Promise<LeadResponse> {
    console.log("📝 Creating lead:", payload.email);
    
    const leadData: LeadData = {
      email: payload.email,
      name: payload.name,
      phone: payload.phone,
      target_country: payload.target_country,
      intake: payload.preferred_intake,
      session_id: payload.session_id || localStorage.getItem("session_id")
    };
    
    return this.makeRequest<LeadResponse>(config.endpoints.leads, {
      method: "POST",
      body: JSON.stringify(leadData),
    });
  }
  
  // Enhanced API functions
  async getSupportedCountries(): Promise<CountriesResponse> {
    return this.makeRequest<CountriesResponse>(config.endpoints.countries);
  }
  
  async getHealthStatus(): Promise<HealthResponse> {
    return this.makeRequest<HealthResponse>(config.endpoints.health);
  }
  
  async getSystemStatus(): Promise<SystemStatusResponse> {
    return this.makeRequest<SystemStatusResponse>(config.endpoints.status);
  }
  
  // Connection test
  async testConnection(): Promise<boolean> {
    try {
      await this.getHealthStatus();
      return true;
    } catch {
      return false;
    }
  }
}

// Export types
export type LeadPayload = {
  name: string;
  email: string;
  phone: string;
  target_country: string;
  preferred_intake?: string;
  study_level?: string;
  gpa_grades?: string;
  study_field?: string;
  session_id?: string;
};

// Create and export API client instance
export const apiClient = new APIClient();

// Export convenience functions
export const sendMessage = (message: string, sessionId?: string) => 
  apiClient.sendMessage(message, sessionId);

export const createLead = (payload: LeadPayload) => 
  apiClient.createLead(payload);

export const getSupportedCountries = () => 
  apiClient.getSupportedCountries();

export const getHealthStatus = () => 
  apiClient.getHealthStatus();

export const getSystemStatus = () => 
  apiClient.getSystemStatus();

export const testConnection = () => 
  apiClient.testConnection();

// Legacy functions for backward compatibility
export async function sendMessageLegacy(message: string): Promise<ChatReply> {
  console.log("Using legacy chat endpoint:", message);
  return apiClient.makeLegacyRequest<ChatReply>("/chat/message", { 
    method: "POST",
    body: JSON.stringify({ message, platform: "website" }) 
  });
}

export async function createLeadLegacy(payload: LeadPayload): Promise<{ ok: boolean; stored?: string } | ChatReply> {
  console.log("Using legacy lead endpoint:", payload);
  return apiClient.makeLegacyRequest<{ ok: boolean; stored?: string } | ChatReply>("/chat/lead", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

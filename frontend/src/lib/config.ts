// src/lib/config.ts
// Configuration using build-time constants - no .env files needed!

export const config = {
  // API Configuration
  apiBase: (__API_BASE__ as string) || '',
  isProduction: (__IS_PRODUCTION__ as boolean) || true, // Set to true for production deployment
  appVersion: (__APP_VERSION__ as string) || '2.0.0',
  
  // Feature Flags
  features: {
    safety: true,
    leadCapture: true,
    realTimeStatus: true,
    enhancedLogging: true,
  },
  
  // Development Settings
  dev: {
    enableHotReload: true,
    enableDebugLogging: true,
    mockData: false,
  },
  
  // Production Settings
  production: {
    enableAnalytics: true,
    enableErrorReporting: true,
    enablePerformanceMonitoring: true,
  },
  
  // API Endpoints
  endpoints: {
    chat: '/api/chat',
    leads: '/api/leads',
    countries: '/api/countries',
    health: '/health',
    status: '/api/status',
  },
  
  // Timeouts and Limits
  timeouts: {
    apiRequest: 10000, // 10 seconds
    connection: 5000,  // 5 seconds
    retryDelay: 1000,  // 1 second
  },
  
  // Retry Configuration
  retry: {
    maxAttempts: 3,
    backoffMultiplier: 2,
    retryDelay: 1000, // 1 second
  },
};

// Helper function to get full API URL
export function getApiUrl(endpoint: string): string {
  if (config.isProduction) {
    // In production, use the Cloud Run backend URL
    return `https://ai-chatbot-backend-irsvqln4dq-uc.a.run.app${endpoint}`;
  } else {
    // In development, use proxy (no base URL needed)
    return endpoint;
  }
}

// Helper function to check if we're in development
export function isDevelopment(): boolean {
  return !config.isProduction;
}

// Helper function to get environment info
export function getEnvironmentInfo() {
  return {
    mode: config.isProduction ? 'production' : 'development',
    version: config.appVersion,
    apiBase: config.apiBase,
    timestamp: new Date().toISOString(),
  };
}

// Export for global use
declare global {
  const __API_BASE__: string;
  const __IS_PRODUCTION__: boolean;
  const __APP_VERSION__: string;
}

// src/lib/config.ts
// PERMANENT Configuration - URLs never change!

export const config = {
  // API Configuration
  apiBase: (__API_BASE__ as string) || '',
  isProduction: (__IS_PRODUCTION__ as boolean) || true,
  appVersion: (__APP_VERSION__ as string) || '3.0.0',
  
  // PERMANENT URLs - These never change!
  permanentUrls: {
    // Production URLs - Set once, never change
    production: {
      backend: 'https://ai-chatbot-backend-irsvqln4dq-uc.a.run.app',
      frontend: 'https://ai-chatbot-frontend-irsvqln4dq-uc.a.run.app'
    },
    // Development URLs
    development: {
      backend: 'http://127.0.0.1:8000',
      frontend: 'http://localhost:5173'
    }
  },
  
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

// PERMANENT Helper function - URL never changes!
export function getBackendUrl(): string {
  if (config.isProduction) {
    // PERMANENT Production URL - Set once, never changes
    return config.permanentUrls.production.backend;
  } else {
    // Development URL
    return config.permanentUrls.development.backend;
  }
}

// PERMANENT Helper function - URL never changes!
export function getFrontendUrl(): string {
  if (config.isProduction) {
    // PERMANENT Production URL - Set once, never changes
    return config.permanentUrls.production.frontend;
  } else {
    // Development URL
    return config.permanentUrls.development.frontend;
  }
}

// Helper function to get full API URL
export function getApiUrl(endpoint: string): string {
  const backendUrl = getBackendUrl();
  return `${backendUrl}${endpoint}`;
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
    backendUrl: getBackendUrl(),
    frontendUrl: getFrontendUrl(),
    timestamp: new Date().toISOString(),
  };
}

// Export for global use
declare global {
  const __API_BASE__: string;
  const __IS_PRODUCTION__: boolean;
  const __APP_VERSION__: string;
}

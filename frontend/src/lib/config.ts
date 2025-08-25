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

// Helper function to automatically detect backend URL
export function getBackendUrl(): string {
  if (config.isProduction) {
    // In production, try to auto-detect backend URL
    const currentHost = window.location.hostname;
    
    // If we're on Cloud Run, construct backend URL from current domain
    if (currentHost.includes('run.app')) {
      // Extract project and region from current frontend URL
      const match = currentHost.match(/([^-]+)-([^-]+)-([^-]+)-([^-]+)-([^-]+)\.a\.run\.app/);
      if (match) {
        const [, service, project, region, hash, zone] = match;
        // Construct backend URL using same project/region
        return `https://ai-chatbot-backend-${project}-${region}.a.run.app`;
      }
    }
    
    // Fallback to hardcoded URL if auto-detection fails
    return 'https://ai-chatbot-backend-irsvqln4dq-uc.a.run.app';
  } else {
    // In development, use local backend
    return 'http://127.0.0.1:8000';
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
    timestamp: new Date().toISOString(),
  };
}

// Export for global use
declare global {
  const __API_BASE__: string;
  const __IS_PRODUCTION__: boolean;
  const __APP_VERSION__: string;
}

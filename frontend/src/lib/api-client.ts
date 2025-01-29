import { env } from './env';
import axiosInstance from './axios';

// Types
export interface ApiError {
  message: string;
  status: number;
}

export interface User {
  email: string;
  name?: string;
  picture?: string;
}

export interface Stream {
  id: string;
  title: string;
  description?: string;
  status: 'scheduled' | 'live' | 'ended';
  created_at: string;
  updated_at: string;
  owner_id: string;
}

export interface WebRTCSignal {
  type: 'offer' | 'answer' | 'ice-candidate';
  payload: any;
  from?: string;
  to?: string;
}

// API Client class
class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = env.BACKEND_URL;
  }

  private async request<T>(
    endpoint: string,
    options: { method?: string; body?: any; headers?: Record<string, string> } = {}
  ): Promise<T> {
    try {
      const { data } = await axiosInstance({
        url: endpoint,
        method: options.method || 'GET',
        data: options.body,
        headers: options.headers as Record<string, string>,
      });

      return data;
    } catch (error: any) {
      throw {
        message: error.response?.data?.detail || error.message,
        status: error.response?.status || 500,
      } as ApiError;
    }
  }

  async post<T>(endpoint: string, body?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body
    });
  }

  // Auth endpoints
  async getCurrentUser(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  async loginWithGoogle(): Promise<void> {
    try {
      // Add state parameter for CSRF protection
      const state = Math.random().toString(36).substring(7);
      sessionStorage.setItem('oauth_state', state);
      
      // Redirect to the backend's OAuth endpoint with state
      const redirectUrl = `${this.baseUrl}/auth/login/google?state=${state}`;
      console.log('Redirecting to OAuth endpoint:', redirectUrl);
      window.location.href = redirectUrl;
    } catch (error) {
      console.error('Failed to initiate Google login:', error);
      throw new Error('Failed to start authentication process');
    }
  }

  async handleOAuthCallback(token: string): Promise<void> {
    try {
      // Store the token in localStorage
      localStorage.setItem('token', token);
      
      // Set secure cookie for WebSocket access
      const secure = window.location.protocol === 'https:' ? 'secure;' : '';
      const domain = window.location.hostname;
      const cookieValue = `token=${token}; path=/; ${secure} domain=${domain}; samesite=lax; max-age=3600`;
      document.cookie = cookieValue;
      
      // Refresh the current user data
      await this.getCurrentUser();
    } catch (error) {
      console.error('Error handling OAuth callback:', error);
      throw new Error('Failed to process authentication token');
    }
  }

  // Stream endpoints
  async createStream(data: {
    title: string;
    description?: string;
  }): Promise<Stream> {
    return this.request<Stream>('/streams', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async listStreams(): Promise<Stream[]> {
    return this.request<Stream[]>('/streams');
  }

  async getStream(streamId: string): Promise<Stream> {
    return this.request<Stream>(`/streams/${streamId}`);
  }

  // WebRTC signaling
  getWebSocketUrl(roomId: string): string {
    // Get token from cookie
    const cookies = document.cookie.split(';');
    const tokenCookie = cookies.find(cookie => cookie.trim().startsWith('token='));
    const token = tokenCookie ? tokenCookie.split('=')[1].trim() : null;

    if (!token) {
      console.warn('No token found in cookies');
      throw new Error('Authentication required');
    }

    // Use the configured WebSocket URL from environment with token
    if (!env.WEBSOCKET_URL) {
      console.error('WebSocket URL not configured in environment');
      throw new Error('WebSocket configuration missing');
    }
    
    const wsUrl = `${env.WEBSOCKET_URL}/${roomId}?token=${encodeURIComponent(token)}`;
    console.log('Creating WebSocket connection to:', wsUrl);
    console.log('Environment variables loaded:', {
      websocketUrl: env.WEBSOCKET_URL,
      backendUrl: env.BACKEND_URL
    });
    return wsUrl;
  }

  // Helper method to create a WebSocket connection
  createSignalingChannel(roomId: string): WebSocket {
    const wsUrl = this.getWebSocketUrl(roomId);
    console.log('Creating WebSocket connection to:', wsUrl);
    
    // Create WebSocket connection
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('WebSocket connection established');
      console.log('Connection details:', {
        url: wsUrl,
        readyState: ws.readyState,
        protocol: ws.protocol,
        extensions: ws.extensions
      });
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      console.error('Connection details:', {
        url: wsUrl,
        readyState: ws.readyState
      });
      // Attempt to reconnect on error after a delay
      setTimeout(() => {
        console.log('Attempting to reconnect...');
        this.createSignalingChannel(roomId);
      }, 3000);
    };
    
    ws.onclose = (event) => {
      console.log('WebSocket connection closed:', {
        code: event.code,
        reason: event.reason,
        wasClean: event.wasClean
      });
    };
    
    return ws;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

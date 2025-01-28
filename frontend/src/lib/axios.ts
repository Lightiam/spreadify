import axios from 'axios';
import { env } from './env';

// Create axios instance with default config
const axiosInstance = axios.create({
  baseURL: env.BACKEND_URL,
  withCredentials: true, // Important for cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for auth
axiosInstance.interceptors.request.use(
  (config) => {
    // Get token from cookie if exists
    const token = document.cookie
      .split('; ')
      .find((row) => row.startsWith('token='))
      ?.split('=')[1];

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      // Also add CORS headers
      config.withCredentials = true;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor for error handling
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error.response?.status;
    
    if (status === 401) {
      // Clear any stored tokens
      document.cookie = 'token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; secure; samesite=lax';
      // Redirect to login on auth error, but avoid redirect loops
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    
    // Enhance error message with status code
    const errorMessage = error.response?.data?.detail || error.message;
    console.error(`API Error (${status}):`, errorMessage);
    
    return Promise.reject(error);
  }
);

export default axiosInstance;

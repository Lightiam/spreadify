/// <reference types="vite/client" />

declare interface ImportMetaEnv {
  readonly VITE_APP_URL: string;
  readonly VITE_BACKEND_URL: string;
  readonly VITE_GOOGLE_CLIENT_ID: string;
  readonly VITE_WEBRTC_ICE_SERVERS: string;
  readonly VITE_WEBSOCKET_URL: string;
}

declare interface ImportMeta {
  readonly env: ImportMetaEnv;
}

export interface EnvVars {
  APP_URL: string;
  BACKEND_URL: string;
  GOOGLE_CLIENT_ID: string;
  WEBRTC_ICE_SERVERS: any;
  WEBSOCKET_URL: string;
  STRIPE_PUBLIC_KEY: string;
}

function validateEnv(): EnvVars {
  const env = import.meta.env;
  
  // Log environment variables for debugging
  console.log('Environment variables:', {
    APP_URL: env.VITE_APP_URL,
    BACKEND_URL: env.VITE_BACKEND_URL,
    GOOGLE_CLIENT_ID: env.VITE_GOOGLE_CLIENT_ID,
    WEBRTC_ICE_SERVERS: env.VITE_WEBRTC_ICE_SERVERS,
    WEBSOCKET_URL: env.VITE_WEBSOCKET_URL
  });
  
  if (!env.VITE_APP_URL) throw new Error('VITE_APP_URL is required');
  if (!env.VITE_BACKEND_URL) throw new Error('VITE_BACKEND_URL is required');
  if (!env.VITE_GOOGLE_CLIENT_ID) throw new Error('VITE_GOOGLE_CLIENT_ID is required');
  if (!env.VITE_WEBRTC_ICE_SERVERS) throw new Error('VITE_WEBRTC_ICE_SERVERS is required');
  if (!env.VITE_WEBSOCKET_URL) throw new Error('VITE_WEBSOCKET_URL is required');
  if (!env.VITE_STRIPE_PUBLIC_KEY) throw new Error('VITE_STRIPE_PUBLIC_KEY is required');

  return {
    APP_URL: env.VITE_APP_URL,
    BACKEND_URL: env.VITE_BACKEND_URL,
    GOOGLE_CLIENT_ID: env.VITE_GOOGLE_CLIENT_ID,
    WEBRTC_ICE_SERVERS: JSON.parse(env.VITE_WEBRTC_ICE_SERVERS),
    WEBSOCKET_URL: env.VITE_WEBSOCKET_URL,
    STRIPE_PUBLIC_KEY: env.VITE_STRIPE_PUBLIC_KEY
  };
}

export const env = validateEnv();

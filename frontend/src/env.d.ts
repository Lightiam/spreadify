/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_FRONTEND_URL: string
  readonly VITE_RTMP_SERVER_URL: string
  readonly VITE_STRIPE_PUBLISHABLE_KEY: string
  readonly VITE_WEBSOCKET_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module 'sonner' {
  export function toast(options: { title?: string; description?: string; variant?: 'default' | 'destructive' }): void;
  export function toast(message: string): void;
}

import axios from 'axios';
import { useAuth } from './auth';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = useAuth.getState().token;
  if (token) {
    config.headers = {
      ...config.headers,
      'Authorization': token
    };
  }
  return config;
});

export const auth = {
  login: async (email: string, password: string) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    const response = await axios.post(
      `${import.meta.env.VITE_API_URL}/auth/token`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response;
  },
  register: (email: string, password: string, username: string) =>
    api.post('/auth/register', { email, password, username }),
  me: () => api.get('/auth/me'),
  getFacebookCallback: (code: string) => api.post('/auth/facebook', { code }),
  getTwitterCallback: (code: string) => api.post('/auth/twitter', { code }),
};

export const channels = {
  create: (data: { name: string; description?: string }) =>
    api.post('/channels', data),
  list: () => api.get('/channels'),
  get: (id: string) => api.get(`/channels/${id}`),
  update: (id: string, data: { name?: string; description?: string }) =>
    api.patch(`/channels/${id}`, data),
  delete: (id: string) => api.delete(`/channels/${id}`),
};

export const streams = {
  create: (channelId: string, data: { title: string; description?: string }) =>
    api.post(`/channels/${channelId}/streams`, data),
  list: (channelId: string) => api.get(`/channels/${channelId}/streams`),
  get: (id: string) => api.get(`/streams/${id}`),
  update: (id: string, data: { title?: string; description?: string }) =>
    api.patch(`/streams/${id}`, data),
  delete: (id: string) => api.delete(`/streams/${id}`),
  getStreamKey: (id: string) => api.get(`/streams/${id}/key`),
  schedule: (channelId: string, data: { title: string; description?: string; scheduledFor: string }) =>
    api.post(`/channels/${channelId}/streams/schedule`, data),
};

export const chat = {
  send: (streamId: string, content: string) =>
    api.post(`/streams/${streamId}/chat`, { content }),
  list: (streamId: string) => api.get(`/streams/${streamId}/chat`),
  moderate: (streamId: string, messageId: string, action: 'delete' | 'block') =>
    api.post(`/streams/${streamId}/chat/${messageId}/moderate`, { action }),
};

export const analytics = {
  getStreamStats: (streamId: string) =>
    api.get(`/analytics/streams/${streamId}`),
  getChannelStats: (channelId: string) =>
    api.get(`/analytics/channels/${channelId}`),
};

export const subscriptions = {
  subscribe: (channelId: string) =>
    api.post(`/channels/${channelId}/subscribe`),
  unsubscribe: (channelId: string) =>
    api.post(`/channels/${channelId}/unsubscribe`),
  getStatus: (channelId: string) =>
    api.get(`/channels/${channelId}/subscription`),
};

export const streaming = {
  youtube: {
    start: (streamId: string) => api.post('/streaming/youtube/start', { stream_id: streamId }),
    stop: (broadcastId: string) => api.post(`/streaming/youtube/stop/${broadcastId}`),
  },
  facebook: {
    start: (streamId: string) => api.post('/streaming/facebook/start', { stream_id: streamId }),
    stop: (liveVideoId: string) => api.post(`/streaming/facebook/stop/${liveVideoId}`),
  },
  twitch: {
    start: (streamId: string) => api.post('/streaming/twitch/start', { stream_id: streamId }),
    stop: () => api.post('/streaming/twitch/stop'),
  },
  linkedin: {
    start: (streamId: string) => api.post('/streaming/linkedin/start', { stream_id: streamId }),
    stop: (streamId: string) => api.post(`/streaming/linkedin/stop/${streamId}`),
  },
};

export const music = {
  spotify: {
    getAuthUrl: () => api.get('/music/spotify/auth-url'),
    getNowPlaying: () => api.get('/music/spotify/now-playing'),
    playTrack: (trackUri: string) => api.post('/music/spotify/play', { track_uri: trackUri }),
  },
  apple: {
    getNowPlaying: () => api.get('/music/apple/now-playing'),
    playTrack: (trackId: string) => api.post('/music/apple/play', { track_id: trackId }),
  },
};

export const payments = {
  createPaymentIntent: (amount: number) =>
    api.post('/payments/create-intent', { amount }),
  createPayPalOrder: (amount: number) =>
    api.post('/payments/paypal/create-order', { amount }),
  capturePayPalOrder: (orderId: string) =>
    api.post(`/payments/paypal/capture-order/${orderId}`),
  processSuperChat: (streamId: string, amount: number, message: string) =>
    api.post(`/streams/${streamId}/super-chat`, { amount, message }),
};

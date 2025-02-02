export interface User {
  id: string;
  email: string;
  username: string;
  createdAt: string;
  avatarUrl?: string;
  channels?: {
    id: string;
    role: 'owner' | 'admin' | 'moderator' | 'subscriber' | 'banned';
  }[];
  streams?: {
    id: string;
    role: 'owner' | 'admin' | 'moderator' | 'subscriber' | 'banned';
  }[];
}

export interface Channel {
  id: string;
  name: string;
  description?: string;
  ownerId: string;
  createdAt: string;
  profilePictureUrl?: string;
  subscriberCount: number;
}

export interface Stream {
  id: string;
  channelId: string;
  title: string;
  description?: string;
  status: 'scheduled' | 'live' | 'ended';
  streamKey?: string;
  startTime?: string;
  endTime?: string;
  viewerCount: number;
  createdAt: string;
}

export interface ChatMessage {
  id: string;
  streamId: string;
  userId: string;
  username: string;
  content: string;
  type: 'normal' | 'super_chat';
  amount?: number;
  createdAt: string;
}

export interface StreamAnalytics {
  streamId: string;
  viewerCount: number;
  peakViewers: number;
  chatMessages: number;
  donations: number;
  subscriptions: number;
  platforms: {
    [platform: string]: {
      viewers: number;
      likes: number;
      shares: number;
    };
  };
}

export interface Subscription {
  id: string;
  userId: string;
  channelId: string;
  status: 'active' | 'cancelled';
  createdAt: string;
  cancelledAt?: string;
}

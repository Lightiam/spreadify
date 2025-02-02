import { useAuth } from "./auth";
// import type { User } from "../types";

export function isAuthenticated(): boolean {
  const { token } = useAuth.getState();
  return !!token;
}

export function hasChannelPermission(channelId: string, permission: 'view' | 'edit' | 'manage'): boolean {
  const { user } = useAuth.getState();
  if (!user) return false;

  const channel = user.channels?.find(c => c.id === channelId);
  if (!channel) return permission === 'view';

  if (channel.role === 'owner') return true;
  if (channel.role === 'banned') return false;
  if (['admin', 'moderator'].includes(channel.role)) return permission !== 'manage';
  return permission === 'view';
}

export function hasStreamPermission(streamId: string, permission: 'view' | 'edit' | 'manage'): boolean {
  const { user } = useAuth.getState();
  if (!user) return false;

  const stream = user.streams?.find(s => s.id === streamId);
  if (!stream) return permission === 'view';

  if (stream.role === 'owner') return true;
  if (stream.role === 'banned') return false;
  if (['admin', 'moderator'].includes(stream.role)) return permission !== 'manage';
  return permission === 'view';
}

export function canModerateChat(streamId: string): boolean {
  const { user } = useAuth.getState();
  if (!user) return false;

  const stream = user.streams?.find(s => s.id === streamId);
  return !!stream && ['owner', 'moderator', 'admin'].includes(stream.role);
}

export function canSendSuperChat(streamId: string): boolean {
  const { user } = useAuth.getState();
  if (!user) return false;

  const stream = user.streams?.find(s => s.id === streamId);
  return !stream || stream.role !== 'banned';
}

export function canSubscribe(channelId: string): boolean {
  const { user } = useAuth.getState();
  if (!user) return false;

  const channel = user.channels?.find(c => c.id === channelId);
  return !channel || !['owner', 'banned'].includes(channel.role);
}

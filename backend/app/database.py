from datetime import datetime
from typing import Dict, List, Optional, Any
from .models import User, Channel, Stream, StreamSchedule

class InMemoryDB:
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.channels: Dict[str, Channel] = {}
        self.streams: Dict[str, Stream] = {}
        self.tokens: Dict[str, str] = {}  # user_id -> refresh_token
        self.chat_messages: Dict[str, List[dict]] = {}  # stream_id -> messages
        self.subscriptions: Dict[str, dict] = {}

    async def get_user(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)
        
    async def get_user_by_email(self, email: str) -> Optional[User]:
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    async def create_user(self, user: User) -> User:
        self.users[user.id] = user
        return user

    async def get_channel(self, channel_id: str) -> Optional[Channel]:
        return self.channels.get(channel_id)

    async def create_channel(self, channel: Channel) -> Channel:
        self.channels[channel.id] = channel
        return channel

    async def get_stream(self, stream_id: str) -> Optional[Stream]:
        return self.streams.get(stream_id)
        
    async def get_stream_by_key(self, stream_key: str) -> Optional[Stream]:
        for stream in self.streams.values():
            if stream.stream_key == stream_key:
                return stream
        return None

    async def create_stream(self, stream: Stream) -> Stream:
        self.streams[stream.id] = stream
        return stream

    async def update_stream(self, stream_id: str, data: Dict[str, Any]) -> Optional[Stream]:
        if stream_id in self.streams:
            stream = self.streams[stream_id]
            for key, value in data.items():
                setattr(stream, key, value)
            return stream
        return None
        
    async def get_chat_messages(self, stream_id: str) -> List[Dict[str, Any]]:
        return self.chat_messages.get(stream_id, [])
        
    async def store_chat_message(self, stream_id: str, message: Dict[str, Any]) -> None:
        if stream_id not in self.chat_messages:
            self.chat_messages[stream_id] = []
        self.chat_messages[stream_id].append(message)
        
    async def block_user(self, user_id: str, blocked_user_id: str) -> None:
        if user_id in self.users:
            user = self.users[user_id]
            if not hasattr(user, "blocked_users"):
                user.blocked_users = []
            if blocked_user_id not in user.blocked_users:
                user.blocked_users.append(blocked_user_id)
                
    async def unblock_user(self, user_id: str, blocked_user_id: str) -> None:
        if user_id in self.users:
            user = self.users[user_id]
            if hasattr(user, "blocked_users") and blocked_user_id in user.blocked_users:
                user.blocked_users.remove(blocked_user_id)
                
    async def is_user_blocked(self, user_id: str, blocked_user_id: str) -> bool:
        if user_id in self.users:
            user = self.users[user_id]
            return hasattr(user, "blocked_users") and blocked_user_id in user.blocked_users
        return False
        
    async def get_platform_stats(self, stream_id: str) -> Dict[str, Dict[str, Any]]:
        stream = self.streams.get(stream_id)
        if not stream:
            return {}
        return getattr(stream, "platform_stats", {})
        
    async def store_payment(self, payment_data: Dict[str, Any]) -> None:
        stream_id = payment_data["stream_id"]
        if stream_id in self.streams:
            stream = self.streams[stream_id]
            if not hasattr(stream, "payments"):
                stream.payments = []
            stream.payments.append(payment_data)
            
    async def create_subscription(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        self.subscriptions[subscription_data["id"]] = subscription_data
        return subscription_data
        
    async def update_subscription(self, subscription_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if subscription_id in self.subscriptions:
            subscription = self.subscriptions[subscription_id]
            for key, value in data.items():
                subscription[key] = value
            return subscription
        return None
        
    async def get_channel_subscribers(self, channel_id: str) -> List[Dict[str, Any]]:
        return [
            sub for sub in self.subscriptions.values()
            if sub["channel_id"] == channel_id and sub["status"] == "active"
        ]
        
    async def get_user_channels(self, user_id: str) -> List[Channel]:
        return [
            channel for channel in self.channels.values()
            if channel.owner_id == user_id
        ]
        
    async def update_channel(self, channel_id: str, data: Dict[str, Any]) -> Optional[Channel]:
        if channel_id in self.channels:
            channel = self.channels[channel_id]
            for key, value in data.items():
                setattr(channel, key, value)
            return channel
        return None
        
    async def delete_channel(self, channel_id: str) -> None:
        if channel_id in self.channels:
            del self.channels[channel_id]
            
    async def get_channel_streams(self, channel_id: str) -> List[Stream]:
        return [
            stream for stream in self.streams.values()
            if stream.channel_id == channel_id
        ]

db = InMemoryDB()

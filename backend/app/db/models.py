from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint, UUID, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    password_hash = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    channels = relationship("Channel", back_populates="owner")
    streams = relationship("Stream", back_populates="owner")
    chat_messages = relationship("ChatMessage", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    social_accounts = relationship("SocialAccount", back_populates="user")

class SocialAccount(Base):
    __tablename__ = "social_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    provider = Column(String)  # google, facebook, twitter
    provider_user_id = Column(String)
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="social_accounts")
    
    __table_args__ = (
        UniqueConstraint('provider', 'provider_user_id', name='unique_social_account'),
    )

class Channel(Base):
    __tablename__ = "channels"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    description = Column(String, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    profile_picture_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="channels")
    streams = relationship("Stream", back_populates="channel")
    subscriptions = relationship("Subscription", back_populates="channel")

class Stream(Base):
    __tablename__ = "streams"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String)
    description = Column(String, nullable=True)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id"))
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(String, default="scheduled")  # scheduled, live, ended
    stream_key = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    viewer_count = Column(Integer, default=0)
    scheduled_for = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in minutes
    reminder_sent = Column(Boolean, default=False)
    
    channel = relationship("Channel", back_populates="streams")
    owner = relationship("User", back_populates="streams")
    chat_messages = relationship("ChatMessage", back_populates="stream")
    overlays = relationship("Overlay", back_populates="stream")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stream_id = Column(UUID(as_uuid=True), ForeignKey("streams.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    content = Column(String)
    type = Column(String, default="normal")  # normal, super_chat
    amount = Column(Integer, nullable=True)  # For super chats, in cents
    created_at = Column(DateTime, default=datetime.utcnow)
    
    stream = relationship("Stream", back_populates="chat_messages")
    user = relationship("User", back_populates="chat_messages")

class Overlay(Base):
    __tablename__ = "overlays"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stream_id = Column(UUID(as_uuid=True), ForeignKey("streams.id"))
    path = Column(String)
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    scale = Column(Integer, default=100)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    stream = relationship("Stream", back_populates="overlays")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id"))
    status = Column(String, default="active")  # active, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="subscriptions")
    channel = relationship("Channel", back_populates="subscriptions")

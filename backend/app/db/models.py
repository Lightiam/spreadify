from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class ChannelSettings(Base):
    __tablename__ = "channel_settings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    monetization_enabled = Column(Boolean, default=False)
    subscription_price = Column(Integer)  # In cents
    minimum_donation = Column(Integer)  # In cents
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    channel_id = Column(String, ForeignKey("channels.id"))
    channel = relationship("Channel", back_populates="settings")

class Channel(Base):
    __tablename__ = "channels"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    description = Column(String, nullable=True)
    owner_id = Column(String, default="anonymous")
    profile_picture_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    streams = relationship("Stream", back_populates="channel")
    settings = relationship("ChannelSettings", back_populates="channel", uselist=False)
    social_channels = relationship("SocialChannel", back_populates="channel")

class Stream(Base):
    __tablename__ = "streams"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String)
    description = Column(String, nullable=True)
    channel_id = Column(String, ForeignKey("channels.id"))
    owner_id = Column(String, default="anonymous")
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
    overlays = relationship("Overlay", back_populates="stream")
    chat_messages = relationship("ChatMessage", back_populates="stream")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    stream_id = Column(String, ForeignKey("streams.id"))
    user_id = Column(String, default="anonymous")
    content = Column(String)
    type = Column(String, default="normal")  # normal, super_chat
    amount = Column(Integer, nullable=True)  # For super chats, in cents
    created_at = Column(DateTime, default=datetime.utcnow)
    
    stream = relationship("Stream", back_populates="chat_messages")

class Overlay(Base):
    __tablename__ = "overlays"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    stream_id = Column(String, ForeignKey("streams.id"))
    path = Column(String)
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    scale = Column(Integer, default=100)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    stream = relationship("Stream", back_populates="overlays")

class SocialChannel(Base):
    __tablename__ = "social_channels"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    channel_id = Column(String, ForeignKey("channels.id"))
    platform = Column(String)
    link = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    channel = relationship("Channel", back_populates="social_channels")

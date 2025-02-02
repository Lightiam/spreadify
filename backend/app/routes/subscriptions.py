from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
from sqlalchemy.orm import Session
from ..db.models import Channel
from ..db.database import get_db
import stripe
import os
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class SubscriptionCreate(BaseModel):
    channel_id: str

@router.post("")
async def create_subscription(
    subscription: SubscriptionCreate,
    db: Session = Depends(get_db)
):
    # Get channel
    channel = db.query(Channel).filter(Channel.id == subscription.channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    if not getattr(channel.settings, 'monetization_enabled', False):
        raise HTTPException(
            status_code=400,
            detail="Channel monetization is not enabled"
        )
        
    if not getattr(channel.settings, 'subscription_price', None):
        raise HTTPException(
            status_code=400,
            detail="Channel subscription price is not set"
        )
    
    try:
        # Create Stripe customer if not exists
        customer = stripe.Customer.create(
            email="anonymous@example.com",
            metadata={"user_id": "anonymous"}
        )
        
        # Create subscription
        stripe_subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": channel.settings.subscription_price}],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"],
            metadata={
                "channel_id": channel.id,
                "subscriber_id": "anonymous"
            }
        )
        
        # Store subscription in database
        subscription_data = {
            "id": stripe_subscription.id,
            "channel_id": channel.id,
            "user_id": "anonymous",
            "status": stripe_subscription.status,
            "created_at": datetime.utcnow()
        }
        db.add(subscription_data)
        db.commit()
        
        return {
            "subscription_id": stripe_subscription.id,
            "client_secret": stripe_subscription.latest_invoice.payment_intent.client_secret
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/channel/{channel_id}")
async def get_channel_subscribers(
    channel_id: str,
    db: Session = Depends(get_db)
):
    # Get channel
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    # Anyone can view subscribers in simplified version
    
    return db.query(Channel).filter(Channel.id == channel_id).all()

@router.post("/webhook")
async def subscription_webhook(payload: dict, db: Session = Depends(get_db)):
    try:
        event = stripe.Event.construct_from(payload, stripe.api_key)
        
        if event.type == "customer.subscription.updated":
            subscription = event.data.object
            db.query(Channel).filter(Channel.id == subscription["id"]).update({
                "status": subscription["status"]
            })
            db.commit()
            
        elif event.type == "customer.subscription.deleted":
            subscription = event.data.object
            db.query(Channel).filter(Channel.id == subscription["id"]).update({
                "status": "canceled"
            })
            db.commit()
            
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
